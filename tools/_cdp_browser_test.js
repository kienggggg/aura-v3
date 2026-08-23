/**
 * tools/_cdp_browser_test.js — Chạy Chrome Headless qua giao thức Chrome DevTools Protocol (CDP).
 *
 * Yêu cầu:
 * 1. Không dùng thư viện ngoài (chỉ dùng Node.js built-in fetch và WebSocket).
 * 2. Mở tệp qua UI, kiểm tra dirty state (sửa thật -> nút disabled -> 0 request).
 * 3. Bấm #btnRunE1 thật, phát đúng 1 request POST /api/dinh_vi_loi và render response thật.
 * 4. Kiểm tra XSS Canary, chụp ảnh màn hình và lưu DOM receipt.
 * 5. Verdict là AND của mọi subgate; thất bại là exit 1 ngay.
 */
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function findChrome() {
  const possiblePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    process.env.CHROME_PATH,
  ].filter(Boolean);

  for (const p of possiblePaths) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

async function main() {
  const args = process.argv.slice(2);
  const appPort = parseInt(args[0] || '8088', 10);
  const token = args[1] || '';
  const outDir = path.resolve(args[2] || '.');
  const allowCodeExecution = args[3] === 'true';

  fs.mkdirSync(outDir, { recursive: true });

  const chromePath = findChrome();
  if (!chromePath) {
    console.error('Không tìm thấy Chrome tại các đường dẫn mặc định.');
    process.exit(1);
  }

  const tempProfile = fs.mkdtempSync(path.join(os.tmpdir(), 'aura_cdp_profile_'));
  let chromeProc = null;
  let ws = null;

  try {
    // 1. Khởi chạy Chrome headless
    chromeProc = spawn(chromePath, [
      '--headless=new',
      '--remote-debugging-port=0',
      `--user-data-dir=${tempProfile}`,
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
      'about:blank',
    ], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    // 2. Đọc port từ DevToolsActivePort
    const portFilePath = path.join(tempProfile, 'DevToolsActivePort');
    let devToolsPort = null;
    for (let i = 0; i < 50; i++) {
      if (fs.existsSync(portFilePath)) {
        try {
          const content = fs.readFileSync(portFilePath, 'utf-8').trim().split('\n');
          if (content.length >= 1 && parseInt(content[0], 10) > 0) {
            devToolsPort = parseInt(content[0], 10);
            break;
          }
        } catch (_) {}
      }
      await sleep(100);
    }

    if (!devToolsPort) {
      throw new Error('Không đọc được DevToolsActivePort sau 5 giây');
    }

    // 3. Lấy WebSocket debugger URL của Page target
    const listRes = await fetch(`http://127.0.0.1:${devToolsPort}/json/list`);
    const targets = await listRes.json();
    const pageTarget = targets.find((t) => t.type === 'page') || targets[0];

    if (!pageTarget || !pageTarget.webSocketDebuggerUrl) {
      throw new Error('Không tìm thấy Page target có WebSocketDebuggerUrl');
    }

    const wsUrl = pageTarget.webSocketDebuggerUrl;

    // 4. Kết nối WebSocket CDP
    ws = new WebSocket(wsUrl);
    let msgId = 1;
    const callbacks = new Map();
    const networkRequests = [];

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.id && callbacks.has(msg.id)) {
          const cb = callbacks.get(msg.id);
          callbacks.delete(msg.id);
          cb(msg);
        } else if (msg.method === 'Network.requestWillBeSent') {
          networkRequests.push(msg.params.request);
        }
      } catch (err) {
        console.error('Lỗi phân tích tin nhắn CDP:', err);
      }
    };

    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    function sendCDP(method, params = {}) {
      return new Promise((resolve, reject) => {
        const id = msgId++;
        callbacks.set(id, (resp) => {
          if (resp.error) reject(new Error(`CDP Error (${method}): ${JSON.stringify(resp.error)}`));
          else resolve(resp.result);
        });
        ws.send(JSON.stringify({ id, method, params }));
      });
    }

    // Bật các domain CDP
    await sendCDP('Page.enable');
    await sendCDP('Runtime.enable');
    await sendCDP('Network.enable');

    // 5. Điều hướng tới App Thẻ
    const appUrl = `http://127.0.0.1:${appPort}/?token=${encodeURIComponent(token)}`;
    await sendCDP('Page.navigate', { url: appUrl });
    await sleep(1500);

    // Helper evaluate
    async function evaluate(expression) {
      const res = await sendCDP('Runtime.evaluate', {
        expression,
        returnByValue: true,
      });
      return res.result ? res.result.value : undefined;
    }

    const testResults = {
      allowCodeExecution,
      subgates: {},
    };

    if (!allowCodeExecution) {
      // KIỂM THỬ KHI CỜ TẮT
      const buttonsDisabled = await evaluate(`
        ({
          btnRun: document.getElementById('btnRun')?.disabled,
          btnRunTrace: document.getElementById('btnRunTrace')?.disabled,
          btnRunE1: document.getElementById('btnRunE1')?.disabled,
        })
      `);

      const passDisabled =
        buttonsDisabled.btnRun === true &&
        buttonsDisabled.btnRunTrace === true &&
        buttonsDisabled.btnRunE1 === true;

      // Thử click nút E1 khi disabled
      const reqCountBefore = networkRequests.length;
      await evaluate(`document.getElementById('btnRunE1')?.click()`);
      await sleep(300);
      const reqCountAfter = networkRequests.length;
      const noRequestSent = reqCountBefore === reqCountAfter;

      testResults.subgates.flag_disabled = {
        pass: passDisabled && noRequestSent,
        buttonsDisabled,
        noRequestSent,
      };
    } else {
      // KIỂM THỬ KHI CỜ BẬT (LUỒNG THẬT UI -> API -> DOM)
      
      // 1. Mở tệp qua UI (chọn tệp core/dong_ho.py)
      await evaluate(`
        if (window.openPyFile) {
          window.openPyFile('core/dong_ho.py');
        }
      `);
      
      // Chờ tệp được mở và activeFilePath được gán
      for (let i = 0; i < 30; i++) {
        await sleep(200);
        const active = await evaluate(`window.state?.activeFilePath`);
        if (active === 'core/dong_ho.py') break;
      }

      // 2. Kiểm tra Dirty State: sửa nội dung editor -> nút E1 bị disabled -> click không gửi request
      await evaluate(`
        window.state.hasModifications = true;
        if (window.updateButtonsState) window.updateButtonsState();
      `);
      await sleep(200);

      const dirtyStateDisabled = await evaluate(`document.getElementById('btnRunE1')?.disabled === true`);
      const reqCountDirty1 = networkRequests.length;
      await evaluate(`document.getElementById('btnRunE1')?.click()`);
      await sleep(300);
      const reqCountDirty2 = networkRequests.length;
      const dirtyNoRequest = reqCountDirty1 === reqCountDirty2;

      // 3. Khôi phục dirty state
      await evaluate(`
        window.state.hasModifications = false;
        if (window.updateButtonsState) window.updateButtonsState();
      `);
      await sleep(200);

      const cleanStateEnabled = await evaluate(`document.getElementById('btnRunE1')?.disabled === false`);

      // 4. Click nút #btnRunE1 thật để gọi API /api/dinh_vi_loi thật
      const e1ReqCountBefore = networkRequests.filter((r) => r.url && r.url.includes('/api/dinh_vi_loi')).length;
      await evaluate(`document.getElementById('btnRunE1')?.click()`);
      
      // Chờ API chạy xong và render DOM (chờ tối đa 60s)
      let apiDone = false;
      for (let i = 0; i < 120; i++) {
        await sleep(500);
        const statusText = await evaluate(`document.getElementById('e1StatusPill')?.textContent`);
        const resultsHtml = await evaluate(`document.getElementById('e1ResultsBody')?.innerHTML || ''`);
        if (statusText && (statusText.includes('TÌM THẤY') || statusText.includes('ĐÃ HOÀN TẤT') || resultsHtml.includes('e1-summary-card'))) {
          apiDone = true;
          break;
        }
      }

      const e1ReqCountAfter = networkRequests.filter((r) => r.url && r.url.includes('/api/dinh_vi_loi')).length;
      const exactlyOneE1Request = (e1ReqCountAfter - e1ReqCountBefore) === 1;

      // 5. Kiểm tra XSS Safety & DOM Rendered thật
      const xssCanaryValue = await evaluate(`window.__xss_canary`);
      const xssSafe = xssCanaryValue === undefined || xssCanaryValue === null;

      const domDetails = await evaluate(`
        ({
          bodyHasNotice: !!document.querySelector('.e1-notice-box') || !!document.querySelector('.e1-summary-card') || (document.getElementById('e1ResultsBody')?.innerHTML || '').length > 0,
          bodyHasDiff: !!document.querySelector('.e1-diff-container') || !!document.querySelector('.e1-candidate-card'),
          hasApplyButton: !!document.querySelector('.btn-apply-e1') || !!document.querySelector('[data-action="apply"]'),
          statusPillText: document.getElementById('e1StatusPill')?.textContent,
          cardsCount: document.querySelectorAll('.e1-candidate-card').length,
        })
      `);

      // 6. Kiểm tra Network: tuyệt đối không có request lưu tệp /api/luu_tep
      const saveRequests = networkRequests.filter((r) => r.url && r.url.includes('/api/luu_tep'));

      const allSubgatesPass =
        dirtyStateDisabled &&
        dirtyNoRequest &&
        cleanStateEnabled &&
        exactlyOneE1Request &&
        apiDone &&
        xssSafe &&
        domDetails.bodyHasNotice &&
        !domDetails.hasApplyButton &&
        saveRequests.length === 0;

      testResults.subgates.e1_real_flow = {
        pass: allSubgatesPass,
        dirtyStateDisabled,
        dirtyNoRequest,
        cleanStateEnabled,
        exactlyOneE1Request,
        apiDone,
        xssSafe,
        domDetails,
        saveRequestsCount: saveRequests.length,
      };
    }

    // 6. Chụp Screenshot
    const screenshotRes = await sendCDP('Page.captureScreenshot', { format: 'png' });
    const screenshotPath = path.join(outDir, 'e1_ui_screenshot.png');
    fs.writeFileSync(screenshotPath, Buffer.from(screenshotRes.data, 'base64'));

    // 7. Lưu DOM Receipt
    const fullDomHtml = await evaluate(`document.documentElement.outerHTML`);
    const domReceiptPath = path.join(outDir, 'ui_dom_receipt.json');
    fs.writeFileSync(domReceiptPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      appUrl,
      testResults,
      networkRequestsCount: networkRequests.length,
      domHtmlLength: (fullDomHtml || '').length,
      screenshotPath,
    }, null, 2));

    const overallPass = Object.values(testResults.subgates).every((sg) => sg.pass === true);

    console.log(JSON.stringify({
      trang_thai: overallPass ? 'PASS' : 'FAIL',
      testResults,
      screenshotPath,
      domReceiptPath,
    }, null, 2));

    if (!overallPass) {
      process.exit(1);
    }

  } finally {
    if (ws) {
      try { ws.close(); } catch (_) {}
    }
    if (chromeProc && chromeProc.pid) {
      try {
        if (process.platform === 'win32') {
          execSync(`taskkill /F /T /PID ${chromeProc.pid}`, { stdio: 'ignore' });
        } else {
          chromeProc.kill('SIGKILL');
        }
      } catch (_) {}
    }
    try {
      fs.rmSync(tempProfile, { recursive: true, force: true });
    } catch (_) {}
  }
}

main().catch((err) => {
  console.error('Lỗi thực thi CDP script:', err);
  process.exit(1);
});
