// app.js — Controller tương tác toàn diện cho App Lập trình bằng THẺ v1

(function () {
  'use strict';

  // State chính của ứng dụng
  const state = {
    tree: [],
    history: [],
    historyIndex: -1,
    authToken: '',
    activeFilePath: '',
    activeFileSha256: null,
    hasModifications: false,
    codeExecutionEnabled: false,
    diagnostics: { hop_le: true, so_loi_do: 0, so_canh_bao_vang: 0, danh_sach: [], so_lan_dung_the: {} },
    nodeIdCounter: 100,
    sidebarLeftCollapsed: false,
    sidebarRightCollapsed: false,
    codeFontSize: 14,
    draggingCardId: null,
    selectedNodeId: null,
    activeFileName: 'Chưa đặt tên',
    editorMode: 'split',
    tabs: [],
    tabActive: -1
  };

  // ==========================================================================
  // 1. KHỞI TẠO & LẤY MÃ THÔNG HÀNH AUTH TOKEN (MỤC 14.2)
  // ==========================================================================
  function initAuthToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    if (tokenFromUrl) {
      state.authToken = tokenFromUrl;
      sessionStorage.setItem('aura_the_auth_token', tokenFromUrl);
      // Dọn sạch token khỏi thanh địa chỉ để tránh lưu lịch sử duyệt web
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    } else {
      state.authToken = sessionStorage.getItem('aura_the_auth_token') || '';
    }
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Gọi fetch kèm header bảo mật X-Auth-Token
  async function authFetch(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'X-Auth-Token': state.authToken,
      ...(options.headers || {})
    };
    return fetch(url, { ...options, headers });
  }

  async function configureRuntimeCapabilities() {
    const btnRun = document.getElementById('btnRun');
    const runText = document.getElementById('runBtnText');
    const btnTrace = document.getElementById('btnRunTrace');
    const btnE1 = document.getElementById('btnRunE1');
    const termBody = document.getElementById('terminalBody');
    const traceStatusPill = document.getElementById('traceStatusPill');
    const e1StatusPill = document.getElementById('e1StatusPill');

    try {
      const resp = await authFetch('/api/status');
      const data = await resp.json();
      state.codeExecutionEnabled = Boolean(data.code_execution_enabled);
      state.e1Limitation = data.e1_limitation || '';
      // 26/08: giữ tên thư mục dự án để cây tệp và thanh trạng thái nói
      // được "đang mở dự án nào". Thiếu nó thì cây tệp ghi `root/`, và
      // đo trên app đang chạy thì tên dự án KHÔNG xuất hiện ở bất kỳ đâu
      // trên màn hình.
      state.tenDuAn = data.ten_du_an || '';
      // Vẽ ngay: `onTreeChanged` chỉ chạy khi cây thẻ đổi, mà lúc mới mở app
      // thì chưa có thay đổi nào — thiếu dòng này thanh trạng thái đứng im
      // ở dấu gạch cho tới khi người dùng đụng vào thẻ đầu tiên.
      veThanhTrangThai();
      // ĐUA THỨ TỰ, bắt được 26/08 bằng cách tự bấm thử chứ không đọc mã:
      // `btnModeFiles.click()` lúc khởi động gọi `loadFileTree()` NGAY, còn
      // `/api/status` là lượt gọi mạng riêng và về sau. Nên cây vẽ xong khi
      // `state.tenDuAn` còn rỗng, và nhãn gốc rơi về `root/` — đúng cái vừa
      // sửa, vẫn hiện y như cũ.
      //
      // Không sắp lại thứ tự hai lượt gọi (làm thế thì cây phải CHỜ mạng mới
      // hiện được). Thay vào đó: vẽ lại đúng MỘT lần, và chỉ khi cây thật sự
      // đang mang tên khác. So bằng biến `tenDuAnDaVeCay` chứ không dò chữ
      // `root/` trong HTML — dò chuỗi là đúng bệnh CLAUDE.md §4.
      if (state.tenDuAn && state.tenDuAnDaVeCay !== undefined
          && state.tenDuAnDaVeCay !== state.tenDuAn) {
        const oCay = document.getElementById('fileTreeContainer');
        if (oCay && oCay.style.display !== 'none') loadFileTree();
      }
      if (btnRun) btnRun.disabled = !state.codeExecutionEnabled;
      if (btnTrace) btnTrace.disabled = !state.codeExecutionEnabled;
      if (btnE1) btnE1.disabled = !state.codeExecutionEnabled;

      if (!state.codeExecutionEnabled) {
        if (runText) runText.textContent = 'CHẠY ĐANG TẮT';
        if (btnRun) btnRun.title = 'Tắt mặc định vì tiến trình Python chưa được cách ly khỏi tệp và mạng';
        if (btnTrace) btnTrace.title = 'Chạy mã/test đang tắt mặc định';
        if (btnE1) btnE1.title = 'Chạy mã/test đang tắt mặc định';
        if (traceStatusPill) {
          traceStatusPill.className = 'trace-status-pill cut';
          traceStatusPill.textContent = 'TẮT';
        }
        if (e1StatusPill) {
          e1StatusPill.className = 'trace-status-pill cut';
          e1StatusPill.textContent = 'TẮT';
        }
        if (termBody) {
          termBody.innerHTML = '<div class="term-line term-dim">&gt; Chạy mã đang tắt mặc định. App vẫn mở, sửa, kiểm tra và lưu mã bình thường.</div>';
        }
      }
    } catch (_) {
      state.codeExecutionEnabled = false;
      if (btnRun) btnRun.disabled = true;
      if (btnTrace) btnTrace.disabled = true;
      if (btnE1) btnE1.disabled = true;
      if (runText) runText.textContent = 'CHẠY ĐANG TẮT';
      if (traceStatusPill) {
        traceStatusPill.className = 'trace-status-pill cut';
        traceStatusPill.textContent = 'TẮT';
      }
      if (e1StatusPill) {
        e1StatusPill.className = 'trace-status-pill cut';
        e1StatusPill.textContent = 'TẮT';
      }
    }
  }

  // Quản lý Bố Cục IDE & Phông Chữ (Zoom)
  function applySidebarLayout() {
    const mainEl = document.getElementById('appMain');
    if (!mainEl) return;
    if (state.sidebarLeftCollapsed) mainEl.classList.add('left-collapsed');
    else mainEl.classList.remove('left-collapsed');

    if (state.sidebarRightCollapsed) mainEl.classList.add('right-collapsed');
    else mainEl.classList.remove('right-collapsed');
  }

  function toggleSidebarLeft() {
    state.sidebarLeftCollapsed = !state.sidebarLeftCollapsed;
    localStorage.setItem('aura_sidebar_left_collapsed', String(state.sidebarLeftCollapsed));
    applySidebarLayout();
  }

  function toggleSidebarRight() {
    state.sidebarRightCollapsed = !state.sidebarRightCollapsed;
    localStorage.setItem('aura_sidebar_right_collapsed', String(state.sidebarRightCollapsed));
    applySidebarLayout();
  }

  function setCodeFontSize(size) {
    const clamped = Math.max(10, Math.min(18, size));
    state.codeFontSize = clamped;
    document.documentElement.style.setProperty('--code-font-size', `${clamped}px`);
    const zoomEl = document.getElementById('zoomPercent');
    if (zoomEl) zoomEl.textContent = `${clamped}px`;
    localStorage.setItem('aura_code_font_size', String(clamped));
  }

  function setEditorMode(mode) {
    const validModes = ['cards', 'split', 'code'];
    const activeMode = validModes.includes(mode) ? mode : 'split';
    state.editorMode = activeMode;
    localStorage.setItem('aura_editor_mode', activeMode);

    const bodyEl = document.getElementById('canvasCenterBody');
    if (bodyEl) {
      bodyEl.classList.remove('mode-cards-only', 'mode-split-view', 'mode-code-only');
      if (activeMode === 'cards') bodyEl.classList.add('mode-cards-only');
      else if (activeMode === 'split') bodyEl.classList.add('mode-split-view');
      else if (activeMode === 'code') bodyEl.classList.add('mode-code-only');
    }

    const btnCards = document.getElementById('btnModeCards');
    const btnSplit = document.getElementById('btnModeSplit');
    const btnCode = document.getElementById('btnModeCode');
    if (btnCards) btnCards.classList.toggle('active', activeMode === 'cards');
    if (btnSplit) btnSplit.classList.toggle('active', activeMode === 'split');
    if (btnCode) btnCode.classList.toggle('active', activeMode === 'code');

    if (activeMode !== 'cards') {
      dongBoTheSangCodeEditor();
    }
    yeuCauChinhCotDoc();
  }

  function initEditorMode() {
    const saved = localStorage.getItem('aura_editor_mode') || 'split';
    setEditorMode(saved);
  }

  let dangGoTrongCodeEditor = false;
  let henGioDongBoCode = null;

  function capNhatSoDongGutter(soDong) {
    const gutter = document.getElementById('codeEditorGutter');
    if (!gutter) return;
    const n = Math.max(1, soDong);
    let str = '';
    for (let i = 1; i <= n; i++) {
      str += i + '\n';
    }
    gutter.textContent = str;
  }

  function dongBoTheSangCodeEditor(epBuoc = false) {
    const input = document.getElementById('codeEditorInput');
    const nameEl = document.getElementById('codeEditorFileName');
    const lineCountEl = document.getElementById('codeEditorLineCount');
    const badge = document.getElementById('codeSyncBadge');
    if (!input) return;

    if (nameEl) {
      nameEl.textContent = state.activeFileName || (state.activeFilePath ? state.activeFilePath.split(/[\\/]/).pop() : 'main.py');
    }

    // Nếu người dùng đang gõ trong code editor và không ép buộc -> không ghi đè tránh mất con trỏ
    if (dangGoTrongCodeEditor && !epBuoc) return;

    const code = TheValidator.sinhMaPython(state.tree);
    input.value = code;

    const lines = (code || '').split('\n').length;
    capNhatSoDongGutter(lines);
    if (lineCountEl) lineCountEl.textContent = `${lines} dòng`;
    if (badge) {
      badge.className = 'code-sync-badge ok';
      badge.textContent = 'Live-Sync ✓';
    }
  }

  function capNhatViTriConTroEditor() {
    const input = document.getElementById('codeEditorInput');
    const posEl = document.getElementById('codeEditorCursorPos');
    if (!input || !posEl) return;
    const sel = input.selectionStart || 0;
    const val = input.value.slice(0, sel);
    const lines = val.split('\n');
    const curLine = lines.length;
    const curCol = lines[lines.length - 1].length + 1;
    posEl.textContent = `Dòng ${curLine}, Cột ${curCol}`;
  }

  function setupCodeEditorPane() {
    const input = document.getElementById('codeEditorInput');
    const gutter = document.getElementById('codeEditorGutter');
    const splitterV = document.getElementById('editorSplitterV');
    const cardsPane = document.getElementById('canvasCardsPane');
    const codePane = document.getElementById('canvasCodePane');
    const btnCopy = document.getElementById('btnCopyCodeEditor');
    const badge = document.getElementById('codeSyncBadge');

    if (input) {
      input.addEventListener('focus', () => {
        dangGoTrongCodeEditor = true;
      });

      input.addEventListener('blur', () => {
        dangGoTrongCodeEditor = false;
      });

      input.addEventListener('keyup', capNhatViTriConTroEditor);
      input.addEventListener('click', capNhatViTriConTroEditor);

      input.addEventListener('scroll', () => {
        if (gutter) gutter.scrollTop = input.scrollTop;
      });

      // Phím Tab thụt lề 4 dấu cách
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = input.selectionStart;
          const end = input.selectionEnd;
          const val = input.value;
          if (e.shiftKey) {
            // Lùi lề 4 dấu cách
            const lineStart = val.lastIndexOf('\n', start - 1) + 1;
            if (val.slice(lineStart, lineStart + 4) === '    ') {
              input.value = val.slice(0, lineStart) + val.slice(lineStart + 4);
              input.selectionStart = input.selectionEnd = Math.max(lineStart, start - 4);
            }
          } else {
            // Tiến lề 4 dấu cách
            input.value = val.substring(0, start) + '    ' + val.substring(end);
            input.selectionStart = input.selectionEnd = start + 4;
          }
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });

      // Live-Sync khi gõ code
      input.addEventListener('input', () => {
        const val = input.value;
        const lines = val.split('\n').length;
        capNhatSoDongGutter(lines);
        const lineCountEl = document.getElementById('codeEditorLineCount');
        if (lineCountEl) lineCountEl.textContent = `${lines} dòng`;
        capNhatViTriConTroEditor();

        if (badge) {
          badge.className = 'code-sync-badge syncing';
          badge.textContent = 'Đang đồng bộ...';
        }

        clearTimeout(henGioDongBoCode);
        henGioDongBoCode = setTimeout(() => {
          // Đánh dấu đã sửa
          state.hasModifications = true;
          if (badge) {
            badge.className = 'code-sync-badge ok';
            badge.textContent = 'Live-Sync ✓';
          }
          veThanhTrangThai();
        }, 350);
      });
    }

    if (btnCopy && input) {
      btnCopy.addEventListener('click', () => {
        navigator.clipboard.writeText(input.value).then(() => {
          baoNhanh('Đã sao chép toàn bộ mã Python!');
        }).catch(() => {});
      });
    }

    // Splitter kéo dọc
    if (splitterV && cardsPane && codePane) {
      let isDraggingV = false;
      let startX = 0;
      let startCardsW = 0;

      splitterV.addEventListener('mousedown', (e) => {
        isDraggingV = true;
        startX = e.clientX;
        startCardsW = cardsPane.getBoundingClientRect().width;
        splitterV.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDraggingV) return;
        const deltaX = e.clientX - startX;
        const totalW = cardsPane.parentElement.getBoundingClientRect().width;
        const newCardsW = Math.max(220, Math.min(totalW - 240, startCardsW + deltaX));
        const pct = (newCardsW / totalW) * 100;
        cardsPane.style.flex = `0 0 ${pct}%`;
        codePane.style.flex = `0 0 ${100 - pct}%`;
        yeuCauChinhCotDoc();
      });

      window.addEventListener('mouseup', () => {
        if (isDraggingV) {
          isDraggingV = false;
          splitterV.classList.remove('dragging');
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          yeuCauChinhCotDoc();
        }
      });
    }

    // Nút chuyển chế độ
    const btnCards = document.getElementById('btnModeCards');
    const btnSplit = document.getElementById('btnModeSplit');
    const btnCode = document.getElementById('btnModeCode');

    if (btnCards) btnCards.addEventListener('click', () => setEditorMode('cards'));
    if (btnSplit) btnSplit.addEventListener('click', () => setEditorMode('split'));
    if (btnCode) btnCode.addEventListener('click', () => setEditorMode('code'));
  }

  function initLayoutPreferences() {
    // 1. Phông chữ mặc định 14px đọc được
    const savedFontSize = localStorage.getItem('aura_code_font_size');
    const initialFontSize = savedFontSize ? parseInt(savedFontSize, 10) : 14;
    setCodeFontSize(initialFontSize);

    // 2. Thu gọn cột bên
    const savedLeft = localStorage.getItem('aura_sidebar_left_collapsed');
    state.sidebarLeftCollapsed = (savedLeft === 'true');

    const savedRight = localStorage.getItem('aura_sidebar_right_collapsed');
    if (savedRight !== null) {
      state.sidebarRightCollapsed = (savedRight === 'true');
    } else {
      // Màn hình < 1100px thì cột phải (Trợ lý AI) mặc định thu gọn
      state.sidebarRightCollapsed = (window.innerWidth < 1100);
    }
    applySidebarLayout();

    // 3. Khởi tạo Chế độ Soạn Thảo (Thẻ / Song Song / Mã Thuần)
    initEditorMode();
  }

  // ==========================================================================
  // ==========================================================================
  // 2. KHỞI TẠO KHAY THẺ (6 NHÓM MÀU CHUẨN, 12 THẺ & BỘ ĐẾM ×N)
  // ==========================================================================
  // Nhãn cú pháp Python hiện trên mặt thẻ trong khay.
  //
  // 25/08: TRƯỚC ĐÂY LÀ MỘT CHUỖI if-else KHÔNG CÓ NHÁNH DỰ PHÒNG. Thêm 5 thẻ
  // mới thì cả 5 hiện lên khay với nhãn TRỐNG — kéo thả được, đếm ×N được, chỉ
  // là không ai đọc nổi nó là thẻ gì. Không test nào bắt được: thẻ vẫn tồn
  // tại, hàm vẫn trả về đúng, chỉ có mặt thẻ là trắng.
  //
  // Bắt được bằng cách mở app ra nhìn. Sửa ở GỐC — bảng tra cứu kèm dự phòng
  // `cardDef.ten` — nên thẻ thêm sau này cùng lắm hiện tên tiếng Việt, không
  // bao giờ hiện trống nữa.
  const NHAN_CU_PHAP = {
    gan: 'x = 10',
    in_ra: 'print(...)',
    neu: 'if cond:',
    nguoc_lai: 'else:',
    lap_moi: 'for i in day:',
    lap_khi: 'while cond:',
    tra_ve: 'return val',
    ham: 'def fn(args):',
    goi_ham: 'fn(args)',
    pheptinh: 'a + b',
    chu_thich: '# Chú thích',
    ma_tho: 'raw code',
    nhap: 'import lib',
    dung_lap: 'break',
    bo_qua: 'continue',
    thu: 'try:',
    bat_loi: 'except E as e:'
  };

  // Từ khoá Python mà mỗi loại thẻ SINH RA. Ô Tìm (Ctrl+F) gom cả bảng này vào
  // chữ của thẻ, vì `chuTrenThe` trước đây chỉ gom GIÁ TRỊ người dùng gõ.
  //
  // Đo 30/08/2026, chương trình đang hiện trên màn hình ở chế độ Mã Thuần là
  // `def chào(tên): ... print(chào(người))`, gõ vào ô Tìm:
  //     chào 1/3 · người 1/2 · danh_sách 1/2 · Sếp 1/1   <- tìm được
  //     def 0/0 · print 0/0 · return 0/0                 <- KHÔNG, dù nhìn thấy
  // Nhãn ô ghi "Tìm trong chương trình…", nên 0/0 đọc như là "chương trình
  // không có chữ def" — sai. Cùng họ với nhãn nói sai việc ở CLAUDE.md mục 4.
  //
  // KHÔNG dùng lại NHAN_CU_PHAP: nhãn ấy kèm chỗ giữ chỗ (`x = 10`,
  // `for i in day:`), nhét vào thì tìm `10` sẽ khớp MỌI thẻ gán, tìm `day` khớp
  // MỌI vòng lặp. Bảng này chỉ chứa từ khoá thật sự xuất hiện trong mã sinh ra.
  const TU_KHOA_PYTHON_CUA_THE = {
    in_ra: 'print',
    neu: 'if',
    nguoc_lai: 'else',
    lap_moi: 'for in',
    lap_khi: 'while',
    tra_ve: 'return',
    ham: 'def',
    chu_thich: '#',
    nhap: 'import',
    dung_lap: 'break',
    bo_qua: 'continue',
    thu: 'try',
    bat_loi: 'except as'
  };

  // ==========================================================================
  // EXTENSION MANAGER & KHO GÓI THẺ CHUYÊN DỤNG (CARD PACKS)
  // ==========================================================================
  const DANH_SACH_EXTENSIONS = [
    {
      id: 'pack_datasci',
      ten: 'Pandas & Data Science Pack',
      phien_ban: 'v1.2.0',
      danh_muc: 'du_lieu',
      icon: '📊',
      mo_ta: 'Xử lý bảng biểu DataFrame, đọc file CSV/Excel, thống kê dữ liệu tổng quan và vẽ biểu đồ trực quan.',
      cards: [
        { ma: 'ma_tho', nhan: 'df = pd.read_csv(...)', ten: 'Đọc File CSV', o: { nguyen_van: 'import pandas as pd\ndf = pd.read_csv("data.csv")' } },
        { ma: 'ma_tho', nhan: 'df_loc = df[...]', ten: 'Lọc Dữ Liệu', o: { nguyen_van: 'df_loc = df[df["score"] >= 8.0]' } },
        { ma: 'ma_tho', nhan: 'df.describe()', ten: 'Thống Kê Tổng Quan', o: { nguyen_van: 'print(df.describe())' } },
        { ma: 'ma_tho', nhan: 'df.plot(kind="bar")', ten: 'Vẽ Biểu Đồ Cột', o: { nguyen_van: 'import matplotlib.pyplot as plt\ndf.plot(kind="bar")\nplt.show()' } }
      ]
    },
    {
      id: 'pack_web',
      ten: 'Web Scraping & Requests Pack',
      phien_ban: 'v1.0.4',
      danh_muc: 'web',
      icon: '🌐',
      mo_ta: 'Tự động hóa gửi yêu cầu HTTP Requests, bóc tách cấu trúc HTML BeautifulSoup và trích xuất JSON API.',
      cards: [
        { ma: 'ma_tho', nhan: 'res = requests.get(url)', ten: 'Gửi GET Request', o: { nguyen_van: 'import requests\nres = requests.get("https://api.example.com/data")' } },
        { ma: 'ma_tho', nhan: 'data = res.json()', ten: 'Đọc JSON Response', o: { nguyen_van: 'data = res.json()' } },
        { ma: 'ma_tho', nhan: 'soup = BeautifulSoup(...)', ten: 'Bóc Tách HTML', o: { nguyen_van: 'from bs4 import BeautifulSoup\nsoup = BeautifulSoup(res.text, "html.parser")' } }
      ]
    },
    {
      id: 'pack_ai',
      ten: 'GenAI & LLM Connect Pack',
      phien_ban: 'v2.1.0',
      danh_muc: 'ai',
      icon: '🤖',
      mo_ta: 'Tích hợp gọi mô hình ngôn ngữ lớn (LLM), thiết lập prompt thông minh và phân tích văn bản tự động.',
      cards: [
        { ma: 'ma_tho', nhan: 'prompt = f"Phân tích: ..."', ten: 'Tạo Prompt Thông Minh', o: { nguyen_van: 'prompt = f"Hãy phân tích và tóm tắt văn bản: {van_ban}"' } },
        { ma: 'ma_tho', nhan: 'ai.generate_content(...)', ten: 'Gọi Mô Hình LLM', o: { nguyen_van: '# Gọi mô hình AI sinh câu trả lời\nphan_hoi = "Nội dung phản hồi từ AI..."' } }
      ]
    },
    {
      id: 'pack_game',
      ten: 'Pygame 2D Mini Game Pack',
      phien_ban: 'v1.1.2',
      danh_muc: 'game',
      icon: '🎮',
      mo_ta: 'Khởi tạo màn hình game, vòng lặp hoạt họa FPS, bắt sự kiện bàn phím và vẽ nhân vật 2D.',
      cards: [
        { ma: 'ma_tho', nhan: 'pygame.init()', ten: 'Khởi Tạo Game', o: { nguyen_van: 'import pygame\npygame.init()\nscreen = pygame.display.set_mode((800, 600))\npygame.display.set_caption("My AURA Game")' } },
        { ma: 'ma_tho', nhan: 'while running: game_loop', ten: 'Vòng Lặp Game Loop', o: { nguyen_van: 'running = True\nclock = pygame.time.Clock()\nwhile running:\n    for event in pygame.event.get():\n        if event.type == pygame.QUIT:\n            running = False\n    clock.tick(60)' } }
      ]
    }
  ];

  let extDanhMucDangChon = 'all';
  let extTuKhoaTimKiem = '';

  function layGoiExtensionDaCai() {
    try {
      const saved = localStorage.getItem('aura_installed_extensions');
      if (saved) return JSON.parse(saved);
    } catch (_) {}
    return ['pack_datasci', 'pack_ai'];
  }

  function luuGoiExtensionDaCai(list) {
    try {
      localStorage.setItem('aura_installed_extensions', JSON.stringify(list));
    } catch (_) {}
  }

  function caiDatGoiExtension(packId) {
    const list = layGoiExtensionDaCai();
    if (!list.includes(packId)) {
      list.push(packId);
      luuGoiExtensionDaCai(list);
      renderToolbox();
      veDanhSachExtensions();
      veSidebarExtensions();
      baoNhanh('Đã cài đặt gói extension thành công!');
    }
  }

  function goGoiExtension(packId) {
    let list = layGoiExtensionDaCai();
    list = list.filter(id => id !== packId);
    luuGoiExtensionDaCai(list);
    renderToolbox();
    veDanhSachExtensions();
    veSidebarExtensions();
    baoNhanh('Đã gỡ bỏ gói extension!');
  }

  function veDanhSachExtensions() {
    const container = document.getElementById('extensionsListContainer');
    if (!container) return;

    const installed = layGoiExtensionDaCai();
    const filtered = DANH_SACH_EXTENSIONS.filter(ext => {
      let matchCat = true;
      if (extDanhMucDangChon === 'installed') {
        matchCat = installed.includes(ext.id);
      } else if (extDanhMucDangChon !== 'all') {
        matchCat = (ext.danh_muc === extDanhMucDangChon);
      }
      const kw = extTuKhoaTimKiem.trim().toLowerCase();
      const matchKw = !kw || ext.ten.toLowerCase().includes(kw) || ext.mo_ta.toLowerCase().includes(kw);
      return matchCat && matchKw;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 32px 16px; color: var(--text-muted);">
          <div style="font-size: 28px; margin-bottom: 8px;">🧩</div>
          <p>Không tìm thấy extension hoặc gói thẻ nào phù hợp.</p>
        </div>
      `;
      return;
    }

    let html = '<div class="ext-grid">';
    filtered.forEach(ext => {
      const isInst = installed.includes(ext.id);
      // 30/08/2026 — chip TUNG lay tu ext.the_kem_theo, mot danh sach ten viet tay
      // tach roi khoi ext.cards la thu thuc su duoc cai vao Khay The. Do doi chieu:
      //   pack_datasci  quang cao 4 · thuc co 4   khop
      //   pack_web      quang cao 4 · thuc co 3   lech
      //   pack_ai       quang cao 3 · thuc co 2   lech
      //   pack_game     quang cao 4 · thuc co 2   lech
      // Nay dung chip TU chinh ext.cards, nen quang cao khong the vuot qua hang.
      const chipsHtml = (ext.cards || []).map(c => `<span class="ext-card-chip">+ ${escapeHtml(c.ten || c.nhan)}</span>`).join('');

      html += `
        <div class="ext-card" data-extid="${ext.id}">
          <div class="ext-card-header">
            <div class="ext-icon-box ${ext.danh_muc}">${ext.icon}</div>
            <div class="ext-header-info">
              <div class="ext-name-row">
                <span class="ext-name">${escapeHtml(ext.ten)}</span>
                <span class="ext-version">${ext.phien_ban}</span>
              </div>
              <div class="ext-meta-row">
                <span class="ext-meta-author">${ext.cards.length} thẻ</span>
                <span>•</span>
                <span class="ext-meta-author">Gói dựng sẵn trong app</span>
              </div>
            </div>
          </div>

          <div class="ext-desc">${escapeHtml(ext.mo_ta)}</div>

          <div class="ext-included-cards">
            <span style="font-size: 10px; color: var(--text-muted); width: 100%; margin-bottom: 2px;">Thẻ bổ sung cho Khay Thẻ:</span>
            ${chipsHtml}
          </div>

          <div class="ext-card-footer">
            <span class="wf-badge-category ${ext.danh_muc}">${ext.danh_muc.toUpperCase()}</span>
            ${isInst ? 
              `<button class="btn-ext-installed" data-action="uninstall" data-extid="${ext.id}">✓ Đã Cài Đặt (Gỡ)</button>` : 
              `<button class="btn-ext-install" data-action="install" data-extid="${ext.id}">+ Cài Đặt</button>`
            }
          </div>
        </div>
      `;
    });
    html += '</div>';

    container.innerHTML = html;

    container.querySelectorAll('button[data-action]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const action = btn.getAttribute('data-action');
        const packId = btn.getAttribute('data-extid');
        if (action === 'install') {
          caiDatGoiExtension(packId);
        } else if (action === 'uninstall') {
          goGoiExtension(packId);
        }
      });
    });
  }

  function veSidebarExtensions() {
    const container = document.getElementById('extSidebarContainer');
    if (!container) return;

    const installed = layGoiExtensionDaCai();
    const installedPacks = DANH_SACH_EXTENSIONS.filter(p => installed.includes(p.id));

    let html = `
      <div class="ext-sidebar-header-action">
        <span>Gói Đã Cài (${installedPacks.length})</span>
        <button id="btnOpenExtMarketplace">+ Khám Phá</button>
      </div>
    `;

    if (installedPacks.length === 0) {
      html += `
        <div style="text-align: center; padding: 24px 12px; color: var(--text-muted); font-size: 12px;">
          Chưa cài gói thẻ nào.<br>Bấm "+ Khám Phá" để cài thêm.
        </div>
      `;
    } else {
      installedPacks.forEach(pack => {
        html += `
          <div class="ext-sidebar-item">
            <div class="ext-sidebar-item-top">
              <span class="ext-sidebar-item-title">${pack.icon} ${escapeHtml(pack.ten)}</span>
              <button style="background: none; border: none; color: #F87171; cursor: pointer; font-size: 11px;" data-remove-ext="${pack.id}" title="Gỡ gói này">Gỡ</button>
            </div>
            <div class="ext-sidebar-item-desc">${escapeHtml(pack.mo_ta)}</div>
          </div>
        `;
      });
    }

    container.innerHTML = html;

    const btnMarket = document.getElementById('btnOpenExtMarketplace');
    if (btnMarket) {
      btnMarket.addEventListener('click', () => {
        const modal = document.getElementById('extensionsModal');
        if (modal) {
          modal.style.display = 'flex';
          veDanhSachExtensions();
        }
      });
    }

    container.querySelectorAll('button[data-remove-ext]').forEach(btn => {
      btn.addEventListener('click', () => {
        const packId = btn.getAttribute('data-remove-ext');
        goGoiExtension(packId);
      });
    });
  }

  function setupExtensionHubControls() {
    const searchInput = document.getElementById('extSearchInput');
    const catTabs = document.getElementById('extCatTabs');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        extTuKhoaTimKiem = e.target.value;
        veDanhSachExtensions();
      });
    }

    if (catTabs) {
      catTabs.querySelectorAll('.wf-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          catTabs.querySelectorAll('.wf-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          extDanhMucDangChon = btn.getAttribute('data-extcat') || 'all';
          veDanhSachExtensions();
        });
      });
    }
  }

  function renderToolbox() {
    const container = document.getElementById('toolboxContainer');
    if (!container) return;
    container.innerHTML = '';

    const groups = [
      { id: 'ham', title: 'Hàm (Cam)', color: 'var(--ham)', cards: ['ham', 'goi_ham', 'tra_ve'] },
      { id: 'dieu_khien', title: 'Điều khiển (Xanh dương)', color: 'var(--dk)', cards: ['neu', 'nguoc_lai', 'lap_moi', 'lap_khi', 'dung_lap', 'bo_qua', 'thu', 'bat_loi'] },
      { id: 'du_lieu', title: 'Dữ liệu (Xanh lá)', color: 'var(--dl)', cards: ['gan', 'pheptinh'] },
      { id: 'vao_ra', title: 'Vào / Ra (Tím)', color: 'var(--vr)', cards: ['nhap', 'in_ra'] },
      { id: 'chu_thich', title: 'Chú thích (Xanh ngọc)', color: 'var(--ct)', cards: ['chu_thich'] },
      { id: 'ma_tho', title: 'Mã thô (Xám)', color: 'var(--tho)', cards: ['ma_tho'] }
    ];

    // 1. Render các nhóm thẻ cốt lõi
    groups.forEach(g => {
      const groupEl = document.createElement('div');
      groupEl.className = 'tool-group';
      groupEl.id = `group_${g.id}`;

      const titleEl = document.createElement('div');
      titleEl.className = 'group-title';
      titleEl.textContent = g.title;
      titleEl.style.color = g.color;
      groupEl.appendChild(titleEl);

      const cardsGrid = document.createElement('div');
      cardsGrid.className = 'tool-group-cards';

      g.cards.forEach(cardMa => {
        const cardDef = TheValidator.BO_THE_V1[cardMa];
        if (!cardDef) return;

        const itemEl = document.createElement('div');
        itemEl.className = 'tool-item';
        itemEl.dataset.ma = cardMa;
        itemEl.style.borderLeftColor = g.color;
        itemEl.draggable = true;
        itemEl.title = `Thẻ ${cardDef.ten}: Click để chèn nhanh hoặc kéo vào canvas`;

        const infoEl = document.createElement('div');
        infoEl.className = 'tool-info';

        const syntaxEl = document.createElement('span');
        syntaxEl.className = 'tool-syntax';
        syntaxEl.textContent = NHAN_CU_PHAP[cardMa] || cardDef.ten;
        infoEl.appendChild(syntaxEl);

        itemEl.appendChild(infoEl);

        // Badge đếm xN
        const badgeEl = document.createElement('span');
        badgeEl.className = 'count-badge';
        badgeEl.id = `countBadge_${cardMa}`;
        badgeEl.textContent = '×0';
        itemEl.appendChild(badgeEl);

        itemEl.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'NEW_CARD', ma: cardMa }));
        });

        itemEl.addEventListener('click', () => {
          addNewCardToRoot(cardMa);
        });

        cardsGrid.appendChild(itemEl);
      });

      groupEl.appendChild(cardsGrid);
      container.appendChild(groupEl);
    });

    // 2. Render thêm các nhóm thẻ từ Extension Pack đã cài đặt
    const installedPacks = layGoiExtensionDaCai();
    installedPacks.forEach(packId => {
      const pack = DANH_SACH_EXTENSIONS.find(p => p.id === packId);
      if (!pack || !pack.cards) return;

      const groupEl = document.createElement('div');
      groupEl.className = 'tool-group ext-pack';
      groupEl.id = `group_${pack.id}`;

      const titleEl = document.createElement('div');
      titleEl.className = 'group-title';
      titleEl.textContent = `${pack.icon} ${pack.ten}`;
      titleEl.style.color = '#818CF8';
      groupEl.appendChild(titleEl);

      const cardsGrid = document.createElement('div');
      cardsGrid.className = 'tool-group-cards';

      pack.cards.forEach(cardItem => {
        const itemEl = document.createElement('div');
        itemEl.className = 'tool-item';
        itemEl.dataset.ma = cardItem.ma;
        itemEl.style.borderLeftColor = '#818CF8';
        itemEl.draggable = true;
        itemEl.title = `${cardItem.ten}: Click hoặc kéo vào canvas`;

        const infoEl = document.createElement('div');
        infoEl.className = 'tool-info';

        const syntaxEl = document.createElement('span');
        syntaxEl.className = 'tool-syntax';
        syntaxEl.textContent = cardItem.nhan || cardItem.ten;
        infoEl.appendChild(syntaxEl);
        itemEl.appendChild(infoEl);

        itemEl.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain', JSON.stringify({
            type: 'NEW_CARD',
            ma: cardItem.ma,
            customO: cardItem.o
          }));
        });

        itemEl.addEventListener('click', () => {
          addNewCardToRoot(cardItem.ma, cardItem.o);
        });

        cardsGrid.appendChild(itemEl);
      });

      groupEl.appendChild(cardsGrid);
      container.appendChild(groupEl);
    });

    // Vùng thả để XOÁ — chiều ngược của kéo-từ-khay-vào-canvas. Chỉ hiện đỏ khi
    // đang kéo một thẻ THẬT SỰ có trên canvas (state.draggingCardId), để kéo
    // một thẻ mẫu từ khay rồi buông ngay trên khay không bị hiểu nhầm là xoá.
    container.addEventListener('dragover', (e) => {
      if (!state.draggingCardId) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      container.classList.add('vung-tha-xoa');
    });
    container.addEventListener('dragleave', (e) => {
      if (e.target === container) container.classList.remove('vung-tha-xoa');
    });
    container.addEventListener('drop', (e) => {
      e.preventDefault();
      container.classList.remove('vung-tha-xoa');
      const raw = e.dataTransfer.getData('text/plain');
      if (!raw) return;
      try {
        const payload = JSON.parse(raw);
        if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
          if (layVaXoaTheTheoId(payload.nodeId)) {
            onTreeChanged();
          }
        }
      } catch (_) {}
    });
  }

  function updateToolboxCounters() {
    const counts = state.diagnostics.so_lan_dung_the || {};
    for (const cardMa in TheValidator.BO_THE_V1) {
      const badge = document.getElementById(`countBadge_${cardMa}`);
      if (badge) {
        const c = counts[cardMa] || 0;
        badge.textContent = `×${c}`;
        if (c > 0) {
          badge.classList.add('active');
        } else {
          badge.classList.remove('active');
        }
      }
    }
  }

  // ==========================================================================
  // 3. RENDER VÙNG SOẠN THẢO THẺ NỐI THẲNG (mau_the_noi_thang.html)
  // ==========================================================================
  function chinhCotDoc() {
    if (typeof document === 'undefined') return;
    document.querySelectorAll('.khoi').forEach(function(k) {
      const hang = Array.prototype.filter.call(k.children, function(e) {
        return e.classList.contains('hang');
      });
      if (!hang.length) return;
      const cuoi = hang[hang.length - 1];
      const rk = k.getBoundingClientRect();
      const rc = cuoi.getBoundingClientRect();
      k.style.setProperty('--cao-cot', Math.round(rc.top + rc.height / 2 - rk.top + 4) + 'px');
    });
  }

  function yeuCauChinhCotDoc() {
    if (typeof document === 'undefined') return;
    chinhCotDoc();
    if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(() => {
        chinhCotDoc();
        window.requestAnimationFrame(chinhCotDoc);
      });
    }
  }

  function taoTheNode(ma, customO = null) {
    state.nodeIdCounter++;
    const cardDef = TheValidator.BO_THE_V1[ma];
    const initialO = {};
    if (cardDef && cardDef.o) {
      cardDef.o.forEach(oDef => {
        initialO[oDef.ten] = oDef.goi_y || '';
      });
    }
    if (customO && typeof customO === 'object') {
      Object.assign(initialO, customO);
    }
    return {
      id: `the_${ma}_${state.nodeIdCounter}`,
      ma: ma,
      o: initialO,
      than: [],
      da_sua: true
    };
  }

  function addNewCardToRoot(ma, customO = null) {
    const node = taoTheNode(ma, customO);
    state.tree.push(node);
    onTreeChanged();
  }

  // Tìm node theo id trong cây (kể cả khối con .than), KHÔNG xoá — nền dùng
  // chung cho cả xoá (kéo ra khay) lẫn di chuyển (kéo sắp xếp lại).
  function timTheTheoId(danhSach, nodeId) {
    for (let i = 0; i < danhSach.length; i++) {
      if (danhSach[i].id === nodeId) {
        return { node: danhSach[i], dsCha: danhSach, chiSo: i };
      }
      if (danhSach[i].than && danhSach[i].than.length > 0) {
        const sau = timTheTheoId(danhSach[i].than, nodeId);
        if (sau) return sau;
      }
    }
    return null;
  }

  // Xoá node theo id, trả về node đã xoá (hoặc null nếu không thấy). Dùng
  // cho kéo thẻ NGƯỢC từ canvas ra khay để xoá — cùng thao tác splice như
  // nút ✕, chỉ khác điểm vào (kéo thả thay vì bấm nút).
  function layVaXoaTheTheoId(nodeId) {
    const tim = timTheTheoId(state.tree, nodeId);
    if (!tim) return null;
    tim.dsCha.splice(tim.chiSo, 1);
    return tim.node;
  }

  // `node` có phải chính là `targetId`, hoặc `targetId` nằm trong khối con
  // (.than) của `node`? Chặn kéo một khối THẢ VÀO CHÍNH THÂN NÓ (hoặc thân
  // của một khối con của nó) — việc này sẽ tạo một cây có node chứa chính
  // nó, vỡ mọi thứ đọc cây bằng đệ quy (kể cả renderCard đang gọi hàm này).
  function laTuThaVaoChinhNoHoacConNo(node, targetId) {
    if (!targetId) return false;
    if (node.id === targetId) return true;
    if (!node.than) return false;
    return node.than.some(con => laTuThaVaoChinhNoHoacConNo(con, targetId));
  }

  // Di chuyển một thẻ ĐÃ CÓ tới vị trí mới — dùng cho kéo sắp xếp lại thứ tự.
  //   dsDich:     mảng đích (state.tree hoặc node.than nào đó)
  //   idKhoiDich: id của thẻ đang SỞ HỮU dsDich (null nếu dsDich là gốc
  //               state.tree) — dùng để chặn tự-thả-vào-thân-mình
  //   viTri:      chỉ số muốn chèn vào, tính TRÊN dsDich TRƯỚC khi rút thẻ
  //               cũ ra (nếu cùng mảng, hàm tự bù lại chỗ vừa rút)
  function diChuyenThe(nodeId, dsDich, idKhoiDich, viTri) {
    const tim = timTheTheoId(state.tree, nodeId);
    if (!tim) return false;
    const { node, dsCha, chiSo } = tim;

    if (laTuThaVaoChinhNoHoacConNo(node, idKhoiDich)) return false;

    let viTriMoi = viTri;
    if (dsCha === dsDich && chiSo < viTriMoi) viTriMoi -= 1;

    dsCha.splice(chiSo, 1);
    dsDich.splice(viTriMoi, 0, node);
    return true;
  }

  function createCodeInput(node, fieldName, placeholder = '', className = '') {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = `the-inline-input ${className}`.trim();
    let val = (node.o && node.o[fieldName] !== undefined) ? String(node.o[fieldName]) : '';
    if (node.ma === 'chu_thich' && fieldName === 'noi_dung' && val.startsWith('#')) {
      val = val.replace(/^#\s*/, '');
    }
    input.value = val;
    input.placeholder = placeholder || fieldName;
    input.spellcheck = false;
    input.autocomplete = 'off';

    function updateWidth() {
      const len = (input.value || input.placeholder || '').length;
      input.style.width = Math.max(len + 1, 2) + 'ch';
    }
    updateWidth();

    // Ctrl+Bấm vào một cái tên trong ô -> nhảy tới thẻ khai ra nó.
    // Chỉ khi GIỮ Ctrl: bấm thường vẫn phải đặt được con trỏ để gõ.
    input.addEventListener('click', (e) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const tu = tuDuoiConTro(input);
      if (tu) nhayToiDinhNghia(tu);
    });

    input.addEventListener('input', (e) => {
      if (!node.o) node.o = {};
      node.o[fieldName] = e.target.value;
      updateWidth();
      node.da_sua = true;
      onTreeChanged(false);
    });

    return input;
  }

  /** Một mẩu từ khoá Python cố định trên mặt thẻ (không sửa được). */
  function tuKhoa(chu) {
    const el = document.createElement('span');
    el.className = 'ma';
    el.textContent = chu;
    return el;
  }

  function renderCodeLineContent(node, cardDef) {
    const wrap = document.createElement('span');
    wrap.className = 'the-content';

    if (node.ma === 'gan') {
      wrap.appendChild(createCodeInput(node, 'ten_bien', 'x', 'ma'));
      const op = document.createElement('span');
      op.className = 'ma';
      op.textContent = ' = ';
      wrap.appendChild(op);
      wrap.appendChild(createCodeInput(node, 'gia_tri', 'giá_trị', 'n'));
    } else if (node.ma === 'in_ra') {
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = 'print(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'noi_dung', 'nội_dung', 's'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);
    } else if (node.ma === 'ham') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = (node.o && node.o.async === '1') ? 'async def ' : 'def ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'ten_ham', 'tên_hàm', 'fn'));
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = '(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'tham_so', 'tham_số', 'ma'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);

      if (node.o && (node.o.kieu_tra_ve || node.o.kieu_tra_ve === '')) {
        const arrow = document.createElement('span');
        arrow.className = 'kw';
        arrow.textContent = ' -> ';
        wrap.appendChild(arrow);
        wrap.appendChild(createCodeInput(node, 'kieu_tra_ve', 'kiểu', 'fn'));
      }

      const pColon = document.createElement('span');
      pColon.className = 'ma';
      pColon.textContent = ':';
      wrap.appendChild(pColon);
    } else if (node.ma === 'neu') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = (node.o && node.o.noi_tiep === '1') ? 'elif ' : 'if ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'dieu_kien', 'điều_kiện', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'nguoc_lai') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'else';
      wrap.appendChild(kw);
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'lap_moi') {
      const kw1 = document.createElement('span');
      kw1.className = 'kw';
      kw1.textContent = 'for ';
      wrap.appendChild(kw1);
      wrap.appendChild(createCodeInput(node, 'bien', 'i', 'ma'));
      const kw2 = document.createElement('span');
      kw2.className = 'kw';
      kw2.textContent = ' in ';
      wrap.appendChild(kw2);
      wrap.appendChild(createCodeInput(node, 'day', 'range(10)', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'lap_khi') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'while ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'dieu_kien', 'điều_kiện', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'tra_ve') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'return ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'gia_tri', 'giá_trị', 'n'));
    } else if (node.ma === 'goi_ham') {
      wrap.appendChild(createCodeInput(node, 'ten_ham', 'tên_hàm', 'fn'));
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = '(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'doi_so', 'đối_số', 's'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);
    } else if (node.ma === 'pheptinh') {
      wrap.appendChild(createCodeInput(node, 'trai', 'vế_trái', 'ma'));
      wrap.appendChild(createCodeInput(node, 'phep', '+', 'kw'));
      wrap.appendChild(createCodeInput(node, 'phai', 'vế_phải', 'ma'));
    } else if (node.ma === 'chu_thich') {
      const cm = document.createElement('span');
      cm.className = 'cm';
      cm.textContent = '# ';
      wrap.appendChild(cm);
      wrap.appendChild(createCodeInput(node, 'noi_dung', 'chú thích...', 'cm'));
    } else if (node.ma === 'ma_tho') {
      const rawVal = (node.o && node.o.nguyen_van !== undefined) ? node.o.nguyen_van : (node.raw_text || '');
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'the-inline-input ma';
      input.value = rawVal;
      input.placeholder = '# Mã Python thô...';
      input.spellcheck = false;
      input.autocomplete = 'off';

      function updateRawWidth() {
        const len = (input.value || input.placeholder || '').length;
        input.style.width = Math.max(len + 1, 6) + 'ch';
      }
      updateRawWidth();

      input.addEventListener('input', (e) => {
        if (!node.o) node.o = {};
        node.o.nguyen_van = e.target.value;
        updateRawWidth();
        node.da_sua = true;
        onTreeChanged(false);
      });
      wrap.appendChild(input);
    } else if (node.ma === 'nhap') {
      // Hình dạng TĨNH, không đổi theo giá trị đang gõ.
      //
      // `createCodeInput` bắn `onTreeChanged(false)` mỗi phím — hàm ấy KHÔNG
      // vẽ lại cây (vẽ lại thì mất con trỏ giữa lúc gõ). Nên từ khoá động kiểu
      // "gõ vào ô `lấy` thì `import` đổi thành `from`" sẽ không đổi kịp, và
      // người dùng thấy mặt thẻ nói một đằng khung mã nói một nẻo.
      //
      // `import` đứng đầu đúng trong CẢ HAI dạng sinh ra, nên đặt nó tĩnh;
      // hai ô còn lại mang nhãn mờ. Khung mã bên phải luôn là sự thật.
      wrap.appendChild(tuKhoa('import '));
      wrap.appendChild(createCodeInput(node, 'thu_vien', 'math', 'ma'));
      wrap.appendChild(tuKhoa(' lấy '));
      wrap.appendChild(createCodeInput(node, 'phan', 'cả thư viện', 'ma'));
      wrap.appendChild(tuKhoa(' as '));
      wrap.appendChild(createCodeInput(node, 'ten_khac', '—', 'ma'));
    } else if (node.ma === 'bat_loi') {
      wrap.appendChild(tuKhoa('except '));
      wrap.appendChild(createCodeInput(node, 'loai_loi', 'Exception', 'ma'));
      wrap.appendChild(tuKhoa(' as '));
      wrap.appendChild(createCodeInput(node, 'ten_bien', '—', 'ma'));
      wrap.appendChild(tuKhoa(':'));
    } else if (node.ma === 'thu') {
      wrap.appendChild(tuKhoa('try:'));
    } else if (node.ma === 'dung_lap') {
      wrap.appendChild(tuKhoa('break'));
    } else if (node.ma === 'bo_qua') {
      wrap.appendChild(tuKhoa('continue'));
    } else if (cardDef.o && cardDef.o.length > 0) {
      cardDef.o.forEach((oDef, idx) => {
        if (idx > 0) {
          const sep = document.createElement('span');
          sep.className = 'ma';
          sep.textContent = ' ';
          wrap.appendChild(sep);
        }
        wrap.appendChild(createCodeInput(node, oDef.ten, oDef.goi_y || oDef.ten, 'ma'));
      });
    }

    return wrap;
  }

  // Dòng thẻ đang được đánh dấu "sẽ chèn trước/sau đây" trong lúc kéo. Theo
  // dõi ĐÚNG MỘT phần tử ở đây thay vì quét toàn bộ DOM mỗi lần dragover —
  // cây có thể tới vài trăm thẻ (281 trên core/web_search.py), dragover bắn
  // liên tục khi rê chuột.
  let hangDangDanhDau = null;
  function danhDauViTriTha(hangEl, truoc) {
    if (hangDangDanhDau && hangDangDanhDau !== hangEl) {
      hangDangDanhDau.classList.remove('tha-truoc-hang', 'tha-sau-hang');
    }
    hangEl.classList.toggle('tha-truoc-hang', truoc);
    hangEl.classList.toggle('tha-sau-hang', !truoc);
    hangDangDanhDau = hangEl;
  }
  function xoaDanhDauViTriTha() {
    if (hangDangDanhDau) {
      hangDangDanhDau.classList.remove('tha-truoc-hang', 'tha-sau-hang');
      hangDangDanhDau = null;
    }
  }

  function renderCard(node, parentList, index, depth = 1, parentBlockId = null) {
    const cardDef = TheValidator.BO_THE_V1[node.ma] || { ten: node.ma, mau: '#6B7280', co_than: false, o: [] };
    
    // Tìm lỗi / cảnh báo ứng với nút này
    const nodeDiags = (state.diagnostics.danh_sach || []).filter(d => d.node_id === node.id);
    const hasDo = nodeDiags.some(d => d.muc_do === 'do');
    const hasVang = nodeDiags.some(d => d.muc_do === 'vang');

    // Xác định lớp màu và CSS variable theo nhóm chuẩn
    // 25/08: TRƯỚC ĐÂY LÀ DANH SÁCH TÊN THẺ CHÉP TAY. Thêm 5 thẻ mới thì cả
    // 5 rơi vào nhánh `else` và nhận màu XÁM của "mã thô" — `nhap` đáng lẽ
    // tím, bốn thẻ điều khiển đáng lẽ xanh dương. Không test nào bắt được:
    // thẻ vẫn dựng lên, vẫn kéo được, chỉ sai màu. Bắt được bằng cách mở app
    // ra nhìn.
    //
    // Nhóm đã nằm sẵn trong `BO_THE_V1[ma].nhom` — chép tay lần hai là tự
    // tạo ra chỗ để hai bên trôi khỏi nhau.
    const NHOM_LOP = {
      ham: ['c-ham', 'var(--ham)'],
      dieu_khien: ['c-dk', 'var(--dk)'],
      du_lieu: ['c-dl', 'var(--dl)'],
      vao_ra: ['c-vr', 'var(--vr)'],
      chu_thich: ['c-ct', 'var(--ct)'],
      ma_tho: ['c-tho', 'var(--tho)']
    };
    const defnMau = TheValidator.BO_THE_V1[node.ma];
    const [colorClass, groupVar] = NHOM_LOP[defnMau && defnMau.nhom] || ['c-tho', 'var(--tho)'];

    const fragment = document.createDocumentFragment();

    // 1. Dòng thẻ (.hang)
    const hangEl = document.createElement('div');
    hangEl.className = 'hang';
    hangEl.style.color = groupVar;
    hangEl.id = `node_${node.id}`;
    hangEl.dataset.nodeId = node.id;

    // Kéo NGƯỢC: từ canvas ra khay để xoá — chiều còn thiếu trước 24/08, khay
    // chỉ kéo được một chiều (khay -> canvas). `input, button` trong dòng thẻ
    // cần giữ được bấm/chọn chữ bình thường nên chặn drag khi bắt đầu từ đó.
    hangEl.draggable = true;
    // Bấm vào DÒNG thẻ thì chọn nó. Bấm vào ô nhập / nút thì KHÔNG chọn —
    // lúc ấy người dùng đang gõ hoặc đang bấm nút, không phải đang chọn thẻ.
    hangEl.addEventListener('click', (e) => {
      if (e.target.closest('input, textarea, select, button')) return;
      chonThe(node.id);
    });

    hangEl.addEventListener('dragstart', (e) => {
      if (e.target.closest('input, textarea, select, button')) {
        e.preventDefault();
        return;
      }
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'EXISTING_CARD', nodeId: node.id }));
      state.draggingCardId = node.id;
      hangEl.classList.add('dang-keo-ra');
    });
    hangEl.addEventListener('dragend', () => {
      state.draggingCardId = null;
      hangEl.classList.remove('dang-keo-ra');
      const tc = document.getElementById('toolboxContainer');
      if (tc) tc.classList.remove('vung-tha-xoa');
      xoaDanhDauViTriTha();
    });

    // Kéo SẮP XẾP LẠI: rê một thẻ (từ khay hoặc từ chỗ khác trên canvas) tới
    // gần dòng này — thả nửa TRÊN thì chèn trước, nửa DƯỚI thì chèn sau.
    // stopPropagation để khối .khoi/canvas bao ngoài không tô viền chồng lên.
    hangEl.addEventListener('dragover', (e) => {
      if (state.draggingCardId === node.id) return; // đang kéo chính mình
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
      const r = hangEl.getBoundingClientRect();
      const truoc = (e.clientY - r.top) < r.height / 2;
      danhDauViTriTha(hangEl, truoc);
    });
    hangEl.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const chenTruoc = hangEl.classList.contains('tha-truoc-hang');
      xoaDanhDauViTriTha();
      const raw = e.dataTransfer.getData('text/plain');
      if (!raw) return;
      try {
        const payload = JSON.parse(raw);
        const viTri = chenTruoc ? index : index + 1;
        if (payload.type === 'NEW_CARD') {
          const newNode = taoTheNode(payload.ma, payload.customO);
          parentList.splice(viTri, 0, newNode);
          onTreeChanged();
        } else if (payload.type === 'EXISTING_CARD' && payload.nodeId && payload.nodeId !== node.id) {
          if (diChuyenThe(payload.nodeId, parentList, parentBlockId, viTri)) {
            onTreeChanged();
          }
        }
      } catch (_) {}
    });

    // 2. Thẻ viên thuốc (.the)
    const theEl = document.createElement('span');
    theEl.className = `the ${colorClass} ${hasDo ? 'status-do' : (hasVang ? 'status-vang' : '')}`;

    // Lỗ cạnh TRÁI (.lo)
    const loEl = document.createElement('span');
    loEl.className = 'lo';
    theEl.appendChild(loEl);

    // Chấm báo lỗi / cảnh báo
    if (hasDo) {
      const badge = document.createElement('span');
      badge.className = 'card-diag-icon do';
      badge.textContent = '🔴';
      badge.title = nodeDiags.filter(d => d.muc_do === 'do').map(d => d.thong_diep).join('\n');
      theEl.appendChild(badge);
    } else if (hasVang) {
      const badge = document.createElement('span');
      badge.className = 'card-diag-icon vang';
      badge.textContent = '🟡';
      badge.title = nodeDiags.filter(d => d.muc_do === 'vang').map(d => d.thong_diep).join('\n');
      theEl.appendChild(badge);
    }

    // Nội dung thẻ (tokens + inputs)
    const contentEl = renderCodeLineContent(node, cardDef);
    theEl.appendChild(contentEl);

    // Chú thích cuối dòng (duoi_dong) nếu có
    if (node.duoi_dong) {
      const ddEl = document.createElement('span');
      ddEl.className = 'cm duoi-dong-badge';
      ddEl.textContent = ` ${node.duoi_dong.trim()}`;
      ddEl.title = 'Chú thích cuối dòng';
      theEl.appendChild(ddEl);
    }

    hangEl.appendChild(theEl);

    // Controls hover
    const controlsEl = document.createElement('div');
    controlsEl.className = 'card-controls';

    if (index > 0) {
      const btnUp = document.createElement('button');
      btnUp.className = 'btn-card-tool';
      btnUp.textContent = '↑';
      btnUp.title = 'Di chuyển lên';
      btnUp.addEventListener('click', (e) => {
        e.stopPropagation();
        const tmp = parentList[index];
        parentList[index] = parentList[index - 1];
        parentList[index - 1] = tmp;
        onTreeChanged();
      });
      controlsEl.appendChild(btnUp);
    }

    if (index < parentList.length - 1) {
      const btnDown = document.createElement('button');
      btnDown.className = 'btn-card-tool';
      btnDown.textContent = '↓';
      btnDown.title = 'Di chuyển xuống';
      btnDown.addEventListener('click', (e) => {
        e.stopPropagation();
        const tmp = parentList[index];
        parentList[index] = parentList[index + 1];
        parentList[index + 1] = tmp;
        onTreeChanged();
      });
      controlsEl.appendChild(btnDown);
    }

    const btnDup = document.createElement('button');
    btnDup.className = 'btn-card-tool';
    btnDup.textContent = '📋';
    btnDup.title = 'Nhân bản thẻ này';
    btnDup.addEventListener('click', (e) => {
      e.stopPropagation();
      // 25/08: bản cũ chỉ đổi id thẻ NGOÀI CÙNG -> nhân bản một `for` có con
      // là cây có ngay hai thẻ trùng id. Xem chú thích ở `chepSauSinhIdMoi`.
      const clone = chepSauSinhIdMoi(node);
      parentList.splice(index + 1, 0, clone);
      onTreeChanged();
    });
    controlsEl.appendChild(btnDup);

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-card-tool delete';
    btnDel.textContent = '✕';
    btnDel.title = 'Xoá thẻ này';
    btnDel.addEventListener('click', (e) => {
      e.stopPropagation();
      parentList.splice(index, 1);
      onTreeChanged();
    });
    controlsEl.appendChild(btnDel);

    hangEl.appendChild(controlsEl);
    fragment.appendChild(hangEl);

    // 3. Khối con (.khoi) nếu thẻ có thân
    if (cardDef.co_than) {
      const khoiEl = document.createElement('div');
      khoiEl.className = 'khoi cuoi';
      khoiEl.dataset.slotId = node.id;

      if (node.than && node.than.length > 0) {
        renderCardList(node.than, khoiEl, depth + 1, node.id);
      } else {
        const ph = document.createElement('div');
        ph.className = 'slot-placeholder';
        ph.textContent = '+ Thả thẻ vào thân này...';
        khoiEl.appendChild(ph);
      }

      // Drag and drop vào slot
      khoiEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        khoiEl.style.outline = '1px dashed var(--color-chain-active)';
      });
      khoiEl.addEventListener('dragleave', (e) => {
        e.preventDefault();
        khoiEl.style.outline = 'none';
      });
      khoiEl.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        khoiEl.style.outline = 'none';
        const raw = e.dataTransfer.getData('text/plain');
        if (!raw) return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === 'NEW_CARD') {
            const newNode = taoTheNode(payload.ma, payload.customO);
            if (!node.than) node.than = [];
            node.than.push(newNode);
            onTreeChanged();
          } else if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
            // Thả vào NỀN của khối (không trúng dòng thẻ con nào) -> đưa
            // xuống CUỐI thân khối này. Thả trúng một dòng thẻ cụ thể thì
            // dragover/drop của chính dòng đó (ở trên) đã xử lý trước và
            // stopPropagation, nên nhánh này không chạy.
            if (!node.than) node.than = [];
            if (diChuyenThe(payload.nodeId, node.than, node.id, node.than.length)) {
              onTreeChanged();
            }
          }
        } catch (_) {}
      });

      fragment.appendChild(khoiEl);
    }

    return fragment;
  }

  function renderCardList(nodeList, parentContainer, depth = 1) {
    for (let i = 0; i < nodeList.length; i++) {
      const node = nodeList[i];
      const nodeFrag = renderCard(node, nodeList, i, depth);
      parentContainer.appendChild(nodeFrag);
    }
  }

  function renderCanvas() {
    const rootContainer = document.getElementById('cardChainRoot');
    const emptyGuide = document.getElementById('emptyCanvasGuide');
    if (!rootContainer) return;
    rootContainer.innerHTML = '';

    if (state.tree.length === 0) {
      if (emptyGuide) emptyGuide.style.display = 'flex';
    } else {
      if (emptyGuide) emptyGuide.style.display = 'none';
      renderCardList(state.tree, rootContainer, 1);
    }

    // Đo đạc và tinh chỉnh cột dọc ngay sau khi render xong (double rAF)
    yeuCauChinhCotDoc();

    // renderCanvas dựng lại TOÀN BỘ DOM thẻ, nên mọi class đánh dấu tìm kiếm
    // bay hết. Chạy lại phép tìm để dấu bám đúng thẻ sau khi sửa/hoàn tác —
    // không thì đang tìm mà sửa một ô là kết quả biến mất im lặng.
    if (timKiem.tuKhoa) {
      const idHienTai = timKiem.viTri >= 0 ? timKiem.danhSach[timKiem.viTri] : null;
      timKiem.danhSach = gomThePhuHop(state.tree, timKiem.tuKhoa, []);
      // Giữ nguyên kết quả đang xem nếu thẻ đó vẫn còn khớp; nếu nó vừa bị
      // sửa cho hết khớp (hoặc bị xoá) thì lùi về kết quả đầu.
      const viTriMoi = idHienTai ? timKiem.danhSach.indexOf(idHienTai) : -1;
      timKiem.viTri = viTriMoi >= 0 ? viTriMoi : (timKiem.danhSach.length ? 0 : -1);
      veKetQuaTimKiem(false);
    veDanhDauChon();
    }
  }

  // ==========================================================================
  // 4. KIỂM TRA TĨNH & CẬP NHẬT GIAO DIỆN (ĐỎ / VÀNG / ×N / CODE PREVIEW)
  // ==========================================================================
  let syncTimeout = null;

  // Trần 50 bước: cây thẻ của core/web_search.py là 281 thẻ, mỗi ảnh chụp
  // JSON.stringify tốn vài trăm KB — giữ vô hạn thì gõ một lúc là phình bộ
  // nhớ. 50 bước đủ cho thao tác sửa thật, và là trần CÓ THẬT chứ không phải
  // hứa suông.
  const TRAN_LICH_SU = 50;

  // Ảnh chụp SÂU. Cây thẻ lồng nhau qua `than`, nên sao chép nông sẽ khiến
  // "bản cũ" và "bản hiện tại" dùng chung mảng con — hoàn tác xong vẫn thấy
  // thay đổi, đúng loại lỗi im lặng khó tìm nhất.
  function anhChupCay() {
    return JSON.stringify(state.tree);
  }

  // Mở tệp khác / tải mẫu khác / xoá sạch: lịch sử của CÂY CŨ phải bỏ hẳn,
  // nếu không Ctrl+Z sẽ lôi ngược về cây của tệp trước đó — vừa vô nghĩa vừa
  // nguy hiểm (người dùng tưởng đang sửa tệp này, thực ra đang ghi đè bằng
  // nội dung tệp khác).
  function xoaLichSu() {
    state.history = [];
    state.historyIndex = -1;
    // Cập nhật nút NGAY: một số chỗ gọi xoaLichSu() SAU onTreeChanged(), nên
    // nếu không tự cập nhật ở đây thì nút Hoàn tác vẫn sáng dù lịch sử rỗng
    // — bấm vào không có gì xảy ra, đúng cái bệnh vừa sửa xong.
    capNhatNutLichSu();
  }

  function ghiLichSu() {
    const anh = anhChupCay();
    // Bỏ qua nếu cây không đổi thật — tránh Ctrl+Z phải bấm nhiều lần cho
    // một thao tác (vd. renderCanvas gọi lại onTreeChanged mà cây y nguyên).
    if (state.historyIndex >= 0 && state.history[state.historyIndex] === anh) return;
    // Đang ở giữa lịch sử mà sửa tiếp -> nhánh tương lai cũ bị bỏ, đúng như
    // mọi trình soạn thảo.
    state.history = state.history.slice(0, state.historyIndex + 1);
    state.history.push(anh);
    if (state.history.length > TRAN_LICH_SU) state.history.shift();
    state.historyIndex = state.history.length - 1;
    capNhatNutLichSu();
  }

  function capNhatNutLichSu() {
    const btnUndo = document.getElementById('btnUndo');
    const btnRedo = document.getElementById('btnRedo');
    if (btnUndo) btnUndo.disabled = state.historyIndex <= 0;
    if (btnRedo) btnRedo.disabled = state.historyIndex >= state.history.length - 1;
  }

  // `pushHistory = false`: khôi phục cây từ ảnh chụp thì KHÔNG được ghi lại
  // vào lịch sử, nếu không Ctrl+Z sẽ tự sinh ra một bước mới và không bao giờ
  // lùi được quá một bước.
  function apDungAnhChup(anh) {
    state.tree = JSON.parse(anh);
    onTreeChanged(false, true);
    capNhatNutLichSu();
  }

  function hoanTac() {
    if (state.historyIndex <= 0) return;
    state.historyIndex--;
    apDungAnhChup(state.history[state.historyIndex]);
  }

  function lamLai() {
    if (state.historyIndex >= state.history.length - 1) return;
    state.historyIndex++;
    apDungAnhChup(state.history[state.historyIndex]);
  }

  /** Vẽ lại thanh trạng thái đáy — thêm 26/08/2026.
   *
   * Gọi từ `onTreeChanged`, tức MỌI đường làm cây thẻ đổi đều đi qua đây:
   * thêm thẻ, xoá, dán, hoàn tác, chuyển tab, mở tệp, lưu tệp. Cắm vào một
   * chỗ thay vì rải lời gọi khắp nơi — rải ra thì sẽ có nhánh quên gọi, và
   * thanh trạng thái nói sai còn tệ hơn không có.
   */
  function veThanhTrangThai() {
    const dat = (id, chu, lop) => {
      const o = document.getElementById(id);
      if (!o) return;
      o.textContent = chu;
      o.className = 'status-muc' + (lop ? ' ' + lop : '');
    };
    dat('stDuAn', state.tenDuAn ? '\u{1F4C2} ' + state.tenDuAn : '\u{1F4C2} (chưa rõ dự án)');
    dat('stTep', state.activeFileName || 'Chưa đặt tên');
    dat('stLuu',
        state.hasModifications ? '\u25CF chưa lưu' : '\u2713 đã lưu',
        state.hasModifications ? 'chua-luu' : '');

    const soThe = demTheSau(state.tree || []);
    dat('stSoThe', soThe + ' thẻ');

    // `state.diagnostics` là ĐỐI TƯỢNG, không phải mảng:
    //   { hop_le · so_loi_do · so_canh_bao_vang · danh_sach · so_lan_dung_the }
    // Nó đã đếm sẵn, khỏi phải lọc.
    //
    // Tôi đoán sai tên trường HAI LẦN trong đúng hàm này, ngày 26/08:
    //   lần 1  lọc `d.muc_do === 'loi'`  — `validator.js` chỉ sinh 'do' và
    //          'vang', nên nó sẽ luôn báo "không lỗi", im lặng
    //   lần 2  gọi `.filter()` trên đối tượng — ném `filter is not a function`,
    //          làm hàm chết giữa chừng và HAI ô cuối của thanh trạng thái
    //          rỗng trắng
    //
    // Cả hai chỉ lộ ra khi TỰ BẤM THỬ. Không cửa nào bắt được, vì lỗi nằm ở
    // chỗ giao diện đọc dữ liệu — đúng họ bệnh hộp "Mở tệp" đọc
    // `data.tep_tin` trong khi backend trả `danh_sach` (CLAUDE.md §4).
    const cd = state.diagnostics || {};
    const soDo = cd.so_loi_do || 0;
    const soVang = cd.so_canh_bao_vang || 0;
    const chu = soDo ? soDo + ' lỗi' + (soVang ? ', ' + soVang + ' cảnh báo' : '')
              : soVang ? soVang + ' cảnh báo' : 'không lỗi';
    dat('stLoi', chu, soDo ? 'co-loi' : '');

    dat('stChay', state.codeExecutionEnabled ? 'Chạy mã: BẬT' : 'Chạy mã: TẮT');
  }

  /** Đếm CẢ thẻ con, không chỉ thẻ ở tầng ngoài cùng.
   *
   * `state.tree.length` chỉ đếm tầng một. Một chương trình có `def` bọc bốn
   * thẻ bên trong sẽ hiện "1 thẻ" — con số ấy nói sai. */
  function demTheSau(ds) {
    let n = 0;
    for (const t of ds || []) {
      n += 1;
      // `than` là ô chứa thẻ con DUY NHẤT — kiểm bằng cách đọc `BO_THE_V1`
      // trong `core/the_v1.py` (thuộc tính: co_than · ma · mau · nhom · o ·
      // ten). Bản nháp của tôi còn liệt kê `thanElse`, `body`,
      // `cac_the_con` — ba tên KHÔNG tồn tại, chép từ trí nhớ.
      if (Array.isArray(t.than)) n += demTheSau(t.than);
    }
    return n;
  }

  function onTreeChanged(pushHistory = true, markDirty = true) {
    if (pushHistory) ghiLichSu();
    if (markDirty) state.hasModifications = true;
    // Dấu • "chưa lưu" nằm trên tab, nên tab phải vẽ lại theo mỗi lần sửa.
    if (state.tabActive >= 0) {
      state.tabs[state.tabActive].hasModifications = state.hasModifications;
      veThanhTab();
    }
    document.getElementById('fileModifiedBadge').style.display =
      state.activeFilePath && state.hasModifications ? 'inline-block' : 'none';

    // 1. Chạy Client-side validator tức thì (0ms latency)
    state.diagnostics = TheValidator.kiemTraCayThe(state.tree);

    // 2. Cập nhật giao diện
    renderCanvas();
    updateToolboxCounters();
    veThanhTrangThai();
    kiemCauTrucDoi();
    updateCodePreview();
    updateDiagnosticsPanel();
    updateStatusBar();
    capNhatDaiNhip();
    capNhatKichBan();
    capNhatAiContextBanner();
    dongBoTheSangCodeEditor();

    // 3. Đảm bảo căn chỉnh cột dọc sau mọi thay đổi cây thẻ
    yeuCauChinhCotDoc();

    // 4. Đồng bộ với Backend API /api/kiem (Python làm trọng tài)
    clearTimeout(syncTimeout);
    syncTimeout = setTimeout(syncWithBackendValidator, 300);
  }


  async function syncWithBackendValidator() {
    try {
      const resp = await authFetch('/api/kiem', {
        method: 'POST',
        body: JSON.stringify({ tree: state.tree })
      });
      if (resp.ok) {
        const data = await resp.json();
        // Cập nhật kết quả trọng tài từ Python nếu có lệch
        state.diagnostics = data;
        updateDiagnosticsPanel();
        updateStatusBar();
        updateToolboxCounters();
        yeuCauChinhCotDoc();
      }
    } catch (err) {
      console.warn('Không thể kết nối /api/kiem:', err);
    }
  }

  function updateCodePreview() {
    // Tab "Mã Python" đã bỏ ở vòng ba cột 23/08 (cột giữa đã là mã rồi, không cần
    // hiện hai lần), nhưng hàm này vẫn ghi vào #pythonCodeOutput. Phần tử không
    // còn nên `codeEl` là null -> TypeError -> openPyFile nuốt vào catch rồi
    // alert("Lỗi kết nối khi mở tệp: Cannot set properties of null").
    //
    // Đo 24/08: trang mới tinh, mở tệp ĐẦU TIÊN là hộp lỗi hiện lên, dù tệp
    // MỞ ĐƯỢC (state.activeFilePath đã gán đúng). Và trong Chrome headless thì
    // `alert` chặn renderer, không ai đóng, nên cửa CDP treo quá 317 giây.
    const codeEl = document.getElementById('pythonCodeOutput');
    if (!codeEl) return;
    const code = TheValidator.sinhMaPython(state.tree);
    codeEl.textContent = code || '# (Chưa có lệnh nào trong chương trình)';
  }

  function updateStatusBar() {
    const dot = document.getElementById('overallStatusDot');
    const text = document.getElementById('overallStatusText');
    const doCount = state.diagnostics.so_loi_do;
    const vangCount = state.diagnostics.so_canh_bao_vang;

    if (doCount > 0) {
      dot.className = 'status-indicator do';
      text.textContent = `${doCount} Lỗi ĐỎ · ${vangCount} Cảnh báo VÀNG`;
      text.style.color = 'var(--color-error-do)';
    } else if (vangCount > 0) {
      dot.className = 'status-indicator vang';
      text.textContent = `Hợp lệ · ${vangCount} Cảnh báo VÀNG`;
      text.style.color = 'var(--color-warn-vang)';
    } else {
      dot.className = 'status-indicator';
      text.textContent = 'Hợp lệ · 0 Lỗi · 0 Cảnh báo';
      text.style.color = 'var(--text-secondary)';
    }
  }

  function updateDiagnosticsPanel() {
    const badgeCount = document.getElementById('diagBadge');
    const badgeDo = document.getElementById('badgeCountDo');
    const badgeVang = document.getElementById('badgeCountVang');
    const listEl = document.getElementById('diagList');

    const doCount = state.diagnostics.so_loi_do;
    const vangCount = state.diagnostics.so_canh_bao_vang;

    badgeCount.textContent = doCount + vangCount;
    badgeDo.textContent = `${doCount} ĐỎ (Lỗi)`;
    badgeVang.textContent = `${vangCount} VÀNG (Cảnh báo)`;

    listEl.innerHTML = '';

    if (state.diagnostics.danh_sach.length === 0) {
      listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 20px;">✓ Không phát hiện lỗi hoặc cảnh báo nào.</div>';
      return;
    }

    state.diagnostics.danh_sach.forEach(item => {
      const div = document.createElement('div');
      div.className = `diag-item ${item.muc_do}`;
      div.innerHTML = `
        <span>${item.muc_do === 'do' ? '🔴' : '🟡'}</span>
        <div>
          <strong>${item.thong_diep}</strong>
          ${item.line ? `<div style="font-size: 11px; opacity: 0.8;">Dòng ${item.line}</div>` : ''}
        </div>
      `;
      div.addEventListener('click', () => {
        if (item.node_id && item.node_id !== 'global') {
          const targetEl = document.getElementById(`node_${item.node_id}`);
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetEl.style.transition = 'transform 200ms';
            targetEl.style.transform = 'scale(1.02)';
            setTimeout(() => targetEl.style.transform = 'scale(1)', 400);
          }
        }
      });
      listEl.appendChild(div);
    });
  }

  // ==========================================================================
  // DẢI NHỊP THỰC THI (EXECUTION RHYTHMS — CẮT THEO DEF & NHỊP CHƯA ĐÓNG)
  // ==========================================================================
  const TANG_THE_MAP = {
    gan: 'K',
    pheptinh: 'B', neu: 'B', nguoc_lai: 'B', lap_moi: 'B', lap_khi: 'B',
    in_ra: 'X', tra_ve: 'X'
  };

  function capNhatDaiNhip() {
    const container = document.getElementById('rhythmPillsContainer');
    if (!container) return;
    container.innerHTML = '';

    if (!state.tree || state.tree.length === 0) {
      container.innerHTML = '<span class="rhythm-empty-hint">Chưa có hàm hoặc thẻ phân tầng...</span>';
      return;
    }

    // Tách các track theo từng hàm def hoặc module top-level
    const tracks = [];
    const moduleNodes = [];

    state.tree.forEach(node => {
      if (node.ma === 'ham') {
        const fnName = (node.o && node.o.ten_ham) ? String(node.o.ten_ham).trim() : 'hàm';
        tracks.push({
          tenTrack: `def ${fnName}()`,
          nodes: node.than || []
        });
      } else {
        moduleNodes.push(node);
      }
    });

    if (moduleNodes.length > 0) {
      tracks.unshift({
        tenTrack: 'Module',
        nodes: moduleNodes
      });
    }

    let tongSoNhip = 0;

    tracks.forEach(track => {
      const flatNodes = [];
      function di(ns) {
        ns.forEach(n => {
          flatNodes.push(n);
          if (n.than && n.than.length) di(n.than);
        });
      }
      di(track.nodes);

      const thePhanTang = flatNodes.filter(n => TANG_THE_MAP[n.ma]);
      if (thePhanTang.length === 0) return;

      const nhipList = [];
      let curNodes = [];
      let curStr = [];
      let soThuTu = 1;

      thePhanTang.forEach(the => {
        const k = TANG_THE_MAP[the.ma];
        curNodes.push(the);
        curStr.push(k);
        if (k === 'X') {
          const matCat = curStr.join('');
          const coKhuyetB = !matCat.includes('B') && matCat.includes('K');
          const coRong = !matCat.includes('B') && !matCat.includes('K');
          nhipList.push({
            soThuTu: soThuTu++,
            nodes: [...curNodes],
            matCat,
            coKhuyetB,
            coRong,
            chuaDong: false
          });
          curNodes = [];
          curStr = [];
        }
      });

      if (curNodes.length > 0) {
        const matCat = curStr.join('');
        nhipList.push({
          soThuTu: soThuTu++,
          nodes: [...curNodes],
          matCat,
          coKhuyetB: false,
          coRong: false,
          chuaDong: true
        });
      }

      if (nhipList.length > 0) {
        tongSoNhip += nhipList.length;

        const trackRow = document.createElement('div');
        trackRow.className = 'rhythm-track-row';

        const trackTitle = document.createElement('span');
        trackTitle.className = 'rhythm-track-title';
        trackTitle.textContent = track.tenTrack;
        trackRow.appendChild(trackTitle);

        const pillsContainer = document.createElement('div');
        pillsContainer.className = 'rhythm-pills';

        nhipList.forEach(nhip => {
          const pill = document.createElement('div');
          pill.className = `rhythm-pill ${nhip.chuaDong ? 'unclosed' : ''}`;
          pill.title = `${track.tenTrack} — Nhịp ${nhip.soThuTu} (Mặt cắt: ${nhip.matCat}${nhip.chuaDong ? ' · Chưa đóng' : ''}) — Click để chọn`;

          let badgeHtml = '';
          if (nhip.chuaDong) {
            badgeHtml = `<span class="rhythm-tag-badge unclosed">${nhip.matCat || 'K'} (Chưa đóng)</span>`;
          } else if (nhip.coRong) {
            badgeHtml = '<span class="rhythm-tag-badge empty">X (Rỗng)</span>';
          } else if (nhip.coKhuyetB) {
            badgeHtml = `<span class="rhythm-tag-badge khuyet">${nhip.matCat} (Khuyết B)</span>`;
          } else {
            badgeHtml = `<span class="rhythm-tag-badge ${nhip.matCat.toLowerCase().includes('k') ? 'k' : 'b'}">${nhip.matCat}</span>`;
          }

          pill.innerHTML = `<span>#${nhip.soThuTu}</span> ${badgeHtml}`;

          pill.addEventListener('click', () => {
            document.querySelectorAll('.rhythm-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            document.querySelectorAll('.card-block').forEach(c => c.style.outline = 'none');
            nhip.nodes.forEach(n => {
              const card = document.getElementById(`node_${n.id}`);
              if (card) {
                card.style.outline = '2px solid var(--color-bien-so)';
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              }
            });
          });

          pillsContainer.appendChild(pill);
        });

        trackRow.appendChild(pillsContainer);
        container.appendChild(trackRow);
      }
    });

    if (tongSoNhip === 0) {
      container.innerHTML = '<span class="rhythm-empty-hint">Chưa có thẻ phân tầng (Gán/Biến đổi/Kết xuất)...</span>';
    }
  }

  // ==========================================================================
  // MẠCH NƯỚC NGẦM BIẾN SỐ (RUNTIME TRACE)
  // ==========================================================================
  async function chayMachNuocNgam() {
    const btnTrace = document.getElementById('btnRunTrace');
    const statusPill = document.getElementById('traceStatusPill');
    const subInfo = document.getElementById('traceSubInfo');
    const testNameEl = document.getElementById('traceTestName');
    const noticeEl = document.getElementById('traceNotice');
    const timelineBody = document.getElementById('traceTimelineBody');
    const e1ResultsBody = document.getElementById('e1ResultsBody');

    if (!btnTrace || !statusPill || !timelineBody) return;

    if (!state.codeExecutionEnabled) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Chạy mã/test đang tắt';
      return;
    }

    // Chặn TRƯỚC khi gọi, bằng câu người dùng hiểu được. 24/08: bấm nút này
    // lúc chưa mở tệp thì server trả "403 Forbidden: Tệp nguồn chưa được mở
    // trong phiên làm việc" — và app in NGUYÊN VĂN mã lỗi HTTP đó lên màn
    // hình. Nút "Chạy thử" cạnh bên đã làm đúng từ lâu (câu tiếng Việt rõ
    // ràng khi có lỗi đỏ); nút này thì phun lỗi kỹ thuật.
    if (!state.activeFilePath) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Hãy mở một tệp .py trước khi dò vết';
      timelineBody.style.display = 'block';
      timelineBody.innerHTML = '<div class="trace-empty-hint">Dò dòng dữ liệu chạy trên một tệp .py có sẵn trong kho. Bấm "Mở Tệp" để chọn tệp, rồi chọn tệp test tương ứng ở ô bên dưới.</div>';
      return;
    }

    const testSelectTrace = document.getElementById('e1TestSelect');
    const tepTest = testSelectTrace && testSelectTrace.value ? testSelectTrace.value : '';
    if (!tepTest) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Hãy chọn tệp test ở ô bên dưới';
      timelineBody.style.display = 'block';
      timelineBody.innerHTML = '<div class="trace-empty-hint">Dò dòng dữ liệu cần một tệp test để biết chạy hàm nào. Chọn tệp test ở ô "Tệp test" ngay dưới đây.</div>';
      return;
    }

    btnTrace.disabled = true;
    statusPill.className = 'trace-status-pill ready';
    statusPill.textContent = 'Đang dò vết...';
    timelineBody.style.display = 'block';
    if (e1ResultsBody) e1ResultsBody.style.display = 'none';
    timelineBody.innerHTML = '<div class="trace-empty-hint">Đang thu thập chuỗi biến đổi dữ liệu thực thi (Trần 5000 bước)...</div>';

    try {
      // 24/08: dòng cũ là
      //   tep_test: state.activeFilePath.replace('core/', 'tests/test_')
      // — KHÔNG BAO GIỜ khớp, vì `activeFilePath` là đường dẫn tuyệt đối
      // Windows dùng dấu `\` (`D:\AURA_v3\core\dong_ho.py`), còn chuỗi tìm là
      // `core/` với dấu `/`. Đo thật: replace xong ra CHÍNH chuỗi cũ, nên
      // `tep_test` = đường dẫn tệp NGUỒN, server từ chối "Tệp test không hợp
      // lệ (phải nằm dưới tests/)". Nút này chưa từng chạy được, với mọi tệp.
      //
      // Dùng lại ĐÚNG nguồn mà E1 (dòng ~1464) đang dùng và chạy tốt: dropdown
      // `e1TestSelect` do người dùng chọn. Hai nút nằm cùng một khu vực, cùng
      // cần một tệp test — không có lý do gì để đoán riêng.
      const payload = {
        tep_nguon: state.activeFilePath,
        tep_test: tepTest,
        max_steps: 5000
      };

      const resp = await authFetch('/api/trace', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = errData.error || (resp.status === 403 ? 'Chạy mã/test đang tắt' : 'Không đo được');
        timelineBody.innerHTML = `<div class="trace-empty-hint" style="color: var(--color-error-do);">${escapeHtml(errData.error || 'Lỗi ' + resp.status)}</div>`;
        return;
      }

      const res = await resp.json();

      if (res.trang_thai === 'trace_du') {
        statusPill.className = 'trace-status-pill success';
        statusPill.textContent = `✓ ${res.thong_diep} (${res.thoi_gian_giay}s)`;
      } else if (res.trang_thai === 'trace_cut') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = `⚠️ ${res.thong_diep}`;
      } else if (res.trang_thai === 'trace_khong_qua_loi') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = `⚠️ ${res.thong_diep}`;
      } else {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = `❌ ${res.thong_diep || 'Không đo được'}`;
      }

      if (res.ten_test) {
        subInfo.style.display = 'flex';
        testNameEl.textContent = `Test: ${res.ten_test}`;
        if (res.trang_thai === 'trace_khong_qua_loi') {
          noticeEl.textContent = 'CẢNH BÁO: Vết thực thi của test này không đi qua dòng lỗi!';
        } else if (res.so_test_do_khac > 0) {
          noticeEl.textContent = `(Đang hiển thị test ít bước nhất; còn ${res.so_test_do_khac} test đỏ khác)`;
        } else {
          noticeEl.textContent = '';
        }
      } else {
        subInfo.style.display = 'none';
      }

      const events = res.cac_su_kien || [];
      if (events.length === 0) {
        timelineBody.innerHTML = '<div class="trace-empty-hint">Không có sự kiện biến đổi biến nào được ghi nhận.</div>';
        return;
      }

      timelineBody.innerHTML = '';
      events.forEach(ev => {
        const card = document.createElement('div');
        card.className = `trace-event-card ${ev.su_kien === 'tra_ve' ? 'return-event' : ''}`;
        card.innerHTML = `
          <div class="trace-event-header">
            <span class="trace-step-badge">Bước #${ev.buoc}</span>
            <span class="trace-line-badge">Dòng ${ev.dong}</span>
          </div>
          <div class="trace-event-body">
            <span class="trace-var-name">${escapeHtml(ev.ten_bien)}</span>
            <span class="trace-arrow">➔</span>
            ${ev.gia_tri_cu ? `<span class="trace-old-val">${escapeHtml(ev.gia_tri_cu)}</span>` : ''}
            <span class="trace-new-val">${escapeHtml(ev.gia_tri_moi)}</span>
          </div>
          ${ev.dong_ma ? `<div class="trace-code-snippet">${escapeHtml(ev.dong_ma)}</div>` : ''}
        `;
        timelineBody.appendChild(card);
      });

    } catch (err) {
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Lỗi kết nối /api/trace';
      timelineBody.innerHTML = `<div class="trace-empty-hint" style="color: var(--color-error-do);">Lỗi: ${escapeHtml(err.message)}</div>`;
    } finally {
      btnTrace.disabled = !state.codeExecutionEnabled;
    }
  }

  // ==========================================================================
  // E1 — ĐỊNH VỊ LỖI BẰNG TEST TRÊN BẢN SAO TẠM
  // ==========================================================================
  // 26/08/2026: hai lượt gọi từng đóng đinh `?thu_muc=tests`; dự án không có
  // thư mục ấy nhận HTTP 403 rồi cả hai nhánh đều im lặng, khiến ô test rỗng.
  // Lấy danh mục toàn dự án rồi lọc theo đúng quy ước pytest để tệp test ở gốc
  // hay trong bất kỳ thư mục được phép nào đều có cùng một đường đi.
  function laTepPytest(tep) {
    if (!tep || typeof tep.duong_dan !== 'string') return false;
    const cacPhan = tep.duong_dan.replaceAll('\\', '/').split('/');
    const tenTep = typeof tep.ten_tep === 'string' ? tep.ten_tep : cacPhan[cacPhan.length - 1];
    return (/^test_.*\.py$/.test(tenTep) || /_test\.py$/.test(tenTep));
  }

  async function layDanhSachTepPytest() {
    const resp = await authFetch('/api/tep_tin');
    const data = await readJsonSafely(resp);
    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status} khi tải danh sách tệp`);
    }
    if (!Array.isArray(data.danh_sach)) {
      throw new Error('Máy chủ không trả danh_sach tệp hợp lệ');
    }
    return data.danh_sach.filter(laTepPytest);
  }

  function baoDanhSachTestKhongDungDuoc(select, message, laLoi = true) {
    state.testFilesInventory = {};
    select.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = message;
    opt.disabled = true;
    opt.selected = true;
    select.appendChild(opt);

    const statusPill = document.getElementById('e1StatusPill');
    if (statusPill) {
      statusPill.className = `trace-status-pill ${laLoi ? 'error' : 'cut'}`;
      statusPill.textContent = message;
    }
  }

  async function loadAvailableTests(defaultTestPath = '') {
    const select = document.getElementById('e1TestSelect');
    if (!select) return;
    try {
      const tests = await layDanhSachTepPytest();
      state.testFilesInventory = {};
      select.innerHTML = '';

      if (tests.length === 0) {
        baoDanhSachTestKhongDungDuoc(
          select,
          'Không tìm thấy tệp pytest (test_*.py hoặc *_test.py)',
          false
        );
        return;
      }

      const tenMacDinh = defaultTestPath.replaceAll('\\', '/').split('/').pop();
      const testMacDinh = tests.find(t => t.duong_dan === defaultTestPath) ||
        tests.find(t => tenMacDinh && t.ten_tep === tenMacDinh);

      tests.forEach(t => {
        state.testFilesInventory[t.duong_dan] = t;
        const opt = document.createElement('option');
        opt.value = t.duong_dan;
        opt.textContent = t.duong_dan;
        if (testMacDinh && t.duong_dan === testMacDinh.duong_dan) {
          opt.selected = true;
        }
        select.appendChild(opt);
      });
    } catch (err) {
      baoDanhSachTestKhongDungDuoc(select, `Không tải được tệp test: ${err.message}`);
    }
  }

  function updateButtonsState() {
    const btnRun = document.getElementById('btnRun');
    const btnTrace = document.getElementById('btnRunTrace');
    const btnE1 = document.getElementById('btnRunE1');

    if (!state.codeExecutionEnabled) {
      if (btnRun) btnRun.disabled = true;
      if (btnTrace) btnTrace.disabled = true;
      if (btnE1) btnE1.disabled = true;
      return;
    }

    if (btnRun) btnRun.disabled = false;
    if (btnTrace) btnTrace.disabled = false;

    if (btnE1) {
      if (state.hasModifications) {
        btnE1.disabled = true;
        btnE1.title = 'Vui lòng lưu hoặc hoàn tác trước khi định vị lỗi';
      } else {
        btnE1.disabled = false;
        btnE1.title = 'Định vị lỗi E1 trên bản sao tạm';
      }
    }
  }

  async function chayDinhViLoiE1() {
    const btnE1 = document.getElementById('btnRunE1');
    const statusPill = document.getElementById('e1StatusPill');
    const e1ResultsBody = document.getElementById('e1ResultsBody');
    const traceTimelineBody = document.getElementById('traceTimelineBody');
    const testSelect = document.getElementById('e1TestSelect');

    if (!btnE1 || !statusPill || !e1ResultsBody) return;

    if (!state.codeExecutionEnabled) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Chạy mã/test đang tắt';
      return;
    }

    if (state.hasModifications) {
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Hãy lưu hoặc hoàn tác trước khi định vị';
      return;
    }

    if (!state.activeFilePath || !state.activeFileSha256) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Vui lòng mở một tệp .py';
      return;
    }

    const selectedTestFile = testSelect && testSelect.value ? testSelect.value : '';
    if (!selectedTestFile) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Chưa có tệp pytest để định vị lỗi';
      return;
    }

    let testSha = '';
    if (state.testFilesInventory && state.testFilesInventory[selectedTestFile]) {
      testSha = state.testFilesInventory[selectedTestFile].sha256 || '';
    }
    if (!testSha) {
      try {
        const tests = await layDanhSachTepPytest();
        state.testFilesInventory = {};
        tests.forEach(t => {
          state.testFilesInventory[t.duong_dan] = t;
        });
        const match = tests.find(t => t.duong_dan === selectedTestFile);
        if (match && match.sha256) {
          testSha = match.sha256;
        } else {
          statusPill.className = 'trace-status-pill error';
          statusPill.textContent = 'Tệp test không còn trong dự án';
          renderE1Error(`Không tìm thấy ${selectedTestFile} trong danh sách tệp pytest hiện tại.`);
          return;
        }
      } catch (err) {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = 'Không tải được danh sách test';
        renderE1Error(`Không thể lấy SHA-256 của tệp test: ${err.message}`);
        return;
      }
    }

    btnE1.disabled = true;
    statusPill.className = 'trace-status-pill ready';
    statusPill.textContent = 'Đang phân tích E1...';
    if (traceTimelineBody) traceTimelineBody.style.display = 'none';
    e1ResultsBody.style.display = 'block';

    const t0Client = performance.now();
    let stageInterval = null;

    const renderProgress = () => {
      const elapsedSec = (performance.now() - t0Client) / 1000;
      let stageText = 'Đang khởi tạo bản sao tạm...';
      if (elapsedSec >= 2.0 && elapsedSec < 8.0) {
        stageText = 'Đang tìm test đỏ và truy vết dòng chạy...';
      } else if (elapsedSec >= 8.0) {
        stageText = 'Đang lọc ứng viên AST và kiểm thử toàn bộ suite...';
      }
      e1ResultsBody.innerHTML = `
        <div class="trace-empty-hint" style="text-align: left; padding: 16px;">
          <div style="font-weight: 600; margin-bottom: 8px; color: var(--color-brand);">⏳ Tiến trình định vị lỗi E1 (${elapsedSec.toFixed(1)}s):</div>
          <div style="margin-left: 12px; line-height: 1.6;">
            <div>${elapsedSec >= 0 ? '✓' : '○'} 1. Kiểm tra ràng buộc và chuẩn bị phiên</div>
            <div>${elapsedSec >= 2.0 ? '✓' : '○'} 2. Nhân bản cô lập & Thu vết dòng trên test đỏ</div>
            <div>${elapsedSec >= 8.0 ? '⏳' : '○'} 3. Lọc 5 họ phép AST & Chạy kiểm thử hồi quy toàn bộ suite</div>
          </div>
          <div style="margin-top: 10px; font-style: italic; color: var(--text-muted);">${stageText}</div>
        </div>
      `;
    };

    renderProgress();
    stageInterval = setInterval(renderProgress, 500);

    try {
      const payload = {
        tep_nguon: state.activeFilePath,
        tep_test: selectedTestFile,
        source_sha256: state.activeFileSha256,
        test_sha256: testSha
      };

      const resp = await authFetch('/api/dinh_vi_loi', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (stageInterval) {
        clearInterval(stageInterval);
        stageInterval = null;
      }

      const elapsedTotalSec = Math.round((performance.now() - t0Client) / 100) / 10;

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        statusPill.className = 'trace-status-pill error';
        if (resp.status === 409) {
          statusPill.textContent = errData.trang_thai === 'busy' ? 'BUSY' : 'SHA trôi (409)';
        } else if (resp.status === 403) {
          statusPill.textContent = 'Chạy mã/test đang tắt';
        } else if (resp.status === 504) {
          statusPill.textContent = 'TIMEOUT/KHÔNG ĐO ĐƯỢC';
        } else {
          statusPill.textContent = `Lỗi ${resp.status}`;
        }
        renderE1Error(errData.error || `HTTP ${resp.status}`);
        return;
      }

      const res = await resp.json();
      renderE1Results(res, null, elapsedTotalSec);

    } catch (err) {
      if (stageInterval) {
        clearInterval(stageInterval);
        stageInterval = null;
      }
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Lỗi kết nối /api/dinh_vi_loi';
      renderE1Error(err.message);
    } finally {
      if (stageInterval) {
        clearInterval(stageInterval);
      }
      btnE1.disabled = !state.codeExecutionEnabled;
    }
  }

  function renderE1Results(res, targetEl, elapsedTotalSec) {
    const statusPill = document.getElementById('e1StatusPill');
    const e1ResultsBody = targetEl || document.getElementById('e1ResultsBody');
    if (!e1ResultsBody) return;

    if (statusPill) {
      if (res.trang_thai === 'tim_thay') {
        statusPill.className = 'trace-status-pill success';
        statusPill.textContent = 'TÌM THẤY';
      } else if (res.trang_thai === 'suite_khong_do_duoc') {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = 'SUITE KHÔNG ĐO ĐƯỢC';
      } else if (res.trang_thai === 'ung_vien_khong_qua_suite') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = 'ỨNG VIÊN KHÔNG QUA TOÀN BỘ TEST';
      } else if (res.trang_thai === 'khong_tim_thay') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = 'KHÔNG TÌM THẤY';
      } else {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = 'TIMEOUT/KHÔNG ĐO ĐƯỢC';
      }
    }

    e1ResultsBody.innerHTML = '';

    // 1. Notice: Phân tích trên bản sao
    const noticeTemp = document.createElement('div');
    noticeTemp.className = 'e1-notice-box e1-notice-temp';
    noticeTemp.textContent = '🛡️ Phân tích trên bản sao; tệp thật chưa đổi.';
    e1ResultsBody.appendChild(noticeTemp);

    // 2. Summary Card
    const summaryCard = document.createElement('div');
    summaryCard.className = 'e1-summary-card';

    const titleRow = document.createElement('div');
    titleRow.className = 'e1-summary-title';
    titleRow.innerHTML = `<span>Bằng Chứng Định Vị E1</span>`;
    const badgeState = document.createElement('span');
    if (res.trang_thai === 'tim_thay') {
      badgeState.className = 'e1-badge badge-green';
      badgeState.textContent = 'TÌM THẤY';
    } else if (res.trang_thai === 'suite_khong_do_duoc') {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = 'SUITE KHÔNG ĐO ĐƯỢC';
    } else if (res.trang_thai === 'ung_vien_khong_qua_suite') {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = 'ỨNG VIÊN KHÔNG QUA SUITE';
    } else {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = (res.trang_thai || '').toUpperCase();
    }
    titleRow.appendChild(badgeState);
    summaryCard.appendChild(titleRow);

    const metaList = document.createElement('div');
    metaList.className = 'e1-meta-row';

    function addMetaItem(label, val) {
      const item = document.createElement('div');
      item.className = 'e1-meta-item';
      const l = document.createElement('span');
      l.className = 'e1-meta-label';
      l.textContent = label + ':';
      const v = document.createElement('span');
      v.textContent = val;
      item.appendChild(l);
      item.appendChild(v);
      metaList.appendChild(item);
    }

    addMetaItem('Tệp nguồn', res.source_path || 'Chưa chọn');
    addMetaItem('Tệp test', res.test_file || 'Chưa chọn');
    if (res.selected_test) {
      addMetaItem('Test chọn', res.selected_test);
    }
    if (res.other_red_test_count !== undefined) {
      addMetaItem('Test đỏ khác', String(res.other_red_test_count));
    }
    if (res.candidate_count_before !== undefined && res.candidate_count_after !== undefined) {
      addMetaItem('Ứng viên lọc', `${res.candidate_count_before} → ${res.candidate_count_after}`);
    }
    if (res.elapsed_filter_mutate_s !== undefined) {
      addMetaItem('Thời gian lọc+lật', `${res.elapsed_filter_mutate_s}s`);
    }
    if (res.elapsed_full_suite_s !== undefined) {
      addMetaItem('Thời gian full suite', `${res.elapsed_full_suite_s}s`);
    }
    if (elapsedTotalSec !== undefined) {
      addMetaItem('Tổng thời gian E1', `${elapsedTotalSec.toFixed(2)}s`);
    }

    summaryCard.appendChild(metaList);

    // Giải thích cho ca ung_vien_khong_qua_suite
    if (res.trang_thai === 'ung_vien_khong_qua_suite') {
      const noticeRejected = document.createElement('div');
      noticeRejected.className = 'e1-notice-box e1-notice-rejected';
      noticeRejected.style.marginTop = '10px';
      noticeRejected.innerHTML = `
        <strong>Giải thích:</strong> Các ứng viên dưới đây sửa được đúng bài test chọn nhưng làm gãy các bài test khác trong hệ thống.
        <em>"Sửa một chỗ mà hỏng chỗ khác thì không phải sửa."</em> Hệ thống <strong>KHÔNG đề nghị áp dụng</strong> các bản vá này.
      `;
      summaryCard.appendChild(noticeRejected);
    }

    if (res.reason) {
      const reasonDiv = document.createElement('div');
      reasonDiv.style.marginTop = '8px';
      reasonDiv.style.fontSize = '12px';
      reasonDiv.style.color = 'var(--text-secondary)';
      reasonDiv.textContent = 'Lý do: ' + res.reason;
      summaryCard.appendChild(reasonDiv);
    }

    e1ResultsBody.appendChild(summaryCard);

    // 3. Danh sách ứng viên
    const candidates = res.candidates || [];
    if (candidates.length > 0) {
      const candTitle = document.createElement('div');
      candTitle.className = 'e1-summary-title';
      candTitle.style.marginTop = '16px';
      if (res.trang_thai === 'ung_vien_khong_qua_suite') {
        candTitle.textContent = `Danh Sách Ứng Viên Bị Loại (${candidates.length})`;
      } else {
        candTitle.textContent = `Danh Sách Ứng Viên (${candidates.length})`;
      }
      e1ResultsBody.appendChild(candTitle);

      candidates.forEach((cand, idx) => {
        const card = document.createElement('div');
        card.className = 'e1-candidate-card';

        const h = document.createElement('div');
        h.className = 'e1-candidate-header';

        const titleSpan = document.createElement('span');
        titleSpan.textContent = `Ứng viên #${cand.index !== undefined ? cand.index : idx + 1} (Dòng ${cand.line}): ${cand.operation}`;
        h.appendChild(titleSpan);

        const statusGroup = document.createElement('div');
        statusGroup.style.display = 'flex';
        statusGroup.style.gap = '6px';

        const testBadge = document.createElement('span');
        testBadge.className = `e1-badge ${cand.selected_test_status === 'XANH' ? 'badge-green' : 'badge-red'}`;
        testBadge.textContent = `Test chọn: ${cand.selected_test_status}`;
        statusGroup.appendChild(testBadge);

        const suiteBadge = document.createElement('span');
        if (cand.full_suite_status === 'XANH') {
          suiteBadge.className = 'e1-badge badge-green';
          suiteBadge.textContent = 'Suite: XANH';
        } else if (cand.full_suite_status === 'suite_khong_do_duoc') {
          suiteBadge.className = 'e1-badge badge-red';
          const lyDo = cand.ly_do_suite ? ` (${cand.ly_do_suite})` : '';
          suiteBadge.textContent = `Suite: không đo được${lyDo}`;
        } else {
          const soTest = cand.so_test_hong || (res.other_red_test_count ? res.other_red_test_count + 1 : 1);
          suiteBadge.className = 'e1-badge badge-red';
          suiteBadge.textContent = `Suite: ĐỎ (${soTest} test khác hỏng)`;
        }
        statusGroup.appendChild(suiteBadge);

        h.appendChild(statusGroup);
        card.appendChild(h);

        if (cand.unified_diff) {
          const diffPre = document.createElement('pre');
          diffPre.className = 'e1-diff-container';
          const diffLines = cand.unified_diff.split('\n');
          diffLines.forEach(line => {
            const lineSpan = document.createElement('div');
            if (line.startsWith('+') && !line.startsWith('+++')) {
              lineSpan.className = 'e1-diff-add';
            } else if (line.startsWith('-') && !line.startsWith('---')) {
              lineSpan.className = 'e1-diff-del';
            }
            lineSpan.textContent = line;
            diffPre.appendChild(lineSpan);
          });
          card.appendChild(diffPre);
        }

        e1ResultsBody.appendChild(card);
      });
    }

    // 4. Limitation notice
    const noticeLimit = document.createElement('div');
    noticeLimit.className = 'e1-notice-box e1-notice-limit';
    noticeLimit.textContent = res.limitation || state.e1Limitation || 'Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.';
    e1ResultsBody.appendChild(noticeLimit);
  }

  function renderE1Error(msg, targetEl) {
    const e1ResultsBody = targetEl || document.getElementById('e1ResultsBody');
    if (!e1ResultsBody) return;
    e1ResultsBody.innerHTML = `
      <div class="trace-empty-hint" style="color: var(--color-error-do);">
        Lỗi định vị E1: ${escapeHtml(msg)}
      </div>
    `;
  }

  // ==========================================================================
  // TAB KỊCH BẢN LOGIC (NARRATIVE)
  // ==========================================================================
  function capNhatKichBan() {
    const narrativeBody = document.getElementById('narrativeContent');
    if (!narrativeBody) return;

    if (state.tree.length === 0) {
      narrativeBody.innerHTML = '<div style="color: var(--text-muted); font-style: italic;">Chưa có khối lệnh nào để tạo kịch bản logic.</div>';
      return;
    }

    narrativeBody.innerHTML = '';
    let stepNum = 1;

    function duyetNarrative(nodes, indent = '') {
      nodes.forEach(node => {
        const step = document.createElement('div');
        step.className = 'narrative-step';
        let desc = '';

        if (node.ma === 'ham') {
          desc = `Định nghĩa hàm <code>${escapeHtml(node.o.ten_ham || 'chưa đặt tên')}</code> nhận tham số (<code>${escapeHtml(node.o.tham_so || 'không có')}</code>).`;
        } else if (node.ma === 'gan') {
          desc = `Gán giá trị <code>${escapeHtml(node.o.gia_tri || '')}</code> cho biến <strong>${escapeHtml(node.o.ten_bien || '')}</strong>.`;
        } else if (node.ma === 'pheptinh') {
          desc = `Thực hiện phép tính <code>${escapeHtml(node.o.bieu_thuc || '')}</code> và lưu vào <strong>${escapeHtml(node.o.ten_bien || '')}</strong>.`;
        } else if (node.ma === 'neu') {
          desc = `Kiểm tra điều kiện: Nếu <code>${escapeHtml(node.o.dieu_kien || '')}</code> thoả mãn thì thực hiện khối lệnh con.`;
        } else if (node.ma === 'nguoc_lai') {
          desc = `Trường hợp ngược lại: Thực hiện các lệnh khi điều kiện "Nếu" phía trước sai.`;
        } else if (node.ma === 'lap_moi') {
          desc = `Lặp qua từng phần tử <strong>${escapeHtml(node.o.bien || '')}</strong> trong dãy <code>${escapeHtml(node.o.day || '')}</code>.`;
        } else if (node.ma === 'lap_khi') {
          desc = `Lặp liên tục chừng nào điều kiện <code>${escapeHtml(node.o.dieu_kien || '')}</code> còn đúng.`;
        } else if (node.ma === 'in_ra') {
          desc = `Xuất nội dung <code>${escapeHtml(node.o.noi_dung || '')}</code> ra màn hình terminal.`;
        } else if (node.ma === 'tra_ve') {
          desc = `Trả về kết quả <code>${escapeHtml(node.o.gia_tri || '')}</code> cho nơi gọi hàm.`;
        } else {
          desc = `Thực thi khối lệnh <code>${escapeHtml(node.ma)}</code>.`;
        }

        step.innerHTML = `
          <div class="narrative-step-title">${indent}Bước ${stepNum++}: ${escapeHtml(TheValidator.BO_THE_V1[node.ma]?.ten || node.ma)}</div>
          <div>${desc}</div>
        `;
        narrativeBody.appendChild(step);

        if (node.than && node.than.length) {
          duyetNarrative(node.than, indent + '↳ ');
        }
      });
    }

    duyetNarrative(state.tree);
  }

  // ==========================================================================
  // 5. CHẠY THỬ CÓ CHỦ ĐÍCH (TẮT MẶC ĐỊNH VÌ CHƯA PHẢI SANDBOX THẬT)
  // ==========================================================================

  // ==========================================================================
  // ==========================================================================
  // CHÉP / CẮT / DÁN THẺ (Ctrl+C · Ctrl+X · Ctrl+V)
  // ==========================================================================
  //
  // Trước 25/08 app không có khái niệm "thẻ đang chọn", nên phải dựng thêm.
  // Chọn bằng cách bấm vào DÒNG thẻ; bấm vào ô nhập hay nút thì không chọn —
  // người dùng đang gõ chứ không đang chọn.

  const bangGhiThe = { node: null };     // bảng ghi tạm, chỉ trong phiên này

  /**
   * Chép sâu một thẻ và SINH ID MỚI CHO CẢ CÂY CON.
   *
   * ĐÂY LÀ CHỖ NÚT "NHÂN BẢN" ĐÃ SAI TỪ TRƯỚC 25/08. Bản cũ chỉ đổi id của
   * thẻ ngoài cùng:
   *
   *     const clone = JSON.parse(JSON.stringify(node));
   *     clone.id = `the_${node.ma}_${++state.nodeIdCounter}`;   // chỉ MỘT id
   *
   * Nhân bản một `for` có hai thẻ con thì cây có NGAY hai `in_1` và hai
   * `gan_1`. Đo hậu quả thật ngày 25/08, tái hiện được:
   *
   *   - tìm "chao" ra 2 kết quả, nhảy sang kết quả 2/2 (bản SAO), bấm "Thay"
   *   - `timTheTheoId` tra theo id nên trả về thẻ ĐẦU TIÊN
   *   - bản GỐC bị sửa thành "XIN_CHAO", bản SAO giữ nguyên "chao"
   *
   * Người dùng nhìn thấy con trỏ ở bản sao, sửa xong thì bản gốc đổi. Không
   * lỗi, không báo gì. Cùng họ với "giao diện hứa một việc, mã làm việc khác"
   * ở §4.
   *
   * Mọi đường tra theo id đều dính: `timTheTheoId`, `layVaXoaTheTheoId`,
   * đánh dấu kết quả tìm, và bản đồ dòng lỗi runtime về thẻ.
   */
  function chepSauSinhIdMoi(node) {
    const ban = JSON.parse(JSON.stringify(node));
    (function danhSoLai(n) {
      state.nodeIdCounter++;
      n.id = `the_${n.ma}_${state.nodeIdCounter}`;
      n.da_sua = true;
      (n.than || []).forEach(danhSoLai);
    })(ban);
    return ban;
  }

  function xoaDanhDauChon() {
    document.querySelectorAll('.the.dang-chon')
      .forEach(el => el.classList.remove('dang-chon'));
  }

  function veDanhDauChon() {
    xoaDanhDauChon();
    if (!state.selectedNodeId) return;
    const el = document.querySelector('#node_' + state.selectedNodeId + ' .the');
    if (el) el.classList.add('dang-chon');
  }

  function chonThe(nodeId) {
    state.selectedNodeId = nodeId || null;
    veDanhDauChon();
  }

  function chepThe() {
    if (!state.selectedNodeId) return false;
    const boc = timTheTheoId(state.tree, state.selectedNodeId);
    if (!boc || !boc.node) return false;
    // Chép NGAY lúc bấm, không giữ tham chiếu: người dùng sửa tiếp thẻ gốc
    // rồi mới dán thì phải ra bản LÚC CHÉP, đúng như mọi trình soạn thảo.
    bangGhiThe.node = JSON.parse(JSON.stringify(boc.node));
    return true;
  }

  function catThe() {
    if (!chepThe()) return false;
    const boc = timTheTheoId(state.tree, state.selectedNodeId);
    if (!boc) return false;
    boc.dsCha.splice(boc.chiSo, 1);
    state.selectedNodeId = null;
    onTreeChanged();
    return true;
  }

  function danThe() {
    if (!bangGhiThe.node) return false;
    const ban = chepSauSinhIdMoi(bangGhiThe.node);
    if (state.selectedNodeId) {
      const boc = timTheTheoId(state.tree, state.selectedNodeId);
      if (boc) {
        // Dán NGAY SAU thẻ đang chọn, cùng cấp với nó — kể cả khi thẻ ấy
        // nằm trong thân một khối.
        boc.dsCha.splice(boc.chiSo + 1, 0, ban);
      } else {
        state.tree.push(ban);
      }
    } else {
      state.tree.push(ban);
    }
    onTreeChanged();                 // một lần dán = một bước hoàn tác
    chonThe(ban.id);                 // chọn bản vừa dán, dán tiếp thì nối tiếp
    return true;
  }

  // ==========================================================================
  // ==========================================================================
  // ==========================================================================
  // NHIỀU TAB TỆP
  // ==========================================================================
  //
  // THIẾT KẾ: `state.tree` / `state.activeFilePath` / `state.history`... VẪN
  // là trạng thái của tab ĐANG MỞ. Mảng `state.tabs` chỉ giữ ảnh chụp của các
  // tab kia. Chuyển tab = chụp trạng thái sống vào tab cũ, nạp tab mới ra.
  //
  // Vì sao không tách hẳn ra một lớp "tệp": hơn hai chục chỗ trong tệp này
  // đang đọc thẳng `state.activeFilePath`, `state.tree`, `state.history`
  // (E1, dò dòng dữ liệu, lưu tệp, hoàn tác, tìm kiếm). Đổi hết là hai chục
  // chỗ có thể sai; giữ nguyên thì không chỗ nào phải đổi.
  //
  // MỖI TAB GIỮ LỊCH SỬ RIÊNG. Dùng chung một lịch sử thì Ctrl+Z ở tab A lùi
  // được sang trạng thái của tab B — không giải thích được cho ai.

  function anhTabHienTai() {
    return {
      duong_dan: state.activeFilePath,
      ten_tep: state.activeFileName || 'Chưa đặt tên',
      tree: state.tree,
      sha256: state.activeFileSha256,
      hasModifications: state.hasModifications,
      history: state.history,
      historyIndex: state.historyIndex,
      selectedNodeId: state.selectedNodeId
    };
  }

  function dongBoTabHienTai() {
    if (state.tabActive < 0 || state.tabActive >= state.tabs.length) return;
    state.tabs[state.tabActive] = anhTabHienTai();
  }

  function napTab(i) {
    if (i < 0 || i >= state.tabs.length) return;
    const t = state.tabs[i];
    state.tabActive = i;
    state.tree = t.tree;
    state.activeFilePath = t.duong_dan;
    state.activeFileName = t.ten_tep;
    state.activeFileSha256 = t.sha256;
    state.hasModifications = t.hasModifications;
    state.history = t.history;
    state.historyIndex = t.historyIndex;
    state.selectedNodeId = t.selectedNodeId || null;

    const oTen = document.getElementById('currentFileName');
    if (oTen) oTen.textContent = t.ten_tep;
    // `pushHistory=false, markDirty=false`: chuyển tab KHÔNG phải một lần sửa.
    onTreeChanged(false, false);
    veThanhTab();
  }

  function chuyenTab(i) {
    if (i === state.tabActive) return;
    dongBoTabHienTai();
    napTab(i);
  }

  /** Tab đang mở tệp này rồi thì trả chỉ số, chưa thì -1. */
  function timTabTheoDuongDan(duongDan) {
    return state.tabs.findIndex(t => t.duong_dan && t.duong_dan === duongDan);
  }

  function dongTab(i) {
    if (i < 0 || i >= state.tabs.length) return;
    const t = state.tabs[i];
    if (t.hasModifications) {
      const ok = window.confirm(
        `"${t.ten_tep}" có thay đổi chưa lưu. Đóng và bỏ thay đổi?`);
      if (!ok) return;
    }
    state.tabs.splice(i, 1);
    if (state.tabs.length === 0) {
      // Đóng tab cuối -> về trạng thái nháp, KHÔNG để màn hình trống trơn.
      state.tabs.push({
        duong_dan: '', ten_tep: 'Chưa đặt tên', tree: [], sha256: null,
        hasModifications: false, history: [], historyIndex: -1,
        selectedNodeId: null
      });
      napTab(0);
      xoaLichSu();
      return;
    }
    napTab(Math.min(i, state.tabs.length - 1));
  }

  /** Mở tệp: đã có tab thì chuyển sang, chưa có thì thêm tab mới. */
  function moTrongTab(duLieu) {
    const cu = timTabTheoDuongDan(duLieu.duong_dan);
    if (cu !== -1) {
      // Đã mở rồi thì CHUYỂN SANG chứ không mở thêm bản thứ hai — hai tab
      // cùng một tệp là hai cây thẻ khác nhau ghi đè lẫn nhau lúc lưu.
      dongBoTabHienTai();
      napTab(cu);
      return;
    }
    dongBoTabHienTai();
    state.tabs.push({
      duong_dan: duLieu.duong_dan,
      ten_tep: duLieu.ten_tep,
      tree: duLieu.tree,
      sha256: duLieu.sha256,
      hasModifications: false,
      history: [], historyIndex: -1,
      selectedNodeId: null
    });
    napTab(state.tabs.length - 1);
  }

  function veThanhTab() {
    const thanh = document.getElementById('tabBar');
    if (!thanh) return;
    thanh.innerHTML = '';
    // 26/08: TRƯỚC ĐÂY ẨN THANH KHI CÓ MỘT TAB, lý do cũ "đỡ chiếm một dòng
    // màn hình cho không". Đổi vì hai chuyện đo được:
    //
    //   1. Mở tệp thứ hai thì thanh HIỆN RA và đẩy cả layout xuống — vùng
    //      soạn thảo nhảy đúng lúc người dùng đang nhìn vào nó.
    //   2. Có một tệp thì không chỗ nào trên màn hình nói đang sửa tệp nào và
    //      đã lưu chưa. Thanh tab chính là chỗ ấy: nó mang cả tên tệp lẫn dấu
    //      chấm "chưa lưu".
    //
    // Mọi trình soạn thảo đều giữ thanh tab kể cả khi mở một tệp.
    thanh.style.display = state.tabs.length === 0 ? 'none' : 'flex';

    state.tabs.forEach((t, i) => {
      const el = document.createElement('div');
      el.className = 'tab-item' + (i === state.tabActive ? ' dang-mo' : '');
      el.dataset.tabIndex = String(i);
      el.title = t.duong_dan || 'Chưa lưu ra tệp';

      const ten = document.createElement('span');
      ten.className = 'tab-ten';
      ten.textContent = t.ten_tep + (t.hasModifications ? ' •' : '');
      el.appendChild(ten);

      const x = document.createElement('button');
      x.className = 'tab-dong';
      x.textContent = '✕';
      x.title = 'Đóng tab';
      x.addEventListener('click', (e) => { e.stopPropagation(); dongTab(i); });
      el.appendChild(x);

      el.addEventListener('click', () => chuyenTab(i));
      thanh.appendChild(el);
    });
  }

  // ==========================================================================
  // NHẢY TỚI ĐỊNH NGHĨA (Ctrl+Bấm vào một tên · F12 trên thẻ đang chọn)
  // ==========================================================================
  //
  // Trong cây thẻ, "định nghĩa" của một cái tên là thẻ KHAI ra nó. Sáu chỗ
  // khai tên trong khay hiện tại — đọc từ `BO_THE_V1`, không chép tay:
  //
  //     ham       ten_ham              def f(...)
  //     gan       ten_bien             x = ...
  //     lap_moi   bien                 for i in ...
  //     bat_loi   ten_bien             except E as e
  //     nhap      phan / ten_khac      from m import a  ·  import m as a
  //     nhap      thu_vien             import m
  //
  // `goi_ham` KHÔNG khai tên — nó dùng tên. Đó chính là chỗ hay bấm nhất.

  /** Tên nào được thẻ này khai ra? Trả mảng (một thẻ có thể khai nhiều tên). */
  function tenDuocKhaiBoi(node) {
    const o = node.o || {};
    const lay = (k) => String(o[k] || '').trim();
    switch (node.ma) {
      case 'ham': return [lay('ten_ham')].filter(Boolean);
      case 'gan': return [lay('ten_bien')].filter(Boolean);
      case 'bat_loi': return [lay('ten_bien')].filter(Boolean);
      case 'lap_moi':
        // `for a, b in ...` khai HAI tên. Tách như validator vẫn tách.
        return (lay('bien').match(new RegExp(`(?<![\\p{L}\\p{N}\\p{M}_])[\\p{L}_][\\p{L}\\p{N}\\p{M}_]*`, 'gu')) || []);
      case 'nhap': {
        const ph = lay('phan'), tk = lay('ten_khac'), tv = lay('thu_vien');
        if (ph) {
          const motTen = !ph.includes(',');
          if (tk && motTen) return [tk];
          return ph.split(',').map(x => x.trim()).filter(Boolean);
        }
        if (tk) return [tk];
        // `import a.b.c` chỉ đưa tên `a` vào tầm nhìn.
        return tv ? [tv.split('.')[0].trim()].filter(Boolean) : [];
      }
      default: return [];
    }
  }

  /**
   * Thẻ nào khai ra `ten`? Trả thẻ ĐẦU TIÊN theo thứ tự đọc.
   *
   * Đầu tiên chứ không phải gần nhất: cây thẻ không có phạm vi thật (một hàm
   * và mã ngoài hàm cùng nằm trong một danh sách), nên "gần nhất" sẽ phải
   * đoán phạm vi — mà đoán sai thì nhảy tới chỗ không liên quan, tệ hơn là
   * không nhảy. Chỗ khai đầu tiên luôn giải thích được: đó là nơi cái tên
   * xuất hiện lần đầu.
   */
  function timDinhNghia(ten, danhSach) {
    if (!ten) return null;
    for (const node of (danhSach || state.tree)) {
      if (tenDuocKhaiBoi(node).includes(ten)) return node;
      if (node.than && node.than.length) {
        const sau = timDinhNghia(ten, node.than);
        if (sau) return sau;
      }
    }
    return null;
  }

  /** Lấy chữ nằm dưới con trỏ trong một ô nhập. */
  function tuDuoiConTro(input) {
    const v = String(input.value || '');
    let i = input.selectionStart;
    if (i === null || i === undefined) i = v.length;
    if (i > 0 && !/[\w]/.test(v[i]) && /[\w]/.test(v[i - 1])) i -= 1;
    if (!/[\w]/.test(v[i] || '')) return '';
    let d = i, c = i;
    while (d > 0 && /[\w]/.test(v[d - 1])) d--;
    while (c < v.length - 1 && /[\w]/.test(v[c + 1])) c++;
    return v.slice(d, c + 1);
  }

  let hetGioBao = null;

  /** Báo một câu ngắn cho người dùng, KHÔNG chặn màn hình.
   *
   * Thêm 26/08/2026, thay cho `alert()`.
   *
   * Trước hôm nay app dùng `alert()` ở 6 chỗ, và một trong đó là
   * `alert('Lưu tệp thành công!')` — bật lên MỖI LẦN LƯU. Người dùng bấm
   * Ctrl+S theo phản xạ rồi phải bấm tiếp OK để làm việc tiếp; lưu mười lần
   * là mười lần bị chặn. VS Code không nói gì khi lưu được — dấu chấm "chưa
   * lưu" tắt đi là đủ, và nay thanh trạng thái đáy đã làm việc ấy.
   *
   * Năm chỗ còn lại là báo lỗi. `alert()` trông giống hộp cảnh báo của trình
   * duyệt hơn là của app, chặn cả trang, và mất sạch khi bấm OK — người dùng
   * không đọc kịp thì không xem lại được.
   *
   * `loai`:  '' bình thường (tự mờ sau 3 giây)
   *          'hong' hỏng việc — đỏ, ở lại 8 giây vì người ta cần đọc kỹ hơn
   */
  function baoNhanh(chu, loai = '') {
    const o = document.getElementById('nhanNhanh');
    if (!o) return;
    o.textContent = chu;
    o.className = 'nhan-nhanh hien' + (loai === 'hong' ? ' hong' : '');
    if (hetGioBao) clearTimeout(hetGioBao);
    hetGioBao = setTimeout(
      () => { o.className = 'nhan-nhanh'; }, loai === 'hong' ? 8000 : 3000);
  }

  function baoDinhNghia(chu) {
    // PHẢI NHÌN THẤY ĐƯỢC. Bản đầu rơi về `console.log` khi không có thanh
    // tìm — tức câu "không tìm thấy" biến mất khỏi mắt người dùng. Đúng loại
    // hỏng lặng lẽ mà §4 nói tới.
    const o = document.getElementById('nhanNhanh');
    if (!o) return;
    o.textContent = chu;
    o.classList.add('hien');
    if (hetGioBao) clearTimeout(hetGioBao);
    hetGioBao = setTimeout(() => o.classList.remove('hien'), 3000);
  }

  function nhayToiDinhNghia(ten) {
    if (!ten) return false;
    const dich = timDinhNghia(ten, state.tree);
    if (!dich) {
      // KHÔNG TÌM THẤY khác KHÔNG TỒN TẠI (§4). Tên có thể đến từ thư viện
      // chuẩn (`print`, `len`), từ tham số hàm, hay từ một thẻ `ma_tho` —
      // ba chỗ mà cây thẻ không khai tên tường minh.
      baoDinhNghia(`Không tìm thấy thẻ khai "${ten}" trong chương trình này`);
      return false;
    }
    chonThe(dich.id);
    const el = document.getElementById('node_' + dich.id);
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    baoDinhNghia(`→ định nghĩa "${ten}"`);
    return true;
  }

  /** F12 trên thẻ đang chọn: nhảy theo tên CHÍNH mà thẻ ấy dùng. */
  function nhayTuTheDangChon() {
    if (!state.selectedNodeId) return false;
    const boc = timTheTheoId(state.tree, state.selectedNodeId);
    if (!boc || !boc.node) return false;
    const o = boc.node.o || {};
    // `goi_ham` là ca chính. `tra_ve`/`in_ra` thì lấy tên đầu trong biểu thức.
    const ten = String(o.ten_ham || o.gia_tri || o.noi_dung || '').trim();
    const dau = (ten.match(new RegExp(`(?<![\\p{L}\\p{N}\\p{M}_])[\\p{L}_][\\p{L}\\p{N}\\p{M}_]*`, 'u')) || [])[0];
    return nhayToiDinhNghia(dau);
  }

  // ==========================================================================
  // TÌM TRONG CHƯƠNG TRÌNH (Ctrl+F)
  // ==========================================================================
  // Khác hẳn ô tìm ở khay trái (`toolSearch`): ô kia LỌC danh sách khay thẻ
  // hoặc cây thư mục; cái này tìm trong CÂY THẺ đang mở và nhảy tới từng kết
  // quả. Hai thứ khác nhau nên để riêng, không gộp.
  const timKiem = { danhSach: [], viTri: -1, tuKhoa: '' };

  // Gom mọi CHỮ mà người dùng nhìn thấy trên một thẻ: các ô nhập (node.o, tuỳ
  // loại thẻ) + chú thích cuối dòng. Không lấy node.id/node.ma vì đó là thứ
  // nội bộ, người dùng không thấy — tìm theo chúng sẽ ra kết quả khó hiểu.
  function chuTrenThe(node) {
    const phan = [];
    // Từ khoá Python của loại thẻ này — xem chú thích ở TU_KHOA_PYTHON_CUA_THE.
    if (node.ma && TU_KHOA_PYTHON_CUA_THE[node.ma]) {
      phan.push(TU_KHOA_PYTHON_CUA_THE[node.ma]);
    }
    if (node.o) {
      for (const k in node.o) {
        const v = node.o[k];
        if (v !== null && v !== undefined && typeof v !== 'object') phan.push(String(v));
      }
    }
    if (node.duoi_dong) phan.push(String(node.duoi_dong));
    return phan.join(' ').toLowerCase();
  }

  function gomThePhuHop(danhSach, tuKhoa, ra) {
    (danhSach || []).forEach(node => {
      if (chuTrenThe(node).includes(tuKhoa)) ra.push(node.id);
      // Đi vào cả khối lồng nhau — thẻ trong thân `if`/`for` cũng phải tìm ra.
      if (node.than && node.than.length) gomThePhuHop(node.than, tuKhoa, ra);
    });
    return ra;
  }

  function xoaDanhDauTimKiem() {
    document.querySelectorAll('.the.tim-thay, .the.tim-thay-hien-tai')
      .forEach(el => el.classList.remove('tim-thay', 'tim-thay-hien-tai'));
  }

  // `cuon`: chỉ cuộn khi người dùng CHỦ ĐỘNG nhảy kết quả (gõ, bấm ↑/↓).
  // renderCanvas cũng gọi hàm này để vẽ lại dấu sau khi cây đổi — lúc đó mà
  // cuộn thì màn hình giật mỗi lần gõ một ký tự vào ô thẻ.
  function veKetQuaTimKiem(cuon = true) {
    xoaDanhDauTimKiem();
    const oDem = document.getElementById('findCount');
    const tong = timKiem.danhSach.length;
    if (oDem) {
      oDem.textContent = tong === 0 ? '0/0' : `${timKiem.viTri + 1}/${tong}`;
      // Ô rỗng thì không phải "không tìm thấy", chỉ là chưa gõ gì.
      oDem.classList.toggle('khong-thay', tong === 0 && timKiem.tuKhoa.length > 0);
    }
    timKiem.danhSach.forEach((id, i) => {
      const el = document.querySelector('#node_' + id + ' .the');
      if (!el) return;
      el.classList.add(i === timKiem.viTri ? 'tim-thay-hien-tai' : 'tim-thay');
    });
    if (cuon && timKiem.viTri >= 0) {
      const el = document.getElementById('node_' + timKiem.danhSach[timKiem.viTri]);
      if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function chayTimKiem(tuKhoa) {
    timKiem.tuKhoa = (tuKhoa || '').toLowerCase().trim();
    timKiem.danhSach = timKiem.tuKhoa
      ? gomThePhuHop(state.tree, timKiem.tuKhoa, [])
      : [];
    timKiem.viTri = timKiem.danhSach.length > 0 ? 0 : -1;
    veKetQuaTimKiem();
  }

  function nhayKetQua(buoc) {
    if (timKiem.danhSach.length === 0) return;
    // Quay vòng: qua kết quả cuối thì về đầu, và ngược lại.
    const n = timKiem.danhSach.length;
    timKiem.viTri = (timKiem.viTri + buoc + n) % n;
    veKetQuaTimKiem();
  }

  function moThanhTim() {
    const bar = document.getElementById('findBar');
    const input = document.getElementById('findInput');
    if (!bar || !input) return;
    bar.style.display = 'flex';
    input.focus();
    input.select();
    if (input.value) chayTimKiem(input.value);
  }

  // ==========================================================================
  // THAY THẾ (Ctrl+H)
  // ==========================================================================
  //
  // Nửa còn lại của Ctrl+F. Người mới học đổi tên biến bằng tay là chỗ sai
  // nhiều nhất: sửa được 7 chỗ, sót 1 chỗ, rồi ngồi dò `NameError`.
  //
  // BA ĐIỀU PHẢI ĐÚNG, và cả ba đều dễ làm sai:
  //
  // 1. TÌM không phân biệt hoa thường (Ctrl+F đang thế), nên THAY cũng phải
  //    tìm không phân biệt hoa thường — nhưng chỉ đổi ĐÚNG đoạn khớp, giữ
  //    nguyên mọi byte khác của ô. Dùng `toLowerCase()` rồi `split/join` là
  //    hỏng: nó trả về ô đã bị hạ hết chữ hoa.
  //
  // 2. Không dùng biểu thức chính quy trên chuỗi người dùng gõ. Gõ `(` hay
  //    `[` là `RegExp` ném lỗi, hoặc tệ hơn: `.` khớp mọi ký tự và thay nhầm
  //    chỗ mà không ai thấy.
  //
  // 3. THAY TẤT CẢ phải là MỘT bước hoàn tác. Ghi lịch sử từng ô là người
  //    dùng phải bấm Ctrl+Z ba chục lần để lấy lại chương trình cũ.

  /** Mọi vị trí `kim` xuất hiện trong `chuoi`, so không phân biệt hoa thường. */
  function viTriKhop(chuoi, kim) {
    const ra = [];
    if (!kim) return ra;
    const a = String(chuoi).toLowerCase();
    const b = kim.toLowerCase();
    let i = a.indexOf(b);
    while (i !== -1) {
      ra.push(i);
      // Nhảy qua đoạn vừa khớp, không cho khớp chồng lên nhau: tìm "aa"
      // trong "aaaa" phải ra 2 chỗ, không phải 3.
      i = a.indexOf(b, i + b.length);
    }
    return ra;
  }

  /** Thay mọi chỗ khớp trong MỘT chuỗi. Trả `[chuỗi mới, số chỗ đã thay]`. */
  function thayTrongChuoi(chuoi, kim, moi) {
    const vt = viTriKhop(chuoi, kim);
    if (vt.length === 0) return [chuoi, 0];
    const g = String(chuoi);
    let ra = '', truoc = 0;
    for (const i of vt) {
      ra += g.slice(truoc, i) + moi;
      truoc = i + kim.length;
    }
    // Phần đuôi sau chỗ khớp cuối — quên nó là cắt cụt ô của người dùng.
    ra += g.slice(truoc);
    return [ra, vt.length];
  }

  /** Thay trong mọi ô CHỮ của một thẻ. Trả số chỗ đã thay. */
  function thayTrongThe(node, kim, moi) {
    let dem = 0;
    if (node.o) {
      for (const k in node.o) {
        const v = node.o[k];
        // Đúng bộ ô mà `chuTrenThe` đọc — tìm ở đâu thì thay ở đó, không
        // rộng hơn. Rộng hơn là thay vào chỗ người dùng không nhìn thấy.
        if (v === null || v === undefined || typeof v === 'object') continue;
        const [moiV, n] = thayTrongChuoi(String(v), kim, moi);
        if (n > 0) { node.o[k] = moiV; dem += n; }
      }
    }
    if (node.duoi_dong) {
      const [moiD, n] = thayTrongChuoi(String(node.duoi_dong), kim, moi);
      if (n > 0) { node.duoi_dong = moiD; dem += n; }
    }
    if (dem > 0) node.da_sua = true;
    return dem;
  }

  function baoThayThe(soCho, soThe) {
    const o = document.getElementById('replaceCount');
    if (!o) return;
    o.textContent = soCho === 0
      ? 'không có chỗ nào'
      : `đã thay ${soCho} chỗ · ${soThe} thẻ`;
  }

  function thayMotCho() {
    const kim = timKiem.tuKhoa;
    const moi = (document.getElementById('replaceInput') || {}).value || '';
    if (!kim || timKiem.viTri < 0) { baoThayThe(0, 0); return; }
    // `timTheTheoId` trả về BỌC `{node, dsCha, chiSo}`, không trả về thẻ.
    // 25/08: bản đầu truyền thẳng cái bọc vào `thayTrongThe`; nó tìm `.o`
    // không thấy nên thay 0 chỗ và IM LẶNG — nút bấm được, hàm chạy, không
    // có gì xảy ra. Đúng bệnh "đọc sai tên trường" trong bảng tám lỗi ở §4
    // (`data.tep_tin` so với `danh_sach`), và cửa "mọi nút có người nghe"
    // KHÔNG bắt được loại này: người nghe có thật, chỉ là nó làm sai việc.
    // Bắt được bằng cách tự bấm ba lần rồi nhìn cây thẻ không đổi.
    const boc = timTheTheoId(state.tree, timKiem.danhSach[timKiem.viTri]);
    if (!boc || !boc.node) { baoThayThe(0, 0); return; }

    const n = thayTrongThe(boc.node, kim, moi);
    if (n === 0) { baoThayThe(0, 0); return; }
    onTreeChanged();                 // một thẻ = một bước hoàn tác

    // Tìm lại: thẻ vừa sửa có thể không còn khớp nữa, nên danh sách đổi.
    // Giữ vị trí ở chỗ CŨ để bấm "Thay" liên tiếp đi tới, không dậm chân.
    const truoc = timKiem.viTri;
    chayTimKiem(kim);
    if (timKiem.danhSach.length > 0) {
      timKiem.viTri = truoc % timKiem.danhSach.length;
      veKetQuaTimKiem();
    }
    baoThayThe(n, 1);
  }

  function thayTatCa() {
    const kim = timKiem.tuKhoa;
    const moi = (document.getElementById('replaceInput') || {}).value || '';
    if (!kim) { baoThayThe(0, 0); return; }

    let soCho = 0, soThe = 0;
    (function di(ds) {
      (ds || []).forEach(node => {
        const n = thayTrongThe(node, kim, moi);
        if (n > 0) { soCho += n; soThe += 1; }
        if (node.than && node.than.length) di(node.than);
      });
    })(state.tree);

    if (soCho === 0) { baoThayThe(0, 0); return; }
    // MỘT lần gọi cho TẤT CẢ -> đúng một bước hoàn tác.
    onTreeChanged();
    chayTimKiem(kim);
    baoThayThe(soCho, soThe);
  }

  function moThanhThayThe() {
    const bar = document.getElementById('replaceBar');
    if (bar) bar.style.display = 'flex';
    moThanhTim();
    const o = document.getElementById('replaceInput');
    if (o) o.focus();
  }

  function dongThanhTim() {
    const bar = document.getElementById('findBar');
    if (bar) bar.style.display = 'none';
    const barTT = document.getElementById('replaceBar');
    if (barTT) barTT.style.display = 'none';
    const oBao = document.getElementById('replaceCount');
    if (oBao) oBao.textContent = '';
    timKiem.danhSach = [];
    timKiem.viTri = -1;
    timKiem.tuKhoa = '';
    xoaDanhDauTimKiem();
  }

  // Traceback Python trỏ dòng trong run_script.py (tệp tạm, người dùng
  // không bao giờ thấy). Lấy khung CUỐI CÙNG thuộc script chính (không phải
  // khung nằm sâu trong thư viện chuẩn — traceback liệt kê theo thứ tự gọi
  // hàm, khung cuối luôn gần chỗ lỗi THẬT SỰ xảy ra nhất), tra `sourceMap`
  // để biết thẻ nào sinh ra dòng đó, rồi mượn NGUYÊN hạ tầng hiển thị lỗi
  // ĐỎ tĩnh sẵn có (badge trên .the, lọc theo node_id) — không cần CSS hay
  // đường vẽ mới.
  function danhDauTheGayLoiRuntime(stderr, sourceMap) {
    if (!stderr) return;
    const khopDong = [...stderr.matchAll(/File\s+"[^"]*run_script\.py",\s*line\s+(\d+)/g)];
    if (khopDong.length === 0) return;
    const soDong = parseInt(khopDong[khopDong.length - 1][1], 10);
    const nodeId = sourceMap[soDong - 1];
    if (!nodeId) return;

    const dongCuoi = stderr.trim().split('\n').filter(l => l.trim()).pop() || 'Lỗi khi chạy';
    state.diagnostics.danh_sach = state.diagnostics.danh_sach || [];
    state.diagnostics.danh_sach.push({
      muc_do: 'do',
      ma_loi: 'runtime_error',
      thong_diep: `⚡ Lỗi khi chạy: ${dongCuoi}`,
      node_id: nodeId,
      nguon: 'runtime',
    });
    renderCanvas();
  }

  async function runProgram() {
    const btnRun = document.getElementById('btnRun');
    const runText = document.getElementById('runBtnText');
    const termBody = document.getElementById('terminalBody');
    const metaStatus = document.getElementById('metaStatus');
    const metaTime = document.getElementById('metaTime');

    if (!state.codeExecutionEnabled) {
      termBody.innerHTML = '<div class="term-line term-stderr">Chạy mã đang tắt để bảo vệ máy. Mở/sửa/kiểm tra/lưu mã vẫn hoạt động.</div>';
      return;
    }

    if (state.diagnostics.so_loi_do > 0) {
      termBody.innerHTML = `<div class="term-line term-stderr">❌ KHÔNG THỂ CHẠY: Chương trình đang có ${state.diagnostics.so_loi_do} Lỗi ĐỎ cứng. Vui lòng sửa các lỗi đỏ trước khi chạy.</div>`;
      metaStatus.className = 'meta-status error';
      metaStatus.textContent = 'LỖI ĐỎ';
      return;
    }

    // sourceMap[i] = node.id sinh ra dòng vật lý thứ (i+1) của `code`. Khi
    // chạy lỗi, traceback trỏ số dòng trong run_script.py — tra bảng này để
    // biết THẺ NÀO gây lỗi, thay vì chỉ hiện số dòng của một tệp tạm người
    // dùng chưa từng thấy (khoảng trống bắt được 24/08 lúc tự dùng thử: lỗi
    // TĨNH đã sáng đúng thẻ từ lâu qua node_id, lỗi CHẠY THẬT thì chưa).
    const sourceMap = [];
    const editorInput = document.getElementById('codeEditorInput');
    let code = '';
    if (state.editorMode === 'code' && editorInput && editorInput.value.trim()) {
      code = editorInput.value;
    } else {
      code = TheValidator.sinhMaPython(state.tree, 0, sourceMap);
    }

    // Dọn annotation lỗi runtime của lần chạy TRƯỚC — không phải lỗi tĩnh,
    // chỉ dọn đúng loại 'runtime' để không đụng vào diagnostics tĩnh hiện có.
    state.diagnostics.danh_sach = (state.diagnostics.danh_sach || [])
      .filter(d => d.nguon !== 'runtime');
    if (!code || !code.trim()) {
      termBody.innerHTML = '<div class="term-line term-dim">> Chương trình rỗng, không có lệnh nào để chạy.</div>';
      return;
    }

    runText.textContent = 'ĐANG CHẠY...';
    btnRun.disabled = true;
    metaStatus.className = 'meta-status ready';
    metaStatus.textContent = 'ĐANG CHẠY';
    termBody.innerHTML = '<div class="term-line term-dim">> Đang thực thi trong tiến trình Python con cô lập (Trần 5.0s)...</div>';

    try {
      const resp = await authFetch('/api/chay', {
        method: 'POST',
        body: JSON.stringify({ code: code, tree: state.tree })
      });

      const res = await resp.json();
      metaTime.textContent = `${res.wall_time_ms || 0} ms`;

      if (res.status === 'PASS') {
        metaStatus.className = 'meta-status pass';
        metaStatus.textContent = 'PASS';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '(Không có đầu ra stdout)')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Hoàn thành trong ${res.wall_time_ms} ms · Exit code: 0]</div>
        `;
        const termBanner = document.getElementById('terminalDoctorBanner');
        if (termBanner) termBanner.style.display = 'none';
      } else if (res.status === 'TIMEOUT') {
        metaStatus.className = 'meta-status timeout';
        metaStatus.textContent = 'TIMEOUT';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '')}</div>
          <div class="term-line term-stderr">${escapeHtml(res.stderr || '')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Đã ngắt sau 5.0 giây · Exit code: ${res.exit_code}]</div>
        `;
        const termBanner = document.getElementById('terminalDoctorBanner');
        if (termBanner) termBanner.style.display = 'none';
      } else {
        metaStatus.className = 'meta-status error';
        metaStatus.textContent = 'LỖI RUNTIME';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '')}</div>
          <div class="term-line term-stderr">${escapeHtml(res.stderr || 'Lỗi không xác định')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Thất bại · Exit code: ${res.exit_code}]</div>
        `;
        danhDauTheGayLoiRuntime(res.stderr, sourceMap);

        // Bác sĩ AI phân tích lỗi runtime
        const diag = phanTichLoiRuntime(res.stderr, code, state.tree, sourceMap);
        const termBanner = document.getElementById('terminalDoctorBanner');
        const termTitle = document.getElementById('terminalDoctorTitle');
        const termDesc = document.getElementById('terminalDoctorDesc');
        const btnAutoFix = document.getElementById('btnTerminalAutoFix');

        if (diag && termBanner) {
          termTitle.textContent = diag.tieuDe;
          termDesc.textContent = diag.cachSua;
          termBanner.style.display = 'flex';
          currentRuntimePatch = diag.patch;
          if (btnAutoFix) {
            btnAutoFix.style.display = diag.patch ? 'inline-flex' : 'none';
          }
        } else if (termBanner) {
          termBanner.style.display = 'none';
        }
      }
    } catch (err) {
      metaStatus.className = 'meta-status error';
      metaStatus.textContent = 'LỖI MẠNG';
      termBody.innerHTML = `<div class="term-line term-stderr">Lỗi kết nối máy chủ: ${escapeHtml(err.message)}</div>`;
    } finally {
      runText.textContent = 'CHẠY THỬ';
      btnRun.disabled = !state.codeExecutionEnabled;
    }
  }

  // ==========================================================================
  // 6. MẪU BÀI, MỞ TỆP & LƯU TỆP (CỬA CỨNG MỞ-LƯU LOSSLESS)
  // ==========================================================================
  function clearNodeDirtyFlags(nodes) {
    (nodes || []).forEach(node => {
      node.da_sua = false;
      clearNodeDirtyFlags(node.than || []);
    });
  }

  function normalizedPath(path) {
    return String(path || '').replaceAll('\\', '/').toLowerCase();
  }

  async function readJsonSafely(resp) {
    const text = await resp.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch (_) {
      return { error: text };
    }
  }

  let danhSachWorkflowCache = [];
  let danhMucWorkflowDangChon = 'all';
  let tuKhoaWorkflow = '';

  function demTongSoThe(nodes) {
    if (!Array.isArray(nodes)) return 0;
    let count = 0;
    nodes.forEach(n => {
      count++;
      if (Array.isArray(n.than) && n.than.length > 0) {
        count += demTongSoThe(n.than);
      }
    });
    return count;
  }

  function veDanhSachWorkflow() {
    const container = document.getElementById('samplesListContainer');
    if (!container) return;

    const filtered = danhSachWorkflowCache.filter(m => {
      const matchCat = (danhMucWorkflowDangChon === 'all') || (m.danh_muc === danhMucWorkflowDangChon);
      const kw = tuKhoaWorkflow.trim().toLowerCase();
      const matchKw = !kw || (m.ten && m.ten.toLowerCase().includes(kw)) || (m.mo_ta && m.mo_ta.toLowerCase().includes(kw));
      return matchCat && matchKw;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 32px 16px; color: var(--text-muted);">
          <div style="font-size: 28px; margin-bottom: 8px;">🔍</div>
          <p>Không tìm thấy workflow hoặc dự án mẫu nào phù hợp.</p>
        </div>
      `;
      return;
    }

    const catLabels = {
      du_lieu: '📊 Dữ Liệu',
      web_api: '🌐 Web & API',
      tu_dong_hoa: '🤖 Tự Động',
      co_ban: '📚 Nhập Môn'
    };

    let html = '<div class="workflow-grid">';
    filtered.forEach(m => {
      const catClass = m.danh_muc || 'co_ban';
      const catLabel = catLabels[m.danh_muc] || '📚 Nhập Môn';
      const nodeCount = demTongSoThe(m.tree);
      const tag = m.the_tag || 'Workflow';

      html += `
        <div class="workflow-item-card" data-wfid="${m.id}">
          <div class="wf-card-top">
            <span class="wf-badge-category ${catClass}">${catLabel}</span>
            <span class="wf-card-node-count">${nodeCount} thẻ</span>
          </div>
          <div class="wf-card-title">${escapeHtml(m.ten)}</div>
          <div class="wf-card-desc">${escapeHtml(m.mo_ta)}</div>
          <div class="wf-card-bottom">
            <span class="wf-card-tag">#${escapeHtml(tag)}</span>
            <button class="wf-btn-open" type="button">Mở Workflow</button>
          </div>
        </div>
      `;
    });
    html += '</div>';

    container.innerHTML = html;

    // Gắn sự kiện click nạp workflow
    container.querySelectorAll('.workflow-item-card').forEach(cardEl => {
      const wfId = cardEl.getAttribute('data-wfid');
      const wfData = danhSachWorkflowCache.find(x => x.id === wfId);
      if (!wfData) return;

      const handleSelect = () => {
        state.tree = JSON.parse(JSON.stringify(wfData.tree));
        xoaLichSu();
        state.activeFilePath = '';
        state.activeFileSha256 = null;
        state.activeFileName = wfData.ten;
        const curNameEl = document.getElementById('currentFileName');
        if (curNameEl) curNameEl.textContent = wfData.ten;
        const modal = document.getElementById('samplesModal');
        if (modal) modal.style.display = 'none';

        // Tự động chuyển sang chế độ song song để thấy cả thẻ và mã
        setEditorMode('split');
        onTreeChanged();
        baoNhanh(`Đã mở: ${wfData.ten}`);
      };

      cardEl.addEventListener('click', handleSelect);
    });
  }

  function setupWorkflowHubControls() {
    const searchInput = document.getElementById('workflowSearchInput');
    const catTabs = document.getElementById('workflowCatTabs');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        tuKhoaWorkflow = e.target.value;
        veDanhSachWorkflow();
      });
    }

    if (catTabs) {
      catTabs.querySelectorAll('.wf-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          catTabs.querySelectorAll('.wf-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          danhMucWorkflowDangChon = btn.getAttribute('data-cat') || 'all';
          veDanhSachWorkflow();
        });
      });
    }
  }

  async function loadSamples() {
    try {
      const resp = await authFetch('/api/mau');
      if (resp.ok) {
        const data = await resp.json();
        danhSachWorkflowCache = data.mau || [];
        veDanhSachWorkflow();
      }
    } catch (err) {
      console.warn('Lỗi tải kho workflow:', err);
    }
  }

  // ==========================================================================
  // TRÌNH GỠ LỖI TRỰC QUAN THEO BƯỚC THẺ (VISUAL CARD DEBUGGER & TIMELINE)
  // ==========================================================================
  const debuggerState = {
    isActive: false,
    currentStepIndex: 0,
    steps: [],
    autoPlayTimer: null,
    autoPlaySpeed: 900
  };

  function danhGiaBieuThuc(expr, scope) {
    if (!expr || typeof expr !== 'string') return 0;
    const trimmed = expr.trim();
    if (!trimmed) return 0;

    // 1. Literal số nguyên / số thực
    if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
      return Number(trimmed);
    }
    // 2. Literal chuỗi
    if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
      return trimmed.slice(1, -1);
    }
    // 3. Literal boolean
    if (trimmed === 'True') return true;
    if (trimmed === 'False') return false;
    if (trimmed === 'None') return null;

    // 4. Biến trong scope
    if (scope && Object.prototype.hasOwnProperty.call(scope, trimmed)) {
      return scope[trimmed];
    }

    // 5. f-string
    if (trimmed.startsWith('f"') || trimmed.startsWith("f'")) {
      const raw = trimmed.slice(2, -1);
      return raw.replace(/\{([^}]+)\}/g, (_, inner) => {
        const key = inner.trim();
        return Object.prototype.hasOwnProperty.call(scope, key) ? String(scope[key]) : inner;
      });
    }

    // 6. Range / Danh sách literal
    if (trimmed.startsWith('range(') && trimmed.endsWith(')')) {
      const argStr = trimmed.slice(6, -1).trim();
      const n = Number(argStr) || 5;
      return Array.from({ length: Math.min(n, 20) }, (_, i) => i);
    }
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      try {
        const inner = trimmed.slice(1, -1).trim();
        if (!inner) return [];
        return inner.split(',').map(s => {
          s = s.trim();
          if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
          if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) return s.slice(1, -1);
          return scope[s] !== undefined ? scope[s] : s;
        });
      } catch (_) {}
    }

    // 7. Phép toán số học 2 ngôi cơ bản (a + b, a - b, a * b, a / b)
    const matchMath = trimmed.match(/^([a-zA-Z0-9_.]+)\s*([+\-*/%])\s*([a-zA-Z0-9_.]+)$/);
    if (matchMath) {
      const leftVal = danhGiaBieuThuc(matchMath[1], scope);
      const op = matchMath[2];
      const rightVal = danhGiaBieuThuc(matchMath[3], scope);
      if (typeof leftVal === 'number' && typeof rightVal === 'number') {
        if (op === '+') return leftVal + rightVal;
        if (op === '-') return leftVal - rightVal;
        if (op === '*') return leftVal * rightVal;
        if (op === '/' && rightVal !== 0) return Math.round((leftVal / rightVal) * 100) / 100;
        if (op === '%') return leftVal % rightVal;
      }
      if (op === '+' && (typeof leftVal === 'string' || typeof rightVal === 'string')) {
        return String(leftVal) + String(rightVal);
      }
    }

    // 8. So sánh điều kiện (a >= b, a == b, a < b, a > b, a != b, a <= b)
    const matchCond = trimmed.match(/^([a-zA-Z0-9_.]+)\s*(>=|<=|==|!=|>|<)\s*([a-zA-Z0-9_.]+)$/);
    if (matchCond) {
      const leftVal = danhGiaBieuThuc(matchCond[1], scope);
      const op = matchCond[2];
      const rightVal = danhGiaBieuThuc(matchCond[3], scope);
      if (op === '>=') return leftVal >= rightVal;
      if (op === '<=') return leftVal <= rightVal;
      if (op === '==') return leftVal == rightVal;
      if (op === '!=') return leftVal != rightVal;
      if (op === '>') return leftVal > rightVal;
      if (op === '<') return leftVal < rightVal;
    }

    // Fallback: chuỗi ban đầu
    return trimmed;
  }

  function sinhDanhSachBuocThucThi(treeNodes) {
    const steps = [];
    const globalScope = {};

    function cloneScope(sc) {
      const res = {};
      for (const k in sc) {
        const val = sc[k];
        if (Array.isArray(val)) res[k] = [...val];
        else if (val !== null && typeof val === 'object') res[k] = { ...val };
        else res[k] = val;
      }
      return res;
    }

    function runNodes(nodes, currentScope, maxSteps = 100) {
      for (const node of nodes) {
        if (steps.length >= maxSteps) break;

        if (node.ma === 'gan') {
          const varName = (node.o && node.o.ten_bien) ? node.o.ten_bien.trim() : 'bien';
          const expr = (node.o && node.o.gia_tri) ? node.o.gia_tri.trim() : '0';
          const evaluated = danhGiaBieuThuc(expr, currentScope);
          if (varName && varName !== '_') {
            currentScope[varName] = evaluated;
          }
          steps.push({
            nodeId: node.id,
            cardMa: 'gan',
            lineCode: `${varName} = ${expr}`,
            actionDesc: `Gán biến: ${varName} = ${JSON.stringify(evaluated)}`,
            variables: cloneScope(currentScope),
            changedVar: varName,
            val: evaluated
          });
        } else if (node.ma === 'in_ra') {
          const expr = (node.o && node.o.noi_dung) ? node.o.noi_dung.trim() : '';
          const evaluated = danhGiaBieuThuc(expr, currentScope);
          steps.push({
            nodeId: node.id,
            cardMa: 'in_ra',
            lineCode: `print(${expr})`,
            actionDesc: `In ra terminal: ${JSON.stringify(evaluated)}`,
            variables: cloneScope(currentScope),
            output: String(evaluated)
          });
        } else if (node.ma === 'lap_moi') {
          const varName = (node.o && node.o.bien) ? node.o.bien.trim() : 'i';
          const iterExpr = (node.o && node.o.day) ? node.o.day.trim() : 'range(3)';
          let items = danhGiaBieuThuc(iterExpr, currentScope);
          if (!Array.isArray(items)) items = [0, 1, 2];

          steps.push({
            nodeId: node.id,
            cardMa: 'lap_moi',
            lineCode: `for ${varName} in ${iterExpr}:`,
            actionDesc: `Bắt đầu vòng lặp duyệt qua ${items.length} phần tử của ${iterExpr}`,
            variables: cloneScope(currentScope)
          });

          for (let idx = 0; idx < Math.min(items.length, 10); idx++) {
            const itemVal = items[idx];
            currentScope[varName] = itemVal;
            steps.push({
              nodeId: node.id,
              cardMa: 'lap_moi',
              lineCode: `# Vòng lặp [${idx + 1}/${items.length}]: ${varName} = ${itemVal}`,
              actionDesc: `Lặp nhịp ${idx + 1}: ${varName} nhận giá trị ${JSON.stringify(itemVal)}`,
              variables: cloneScope(currentScope),
              changedVar: varName,
              val: itemVal
            });
            if (node.than && node.than.length > 0) {
              runNodes(node.than, currentScope, maxSteps);
            }
          }
        } else if (node.ma === 'neu') {
          const condExpr = (node.o && node.o.dieu_kien) ? node.o.dieu_kien.trim() : 'True';
          const condResult = Boolean(danhGiaBieuThuc(condExpr, currentScope));
          steps.push({
            nodeId: node.id,
            cardMa: 'neu',
            lineCode: `if ${condExpr}:  # -> ${condResult ? 'True' : 'False'}`,
            actionDesc: `Kiểm tra điều kiện: "${condExpr}" -> ${condResult ? 'ĐÚNG (Chạy thân)' : 'SAI (Bỏ qua)'}`,
            variables: cloneScope(currentScope),
            condResult: condResult
          });
          if (condResult && node.than && node.than.length > 0) {
            runNodes(node.than, currentScope, maxSteps);
          }
        } else if (node.ma === 'nguoc_lai') {
          steps.push({
            nodeId: node.id,
            cardMa: 'nguoc_lai',
            lineCode: `else:`,
            actionDesc: `Nhánh ngược lại (else)`,
            variables: cloneScope(currentScope)
          });
          if (node.than && node.than.length > 0) {
            runNodes(node.than, currentScope, maxSteps);
          }
        } else if (node.ma === 'ham') {
          const fnName = (node.o && node.o.ten_ham) ? node.o.ten_ham.trim() : 'ham';
          const params = (node.o && node.o.tham_so) ? node.o.tham_so.trim() : '';
          steps.push({
            nodeId: node.id,
            cardMa: 'ham',
            lineCode: `def ${fnName}(${params}):`,
            actionDesc: `Định nghĩa hàm ${fnName}(${params}) trong bộ nhớ`,
            variables: cloneScope(currentScope)
          });
          if (node.than && node.than.length > 0) {
            runNodes(node.than, currentScope, maxSteps);
          }
        } else if (node.ma === 'tra_ve') {
          const retExpr = (node.o && node.o.gia_tri) ? node.o.gia_tri.trim() : 'None';
          const evaluated = danhGiaBieuThuc(retExpr, currentScope);
          currentScope['return_value'] = evaluated;
          steps.push({
            nodeId: node.id,
            cardMa: 'tra_ve',
            lineCode: `return ${retExpr}`,
            actionDesc: `Trả về kết quả: ${JSON.stringify(evaluated)}`,
            variables: cloneScope(currentScope),
            changedVar: 'return_value',
            val: evaluated
          });
        } else if (node.ma === 'chu_thich') {
          const cmText = (node.o && node.o.noi_dung) ? node.o.noi_dung : '';
          steps.push({
            nodeId: node.id,
            cardMa: 'chu_thich',
            lineCode: `# ${cmText}`,
            actionDesc: `Bỏ qua dòng chú thích: "${cmText}"`,
            variables: cloneScope(currentScope)
          });
        } else {
          steps.push({
            nodeId: node.id,
            cardMa: node.ma,
            lineCode: `# Lệnh ${node.ma}`,
            actionDesc: `Thực thi thẻ ${node.ma}`,
            variables: cloneScope(currentScope)
          });
        }
      }
    }

    runNodes(treeNodes, globalScope);
    return steps;
  }

  function batDauGoLoi() {
    if (!state.tree || state.tree.length === 0) {
      baoNhanh('Vùng soạn thảo đang trống, hãy thêm thẻ để gỡ lỗi!');
      return;
    }

    const steps = sinhDanhSachBuocThucThi(state.tree);
    if (steps.length === 0) {
      baoNhanh('Không tìm thấy bước thực thi nào trong chương trình.');
      return;
    }

    debuggerState.isActive = true;
    debuggerState.steps = steps;
    debuggerState.currentStepIndex = 0;

    const bar = document.getElementById('debugControlBar');
    if (bar) bar.style.display = 'flex';

    const btnDebug = document.getElementById('btnDebug');
    if (btnDebug) {
      btnDebug.classList.add('active');
      const text = document.getElementById('debugBtnText');
      if (text) text.textContent = 'DỪNG GỠ LỖI';
    }

    // Chuyển sang Tab Biến Số Scope
    const tabBtn = document.querySelector('.tab-btn[data-tab="tabDebugger"]');
    if (tabBtn) tabBtn.click();

    capNhatGiaoDienGoLoi();
    baoNhanh('Đã khởi động trình gỡ lỗi trực quan!');
  }

  function dungGoLoi() {
    if (debuggerState.autoPlayTimer) {
      clearInterval(debuggerState.autoPlayTimer);
      debuggerState.autoPlayTimer = null;
      const btnAuto = document.getElementById('btnDebugAutoPlay');
      if (btnAuto) btnAuto.textContent = '⏯ Tự Động';
    }

    debuggerState.isActive = false;
    debuggerState.steps = [];
    debuggerState.currentStepIndex = 0;

    const bar = document.getElementById('debugControlBar');
    if (bar) bar.style.display = 'none';

    document.querySelectorAll('.hang.card-exec-active').forEach(el => {
      el.classList.remove('card-exec-active');
    });

    const btnDebug = document.getElementById('btnDebug');
    if (btnDebug) {
      btnDebug.classList.remove('active');
      const text = document.getElementById('debugBtnText');
      if (text) text.textContent = 'GỠ LỖI';
    }

    const scopeInfo = document.getElementById('scopeStepInfo');
    if (scopeInfo) scopeInfo.innerHTML = '<span class="scope-pill">Chưa bật gỡ lỗi</span>';

    const scopeBody = document.getElementById('debugScopeBody');
    if (scopeBody) {
      scopeBody.innerHTML = `
        <div class="trace-empty-hint">
          <span>Bấm nút <strong>"🐞 GỠ LỖI"</strong> trên thanh công cụ để theo dõi biến số và luồng thực thi từng bước.</span>
        </div>
      `;
    }

    const varCount = document.getElementById('debugVarCount');
    if (varCount) varCount.textContent = '0';
  }

  function buocTiep() {
    if (!debuggerState.isActive) {
      batDauGoLoi();
      return;
    }
    if (debuggerState.currentStepIndex < debuggerState.steps.length - 1) {
      debuggerState.currentStepIndex++;
      capNhatGiaoDienGoLoi();
    } else {
      if (debuggerState.autoPlayTimer) {
        clearInterval(debuggerState.autoPlayTimer);
        debuggerState.autoPlayTimer = null;
        const btnAuto = document.getElementById('btnDebugAutoPlay');
        if (btnAuto) btnAuto.textContent = '⏯ Tự Động';
      }
      baoNhanh('Đã chạy đến bước cuối cùng!');
    }
  }

  function buocTruoc() {
    if (!debuggerState.isActive) return;
    if (debuggerState.currentStepIndex > 0) {
      debuggerState.currentStepIndex--;
      capNhatGiaoDienGoLoi();
    }
  }

  function nhayToiBuoc(stepIdx) {
    if (!debuggerState.isActive) return;
    const clamped = Math.max(0, Math.min(stepIdx, debuggerState.steps.length - 1));
    debuggerState.currentStepIndex = clamped;
    capNhatGiaoDienGoLoi();
  }

  function batTatTuDongChay() {
    if (!debuggerState.isActive) {
      batDauGoLoi();
    }
    const btnAuto = document.getElementById('btnDebugAutoPlay');
    if (debuggerState.autoPlayTimer) {
      clearInterval(debuggerState.autoPlayTimer);
      debuggerState.autoPlayTimer = null;
      if (btnAuto) btnAuto.textContent = '⏯ Tự Động';
    } else {
      if (btnAuto) btnAuto.textContent = '⏸ Tạm Dừng';
      debuggerState.autoPlayTimer = setInterval(() => {
        if (debuggerState.currentStepIndex < debuggerState.steps.length - 1) {
          buocTiep();
        } else {
          clearInterval(debuggerState.autoPlayTimer);
          debuggerState.autoPlayTimer = null;
          if (btnAuto) btnAuto.textContent = '⏯ Tự Động';
        }
      }, debuggerState.autoPlaySpeed);
    }
  }

  function capNhatGiaoDienGoLoi() {
    if (!debuggerState.isActive || debuggerState.steps.length === 0) return;

    const step = debuggerState.steps[debuggerState.currentStepIndex];
    const totalSteps = debuggerState.steps.length;

    const slider = document.getElementById('debugTimelineSlider');
    const counter = document.getElementById('debugStepCounter');
    const actionText = document.getElementById('debugActionText');

    if (slider) {
      slider.max = totalSteps;
      slider.value = debuggerState.currentStepIndex + 1;
    }
    if (counter) {
      counter.textContent = `Bước ${debuggerState.currentStepIndex + 1} / ${totalSteps}`;
    }
    if (actionText) {
      actionText.textContent = step.actionDesc;
    }

    document.querySelectorAll('.hang.card-exec-active').forEach(el => {
      el.classList.remove('card-exec-active');
    });

    if (step.nodeId) {
      const activeHang = document.getElementById(`node_${step.nodeId}`);
      if (activeHang) {
        activeHang.classList.add('card-exec-active');
        activeHang.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }

    const scopeInfo = document.getElementById('scopeStepInfo');
    if (scopeInfo) {
      scopeInfo.innerHTML = `<span class="scope-pill">Bước ${debuggerState.currentStepIndex + 1} / ${totalSteps}: ${escapeHtml(step.lineCode)}</span>`;
    }

    const scopeBody = document.getElementById('debugScopeBody');
    const varCount = document.getElementById('debugVarCount');

    if (scopeBody) {
      const entries = Object.entries(step.variables || {});
      if (varCount) varCount.textContent = entries.length;

      if (entries.length === 0) {
        scopeBody.innerHTML = `
          <div style="text-align: center; padding: 20px; color: var(--text-muted); font-size: 12px;">
            Chưa có biến số nào được khởi tạo tại bước này.
          </div>
        `;
      } else {
        let tableHtml = `
          <table class="scope-var-table">
            <thead>
              <tr>
                <th style="width: 25%;">Tên Biến</th>
                <th style="width: 20%;">Kiểu Dữ Liệu</th>
                <th style="width: 55%;">Giá Trị Hiện Tại</th>
              </tr>
            </thead>
            <tbody>
        `;

        entries.forEach(([varName, val]) => {
          const isChanged = (step.changedVar === varName);
          let typeStr = typeof val;
          let valClass = 'str';

          if (Array.isArray(val)) {
            typeStr = `list[${val.length}]`;
            valClass = 'num';
          } else if (val === null) {
            typeStr = 'NoneType';
            valClass = 'bool';
          } else if (typeof val === 'number') {
            typeStr = Number.isInteger(val) ? 'int' : 'float';
            valClass = 'num';
          } else if (typeof val === 'boolean') {
            typeStr = 'bool';
            valClass = 'bool';
          } else if (typeof val === 'object') {
            typeStr = 'dict';
          }

          tableHtml += `
            <tr class="var-row ${isChanged ? 'highlight-changed' : ''}">
              <td class="var-name">${escapeHtml(varName)} ${isChanged ? '✨' : ''}</td>
              <td class="var-type">${typeStr}</td>
              <td class="var-val ${valClass}">${escapeHtml(JSON.stringify(val))}</td>
            </tr>
          `;
        });

        tableHtml += '</tbody></table>';
        scopeBody.innerHTML = tableHtml;
      }
    }
  }

  // ==========================================================================
  // PHÒNG THỬ THÁCH LẬP TRÌNH & HỆ THỐNG CHẤM ĐIỂM TEST CASES TỰ ĐỘNG
  // ==========================================================================
  const DANH_SACH_THU_THACH = [
    {
      id: 'bai_tong_chan',
      ten: '1. [Cơ Bản] Tính Tổng Số Chẵn Trong Dãy',
      danh_muc: 'co_ban',
      do_kho: 'Dễ',
      xp: '+50 XP',
      ten_ham: 'tong_so_chan',
      tham_so: 'ds',
      mo_ta: 'Viết hàm tong_so_chan(ds) nhận vào một danh sách các số nguyên, trả về tổng của tất cả các số chẵn trong danh sách đó.',
      starterTree: [
        { id: "c1_1", ma: "ham", o: { ten_ham: "tong_so_chan", tham_so: "ds" }, than: [
          { id: "c1_2", ma: "gan", o: { ten_bien: "tong", gia_tri: "0" }, than: [] },
          { id: "c1_3", ma: "lap_moi", o: { bien: "x", day: "ds" }, than: [
            { id: "c1_4", ma: "neu", o: { dieu_kien: "x % 2 == 0" }, than: [
              { id: "c1_5", ma: "gan", o: { ten_bien: "tong", gia_tri: "tong + x" }, than: [] }
            ]}
          ]},
          { id: "c1_6", ma: "tra_ve", o: { gia_tri: "tong" }, than: [] }
        ]},
        { id: "c1_7", ma: "gan", o: { ten_bien: "kq", gia_tri: "tong_so_chan([1, 2, 3, 4, 6])" }, than: [] },
        { id: "c1_8", ma: "in_ra", o: { noi_dung: "kq" }, than: [] }
      ],
      testCases: [
        { input: [1, 2, 3, 4], expected: 6 },
        { input: [1, 3, 5], expected: 0 },
        { input: [10, 20, 30], expected: 60 },
        { input: [], expected: 0 }
      ]
    },
    {
      id: 'bai_min_max',
      ten: '2. [Thuật Toán] Tìm Giá Trị Min & Max',
      danh_muc: 'thuat_toan',
      do_kho: 'Trung Bình',
      xp: '+100 XP',
      ten_ham: 'tim_min_max',
      tham_so: 'ds',
      mo_ta: 'Viết hàm tim_min_max(ds) trả về tuple (min_val, max_val) chứa giá trị nhỏ nhất và lớn nhất trong dãy số.',
      starterTree: [
        { id: "c2_1", ma: "ham", o: { ten_ham: "tim_min_max", tham_so: "ds" }, than: [
          { id: "c2_2", ma: "neu", o: { dieu_kien: "len(ds) == 0" }, than: [
            { id: "c2_3", ma: "tra_ve", o: { gia_tri: "(None, None)" }, than: [] }
          ]},
          { id: "c2_4", ma: "gan", o: { ten_bien: "nho_nhat", gia_tri: "ds[0]" }, than: [] },
          { id: "c2_5", ma: "gan", o: { ten_bien: "lon_nhat", gia_tri: "ds[0]" }, than: [] },
          { id: "c2_6", ma: "lap_moi", o: { bien: "x", day: "ds" }, than: [
            { id: "c2_7", ma: "neu", o: { dieu_kien: "x < nho_nhat" }, than: [
              { id: "c2_8", ma: "gan", o: { ten_bien: "nho_nhat", gia_tri: "x" }, than: [] }
            ]},
            { id: "c2_9", ma: "neu", o: { dieu_kien: "x > lon_nhat" }, than: [
              { id: "c2_10", ma: "gan", o: { ten_bien: "lon_nhat", gia_tri: "x" }, than: [] }
            ]}
          ]},
          { id: "c2_11", ma: "tra_ve", o: { gia_tri: "(nho_nhat, lon_nhat)" }, than: [] }
        ]},
        { id: "c2_12", ma: "in_ra", o: { noi_dung: "tim_min_max([5, 2, 9, 1, 7])" }, than: [] }
      ],
      testCases: [
        { input: [5, 2, 9, 1, 7], expected: [1, 9] },
        { input: [100], expected: [100, 100] },
        { input: [-5, 0, 5], expected: [-5, 5] }
      ]
    },
    {
      id: 'bai_chuan_hoa_ten',
      ten: '3. [Xử Lý Chuỗi] Chuẩn Hóa Họ Và Tên',
      danh_muc: 'chuoi',
      do_kho: 'Trung Bình',
      xp: '+100 XP',
      ten_ham: 'chuan_hoa_ten',
      tham_so: 'ten',
      mo_ta: 'Viết hàm chuan_hoa_ten(ten) loại bỏ khoảng trắng thừa và viết hoa chữ cái đầu của mỗi từ trong tên.',
      starterTree: [
        { id: "c3_1", ma: "ham", o: { ten_ham: "chuan_hoa_ten", tham_so: "ten" }, than: [
          { id: "c3_2", ma: "gan", o: { ten_bien: "cac_tu", gia_tri: "ten.strip().split()" }, than: [] },
          { id: "c3_3", ma: "gan", o: { ten_bien: "tu_hoa", gia_tri: "[t.capitalize() for t in cac_tu]" }, than: [] },
          { id: "c3_4", ma: "tra_ve", o: { gia_tri: "' '.join(tu_hoa)" }, than: [] }
        ]},
        { id: "c3_5", ma: "in_ra", o: { noi_dung: 'chuan_hoa_ten("  nguyen   van   a  ")' }, than: [] }
      ],
      testCases: [
        { input: "  nguyen   van   a  ", expected: "Nguyen Van A" },
        { input: "AURA", expected: "Aura" },
        { input: "lap trinh python", expected: "Lap Trinh Python" }
      ]
    },
    {
      id: 'bai_loc_san_pham',
      ten: '4. [Thực Chiến] Lọc Sản Phẩm Hợp Ngân Sách',
      danh_muc: 'thuc_te',
      do_kho: 'Thực Tế',
      xp: '+150 XP',
      ten_ham: 'loc_san_pham',
      tham_so: 'ds_sp, ngan_sach',
      mo_ta: 'Viết hàm loc_san_pham(ds_sp, ngan_sach) lọc ra danh sách tên sản phẩm có giá nhỏ hơn hoặc bằng ngân sách.',
      starterTree: [
        { id: "c4_1", ma: "ham", o: { ten_ham: "loc_san_pham", tham_so: "ds_sp, ngan_sach" }, than: [
          { id: "c4_2", ma: "gan", o: { ten_bien: "ket_qua", gia_tri: "[]" }, than: [] },
          { id: "c4_3", ma: "lap_moi", o: { bien: "sp", day: "ds_sp" }, than: [
            { id: "c4_4", ma: "neu", o: { dieu_kien: "sp['gia'] <= ngan_sach" }, than: [
              { id: "c4_5", ma: "gan", o: { ten_bien: "_", gia_tri: "ket_qua.append(sp['ten'])" }, than: [] }
            ]}
          ]},
          { id: "c4_6", ma: "tra_ve", o: { gia_tri: "ket_qua" }, than: [] }
        ]},
        { id: "c4_7", ma: "gan", o: { ten_bien: "ds", gia_tri: '[{"ten": "Chuột", "gia": 250}, {"ten": "Bàn phím", "gia": 800}]' }, "than": [] },
        { id: "c4_8", ma: "in_ra", o: { noi_dung: "loc_san_pham(ds, 500)" }, than: [] }
      ],
      testCases: [
        { input: [[{"ten": "Chuột", "gia": 250}, {"ten": "Bàn phím", "gia": 800}], 500], expected: ["Chuột"] },
        { input: [[{"ten": "Tai nghe", "gia": 450}, {"ten": "Loa", "gia": 1200}], 300], expected: [] }
      ]
    }
  ];

  let challengeDangChon = null;
  let challengeDanhMucHienTai = 'all';
  let challengeTuKhoaHienTai = '';

  function layDanhSachBaiDaGiai() {
    try {
      const saved = localStorage.getItem('aura_solved_challenges');
      if (saved) return JSON.parse(saved);
    } catch (_) {}
    return [];
  }

  function danhDauBaiDaGiai(baiId) {
    const list = layDanhSachBaiDaGiai();
    if (!list.includes(baiId)) {
      list.push(baiId);
      try {
        localStorage.setItem('aura_solved_challenges', JSON.stringify(list));
      } catch (_) {}
    }
  }

  function veDanhSachThuThach() {
    const container = document.getElementById('challengesListContainer');
    if (!container) return;

    const solvedList = layDanhSachBaiDaGiai();
    const filtered = DANH_SACH_THU_THACH.filter(c => {
      const matchCat = (challengeDanhMucHienTai === 'all' || c.danh_muc === challengeDanhMucHienTai);
      const kw = challengeTuKhoaHienTai.trim().toLowerCase();
      const matchKw = !kw || c.ten.toLowerCase().includes(kw) || c.mo_ta.toLowerCase().includes(kw);
      return matchCat && matchKw;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 32px 16px; color: var(--text-muted);">
          <div style="font-size: 28px; margin-bottom: 8px;">🎯</div>
          <p>Không tìm thấy thử thách nào phù hợp.</p>
        </div>
      `;
      return;
    }

    let html = '<div class="workflow-grid">';
    filtered.forEach(c => {
      const isSolved = solvedList.includes(c.id);
      html += `
        <div class="workflow-item-card challenge-card" data-cid="${c.id}">
          <div class="wf-card-header">
            <span class="wf-badge-category ${c.danh_muc}">${c.do_kho}</span>
            <span class="wf-badge-tag">${c.xp} ${isSolved ? '✓ ĐÃ GIẢI' : ''}</span>
          </div>
          <h4 class="wf-card-title">${escapeHtml(c.ten)}</h4>
          <p class="wf-card-desc">${escapeHtml(c.mo_ta)}</p>
          <div class="wf-card-footer">
            <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">${c.testCases.length} Test Cases</span>
            <span class="wf-open-hint">Bắt đầu giải →</span>
          </div>
        </div>
      `;
    });
    html += '</div>';

    container.innerHTML = html;

    container.querySelectorAll('.challenge-card').forEach(cardEl => {
      cardEl.addEventListener('click', () => {
        const cId = cardEl.getAttribute('data-cid');
        chonThuThach(cId);
      });
    });
  }

  function chonThuThach(cId) {
    const c = DANH_SACH_THU_THACH.find(x => x.id === cId);
    if (!c) return;

    challengeDangChon = c;
    state.tree = JSON.parse(JSON.stringify(c.starterTree));
    xoaLichSu();
    state.activeFilePath = '';
    state.activeFileSha256 = null;
    state.activeFileName = c.ten;

    const curNameEl = document.getElementById('currentFileName');
    if (curNameEl) curNameEl.textContent = c.ten;

    const banner = document.getElementById('challengeActiveBanner');
    const titleEl = document.getElementById('activeChallengeTitle');
    const descEl = document.getElementById('activeChallengeDesc');

    if (banner) banner.style.display = 'flex';
    if (titleEl) titleEl.textContent = c.ten;
    if (descEl) descEl.textContent = c.mo_ta;

    const modal = document.getElementById('challengesModal');
    if (modal) modal.style.display = 'none';

    setEditorMode('split');
    onTreeChanged();

    // Mở Tab Chấm Điểm
    const tabBtn = document.querySelector('.tab-btn[data-tab="tabChallengeGrader"]');
    if (tabBtn) tabBtn.click();

    const passBadge = document.getElementById('challengePassCount');
    if (passBadge) passBadge.textContent = `0/${c.testCases.length}`;

    const info = document.getElementById('graderSummaryInfo');
    if (info) info.innerHTML = '<span class="scope-pill">Sẵn sàng chấm điểm</span>';

    const body = document.getElementById('graderResultsBody');
    if (body) {
      body.innerHTML = `
        <div style="padding: 14px; text-align: center; color: var(--text-muted); font-size: 12px;">
          Bấm <strong>"🏆 CHẤM ĐIỂM"</strong> trên thanh banner để kiểm tra bài làm của bạn với <strong>${c.testCases.length} Test Cases</strong>.
        </div>
      `;
    }

    baoNhanh(`Đã mở thử thách: ${c.ten}`);
  }

  function dongThuThach() {
    challengeDangChon = null;
    const banner = document.getElementById('challengeActiveBanner');
    if (banner) banner.style.display = 'none';
  }

  // 30/08/2026 — ban cu TU VIET LOI GIAI bang JS theo c.id roi so voi `expected`
  // do chinh tep nay khai; the cua nguoi hoc KHONG BAO GIO duoc doc (bien `scope`
  // dung o day la ma chet). Do tay: canvas 0 the, 0 request, van ra 4/4 · 100% ·
  // "XUAT SAC", va con ghi bai do vao localStorage aura_solved_challenges.
  // Cot "Thuc Te (Actual)" la so bia.
  //
  // Nay fail-closed. Bo cham chua noi vao cong chay ma that (/api/chay) thi no
  // KHONG DO DUOC, ma khong do duoc thi khong co quyen phan quyet — tach ba trang
  // thai: dat · do duoc ma khong dat · KHONG DO DUOC. De bai (Input/Expected) van
  // hien vi do la du kien that; chi bo phan bia va bo viec cong XP.
  // Vẽ một thẻ kết quả cho MỘT trường hợp thử.
  // Ba trạng thái, không được gộp: đạt · đo được mà không đạt · KHÔNG ĐO ĐƯỢC.
  function veTheTestCase(soThuTu, dauVao, kyVong, thucTe, trangThai, ghiChu) {
    const mau = { dat: '#34D399', truot: '#F87171', chua_do: '#FBBF24' }[trangThai];
    const nhan = { dat: '✓ ĐẠT', truot: '✕ SAI', chua_do: '⏳ KHÔNG ĐO ĐƯỢC' }[trangThai];
    const lop = { dat: 'pass', truot: 'fail', chua_do: '' }[trangThai];
    return `
      <div class="test-case-card ${lop}">
        <div class="test-case-header">
          <span style="font-weight: 700; color: #94A3B8;">Test Case #${soThuTu}</span>
          <span style="font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; color: ${mau}; border: 1px solid ${mau};">${nhan}</span>
        </div>
        <div class="test-case-grid">
          <div>
            <span class="test-io-label">Đầu Vào (Input):</span>
            <span class="test-io-val" style="color: #60A5FA;">${escapeHtml(JSON.stringify(dauVao))}</span>
          </div>
          <div>
            <span class="test-io-label">Kỳ Vọng (Expected):</span>
            <span class="test-io-val" style="color: #34D399;">${escapeHtml(JSON.stringify(kyVong))}</span>
          </div>
          <div>
            <span class="test-io-label">Thực Tế (Actual):</span>
            <span class="test-io-val" style="color: ${mau};">${escapeHtml(thucTe)}</span>
          </div>
        </div>
        ${ghiChu ? `<div style="margin-top: 6px; font-size: 11px; color: var(--text-muted);">${escapeHtml(ghiChu)}</div>` : ''}
      </div>
    `;
  }

  // Trạng thái KHÔNG ĐO ĐƯỢC: không phải "sai", cũng không phải "đúng".
  function veKhongDoDuoc(c, testCases, viSao) {
    const passBadge = document.getElementById('challengePassCount');
    if (passBadge) passBadge.textContent = `—/${testCases.length}`;

    const info = document.getElementById('graderSummaryInfo');
    if (info) {
      info.innerHTML = `<span class="scope-pill" style="color: #FBBF24; border-color: #F59E0B;">CHƯA CHẤM ĐƯỢC</span>`;
    }

    const body = document.getElementById('graderResultsBody');
    if (!body) return;
    let html = `
      <div class="grade-summary-card has-fail">
        <div>
          <div class="grade-score-title">CHƯA CHẤM ĐƯỢC — không phải "sai", cũng không phải "đúng"</div>
          <div class="grade-score-desc">${escapeHtml(viSao)}</div>
        </div>
        <div style="font-size: 24px;">⏳</div>
      </div>
    `;
    testCases.forEach((tc, idx) => {
      html += veTheTestCase(idx + 1, tc.input, tc.expected, 'chưa chạy', 'chua_do', '');
    });
    body.innerHTML = html;
  }

  // 30/08/2026 — bản đầu của hàm này TỰ VIẾT LỜI GIẢI bằng JS theo c.id rồi so với
  // `expected` do chính app.js khai; thẻ của người học không bao giờ được đọc.
  // Đo tay: canvas 0 thẻ, 0 request, vẫn ra 4/4 · 100% · "XUẤT SẮC", và còn ghi
  // vào localStorage aura_solved_challenges. Cột "Thực Tế" là số bịa.
  //
  // Nay chấm thật: ghép mã của người học với một bộ đo sinh tại chỗ, đẩy sang
  // /api/chay (tiến trình Python riêng, trần 5s của backend), rồi đọc lại kết quả
  // từng trường hợp từ stdout theo dấu __AURA_DO__.
  //
  // GIỚI HẠN, phải nói cùng lúc: /api/chay CHƯA cô lập toàn diện. the_api.py trả
  // về execution_notice "vẫn có quyền ghi tệp của tài khoản Windows", và hôm
  // 19/08 đo được `cwd` ở thư mục tạm KHÔNG chặn được ghi bằng đường dẫn tuyệt
  // đối. Bộ chấm này chạy mã NGƯỜI DÙNG tự gõ trên máy của chính họ, không phải
  // mã người lạ gửi đến — nhưng câu chữ đó phải hiện trên màn hình, không được
  // giấu, nên execution_notice được in thẳng vào thẻ tổng kết bên dưới.
  async function chamDiemBaiTap() {
    if (!challengeDangChon) {
      baoNhanh('Vui lòng mở một thử thách từ mục "🏆 Thử Thách" trước khi chấm điểm!');
      return;
    }

    const c = challengeDangChon;
    const testCases = c.testCases || [];

    const tabBtn = document.querySelector('.tab-btn[data-tab="tabChallengeGrader"]');
    if (tabBtn) tabBtn.click();

    // Lấy mã đúng y hệt runProgram: ưu tiên ô soạn thảo nếu đang ở chế độ mã thuần.
    const editorInput = document.getElementById('codeEditorInput');
    let code = '';
    if (state.editorMode === 'code' && editorInput && editorInput.value.trim()) {
      code = editorInput.value;
    } else {
      code = TheValidator.sinhMaPython(state.tree, 0, []);
    }

    if (!state.codeExecutionEnabled) {
      veKhongDoDuoc(c, testCases,
        'Cổng chạy mã (/api/chay) đang TẮT nên không chạy được bài của bạn. Không chạy thì không có quyền phán quyết. Bật bằng cờ --allow-exec khi khởi động app.');
      baoNhanh('Chưa chấm được: cổng chạy mã đang tắt.');
      return;
    }
    if (!code.trim()) {
      veKhongDoDuoc(c, testCases, 'Trên canvas chưa có thẻ nào, không có gì để chạy.');
      baoNhanh('Chưa chấm được: chưa có mã nào.');
      return;
    }

    // Bộ đo: ghép sau mã của người học. In mỗi trường hợp một dòng có dấu riêng
    // để không lẫn với print() của chính người học.
    const thamSo = String(c.tham_so || '').split(',').map(s => s.trim()).filter(Boolean);
    const cacDoiSo = testCases.map(tc =>
      (thamSo.length > 1 && Array.isArray(tc.input)) ? tc.input : [tc.input]);
    const boDo = [
      '',
      '# ===== bo do do trinh cham sinh ra, khong phai ma cua nguoi hoc =====',
      'import json as _aura_json',
      '_aura_cases = _aura_json.loads(' + JSON.stringify(JSON.stringify(cacDoiSo)) + ')',
      '_aura_ten = ' + JSON.stringify(String(c.ten_ham || '')),
      'for _aura_i, _aura_args in enumerate(_aura_cases):',
      '    _aura_fn = globals().get(_aura_ten)',
      '    if _aura_fn is None:',
      '        _aura_out = {"i": _aura_i, "trang_thai": "thieu_ham"}',
      '    else:',
      '        try:',
      '            _aura_out = {"i": _aura_i, "trang_thai": "chay_xong", "kq": _aura_fn(*_aura_args)}',
      '        except Exception as _aura_e:',
      '            _aura_out = {"i": _aura_i, "trang_thai": "no_loi",',
      '                         "loi": type(_aura_e).__name__ + ": " + str(_aura_e)}',
      '    print("__AURA_DO__" + _aura_json.dumps(_aura_out, ensure_ascii=False, default=str))',
      ''
    ].join('\n');

    const info = document.getElementById('graderSummaryInfo');
    if (info) info.innerHTML = `<span class="scope-pill">Đang chạy bài của bạn…</span>`;

    // Khong bao try/catch quanh ca doan ve: mot loi khi VE se bi bao cao thanh
    // "khong goi duoc cong chay ma" — nhan sai viec, dung ho loi CLAUDE.md muc 4.
    // Va cua tests/test_hop_dong_api.js phai thay `const res = await resp.json()`
    // gan TRUC TIEP moi noi duoc binding sang handler Python de doi chieu tung
    // truong; gan vao mot bien khai bao san thi no khong chung minh duoc, va no
    // bao dung: luc do khong con bang chung tinh nao rang res la than cua route ay.
    const resp = await authFetch('/api/chay', {
      method: 'POST',
      body: JSON.stringify({ code: code + '\n' + boDo })
    }).catch(() => null);
    if (!resp) {
      veKhongDoDuoc(c, testCases, 'Không gọi được cổng chạy mã (/api/chay).');
      baoNhanh('Chưa chấm được: không gọi được cổng chạy mã.');
      return;
    }
    const res = await resp.json().catch(() => null);
    if (!res) {
      veKhongDoDuoc(c, testCases, `Cổng chạy mã trả về ${resp.status} nhưng nội dung không đọc được.`);
      baoNhanh('Chưa chấm được: phản hồi không đọc được.');
      return;
    }
    if (!resp.ok) {
      veKhongDoDuoc(c, testCases,
        `Cổng chạy mã trả về ${resp.status}: ${res.error || res.trang_thai || 'không rõ'}.`);
      baoNhanh('Chưa chấm được: cổng chạy mã từ chối.');
      return;
    }

    // Đọc lại kết quả từng trường hợp. Thiếu dòng nào thì trường hợp đó KHÔNG ĐO
    // ĐƯỢC — không được quy thành "sai". Quá giờ cũng vậy: 12/08 đã trả giá một
    // lần vì nhãn timeout đọc y hệt một phán quyết về hành vi.
    const doDuoc = {};
    for (const dong of String(res.stdout || '').split('\n')) {
      const k = dong.indexOf('__AURA_DO__');
      if (k === -1) continue;
      try {
        const o = JSON.parse(dong.slice(k + '__AURA_DO__'.length));
        doDuoc[o.i] = o;
      } catch (e) { /* dòng hỏng thì coi như không đo được */ }
    }

    let soDat = 0, soChuaDo = 0;
    let html = '';
    testCases.forEach((tc, idx) => {
      const o = doDuoc[idx];
      if (!o) {
        soChuaDo += 1;
        const viSao = res.timed_out
          ? 'Chương trình chạy quá trần thời gian nên bị cắt trước khi đo tới trường hợp này.'
          : (String(res.stderr || '').trim()
              ? 'Chương trình dừng vì lỗi trước khi đo tới trường hợp này.'
              : 'Không nhận được kết quả đo cho trường hợp này.');
        html += veTheTestCase(idx + 1, tc.input, tc.expected, 'không đo được', 'chua_do', viSao);
        return;
      }
      if (o.trang_thai === 'thieu_ham') {
        soChuaDo += 1;
        html += veTheTestCase(idx + 1, tc.input, tc.expected, 'không đo được', 'chua_do',
          `Chưa tìm thấy hàm ${c.ten_ham}(...) trong bài của bạn.`);
        return;
      }
      if (o.trang_thai === 'no_loi') {
        html += veTheTestCase(idx + 1, tc.input, tc.expected, o.loi, 'truot',
          'Hàm của bạn chạy nhưng nổ lỗi với đầu vào này.');
        return;
      }
      const dat = JSON.stringify(o.kq) === JSON.stringify(tc.expected);
      if (dat) soDat += 1;
      html += veTheTestCase(idx + 1, tc.input, tc.expected, JSON.stringify(o.kq),
        dat ? 'dat' : 'truot', '');
    });

    const doHet = (soChuaDo === 0);
    const datHet = doHet && (soDat === testCases.length);

    const passBadge = document.getElementById('challengePassCount');
    if (passBadge) passBadge.textContent = doHet ? `${soDat}/${testCases.length}` : `—/${testCases.length}`;

    if (info) {
      const mau = datHet ? '#34D399' : (doHet ? '#F87171' : '#FBBF24');
      const chu = datHet ? '✓ ĐẠT TẤT CẢ'
                         : (doHet ? `Chưa đạt (${soDat}/${testCases.length})`
                                  : `CHƯA CHẤM ĐƯỢC ĐỦ (${soChuaDo}/${testCases.length} chưa đo được)`);
      info.innerHTML = `<span class="scope-pill" style="color: ${mau}; border-color: ${mau};">${chu}</span>`;
    }

    const tieuDe = datHet
      ? `Đã chạy thật ${testCases.length}/${testCases.length} trường hợp và tất cả đều khớp.`
      : (doHet
          ? `Đã chạy thật ${testCases.length} trường hợp: ${soDat} khớp, ${testCases.length - soDat} chưa khớp.`
          : `Chỉ đo được ${testCases.length - soChuaDo}/${testCases.length} trường hợp — phần còn lại KHÔNG ĐO ĐƯỢC, không kết luận.`);

    const body = document.getElementById('graderResultsBody');
    if (body) {
      body.innerHTML = `
        <div class="grade-summary-card ${datHet ? 'all-pass' : 'has-fail'}">
          <div>
            <div class="grade-score-title">${escapeHtml(tieuDe)}</div>
            <div class="grade-score-desc">Chạy trong ${res.wall_time_ms || 0} ms. ${escapeHtml(res.execution_notice || '')}</div>
          </div>
          <div style="font-size: 24px;">${datHet ? '🏅' : (doHet ? '🔧' : '⏳')}</div>
        </div>
      ` + html;
    }

    // Chỉ ghi "đã giải" khi ĐO ĐƯỢC HẾT và ĐẠT HẾT. Đo không hết thì không cộng gì.
    if (datHet) {
      danhDauBaiDaGiai(c.id);
      baoNhanh(`Đã chạy thật ${testCases.length} trường hợp, tất cả đều khớp.`);
    } else if (doHet) {
      baoNhanh(`Đã chạy thật: ${soDat}/${testCases.length} trường hợp khớp.`);
    } else {
      baoNhanh(`Chưa chấm được đủ: ${soChuaDo}/${testCases.length} trường hợp không đo được.`);
    }
  }

  function setupChallengeHubControls() {
    const searchInput = document.getElementById('challengeSearchInput');
    const catTabs = document.getElementById('challengeCatTabs');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        challengeTuKhoaHienTai = e.target.value;
        veDanhSachThuThach();
      });
    }

    if (catTabs) {
      catTabs.querySelectorAll('.wf-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          catTabs.querySelectorAll('.wf-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          challengeDanhMucHienTai = btn.getAttribute('data-ccat') || 'all';
          veDanhSachThuThach();
        });
      });
    }
  }

  // ==========================================================================
  // BỘ CHUYỂN ĐỔI SƠ ĐỒ KHỐI THUẬT TOÁN (FLOWCHART GENERATOR & SVG EXPORTER)
  // ==========================================================================
  let flowchartZoomLevel = 1.0;
  let currentGeneratedSVG = '';
  let currentGeneratedMermaid = '';

  function sinhSVGSoDoKhoi(treeNodes) {
    if (!treeNodes || treeNodes.length === 0) {
      return `
        <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
          <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
          <p>Chưa có thẻ nào trên Canvas để sinh sơ đồ khối thuật toán.</p>
        </div>
      `;
    }

    const flatBlocks = [];
    
    function flattenForFlow(nodes, depth = 0, branchLabel = '') {
      nodes.forEach((node) => {
        let label = '';
        let sub = '';
        let shape = 'rect';

        if (node.ma === 'ham') {
          shape = 'oval';
          label = `Hàm: ${(node.o && node.o.ten_ham) || 'ham'}()`;
          sub = `def ${(node.o && node.o.ten_ham) || 'ham'}(${(node.o && node.o.tham_so) || ''})`;
        } else if (node.ma === 'gan') {
          shape = 'rect';
          label = `Gán: ${(node.o && node.o.ten_bien) || 'x'} = ${(node.o && node.o.gia_tri) || '0'}`;
          sub = `${(node.o && node.o.ten_bien) || 'x'} = ${(node.o && node.o.gia_tri) || '0'}`;
        } else if (node.ma === 'neu') {
          shape = 'diamond';
          label = `Điều kiện: ${(node.o && node.o.dieu_kien) || 'True'}?`;
          sub = `if ${(node.o && node.o.dieu_kien) || 'True'}:`;
        } else if (node.ma === 'nguoc_lai') {
          shape = 'rect';
          label = `Nhánh: Ngược lại (else)`;
          sub = `else:`;
        } else if (node.ma === 'lap_moi') {
          shape = 'loop';
          label = `Lặp: ${(node.o && node.o.bien) || 'i'} trong ${(node.o && node.o.day) || 'day'}`;
          sub = `for ${(node.o && node.o.bien) || 'i'} in ${(node.o && node.o.day) || 'day'}:`;
        } else if (node.ma === 'lap_khi') {
          shape = 'loop';
          label = `Lặp khi: ${(node.o && node.o.dieu_kien) || 'cond'}`;
          sub = `while ${(node.o && node.o.dieu_kien) || 'cond'}:`;
        } else if (node.ma === 'in_ra') {
          shape = 'io';
          label = `Xuất ra: ${(node.o && node.o.noi_dung) || 'print'}`;
          sub = `print(${(node.o && node.o.noi_dung) || ''})`;
        } else if (node.ma === 'tra_ve') {
          shape = 'oval';
          label = `Trả về: ${(node.o && node.o.gia_tri) || 'val'}`;
          sub = `return ${(node.o && node.o.gia_tri) || ''}`;
        } else {
          shape = 'rect';
          label = `Lệnh: ${node.ma}`;
          sub = `# ${node.ma}`;
        }

        flatBlocks.push({
          id: node.id,
          ma: node.ma,
          label: label,
          sub: sub,
          shape: shape,
          depth: depth,
          branchLabel: branchLabel
        });

        if (node.than && node.than.length > 0) {
          flattenForFlow(node.than, depth + 1, node.ma === 'neu' ? 'ĐÚNG' : (node.ma === 'lap_moi' ? 'LẶP' : ''));
        }
      });
    }

    flattenForFlow(treeNodes, 0, '');

    const nodeW = 240;
    const nodeH = 50;
    const gapY = 46;
    const startY = 40;
    const centerX = 280;

    const totalHeight = startY + (flatBlocks.length + 2) * (nodeH + gapY) + 40;
    const totalWidth = 560;

    let svg = `
      <svg class="flow-svg" width="${totalWidth}" height="${totalHeight}" viewBox="0 0 ${totalWidth} ${totalHeight}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#64748B" />
          </marker>
        </defs>
    `;

    // 1. Start Node
    svg += `
      <g class="flow-node flow-node-start" transform="translate(${centerX - nodeW / 2}, ${startY})">
        <rect x="0" y="0" width="${nodeW}" height="${nodeH}" rx="25" ry="25" />
        <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">🟢 BẮT ĐẦU CHƯƠNG TRÌNH</text>
        <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">Start Flow</text>
      </g>
    `;

    let prevY = startY + nodeH;

    // 2. Render từng khối và đường nối
    flatBlocks.forEach((block, idx) => {
      const curY = startY + (idx + 1) * (nodeH + gapY);
      const x = centerX - nodeW / 2;
      const y = curY;

      svg += `
        <line class="flow-link" x1="${centerX}" y1="${prevY}" x2="${centerX}" y2="${curY}" />
      `;

      if (block.branchLabel) {
        svg += `
          <rect x="${centerX + 6}" y="${prevY + 12}" width="42" height="18" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="#F59E0B" stroke-width="1"/>
          <text class="flow-edge-label" x="${centerX + 27}" y="${prevY + 22}">${block.branchLabel}</text>
        `;
      }

      if (block.shape === 'oval') {
        svg += `
          <g class="flow-node flow-node-start" data-nodeid="${block.id}" transform="translate(${x}, ${y})">
            <rect x="0" y="0" width="${nodeW}" height="${nodeH}" rx="25" ry="25" />
            <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">${escapeHtml(block.label)}</text>
            <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">${escapeHtml(block.sub)}</text>
          </g>
        `;
      } else if (block.shape === 'diamond') {
        const cx = nodeW / 2;
        const cy = nodeH / 2;
        const points = `${cx},0 ${nodeW},${cy} ${cx},${nodeH} 0,${cy}`;
        svg += `
          <g class="flow-node flow-node-diamond" data-nodeid="${block.id}" transform="translate(${x}, ${y})">
            <polygon points="${points}" />
            <text class="flow-text-main" x="${cx}" y="${cy - 6}">${escapeHtml(block.label)}</text>
            <text class="flow-text-sub" x="${cx}" y="${cy + 10}">${escapeHtml(block.sub)}</text>
          </g>
        `;
      } else if (block.shape === 'loop') {
        const offset = 16;
        const points = `${offset},0 ${nodeW - offset},0 ${nodeW},${nodeH / 2} ${nodeW - offset},${nodeH} ${offset},${nodeH} 0,${nodeH / 2}`;
        svg += `
          <g class="flow-node flow-node-loop" data-nodeid="${block.id}" transform="translate(${x}, ${y})">
            <polygon points="${points}" />
            <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">${escapeHtml(block.label)}</text>
            <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">${escapeHtml(block.sub)}</text>
          </g>
        `;
      } else if (block.shape === 'io') {
        const skew = 14;
        const points = `${skew},0 ${nodeW},0 ${nodeW - skew},${nodeH} 0,${nodeH}`;
        svg += `
          <g class="flow-node flow-node-io" data-nodeid="${block.id}" transform="translate(${x}, ${y})">
            <polygon points="${points}" />
            <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">${escapeHtml(block.label)}</text>
            <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">${escapeHtml(block.sub)}</text>
          </g>
        `;
      } else {
        svg += `
          <g class="flow-node flow-node-rect" data-nodeid="${block.id}" transform="translate(${x}, ${y})">
            <rect x="0" y="0" width="${nodeW}" height="${nodeH}" rx="6" />
            <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">${escapeHtml(block.label)}</text>
            <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">${escapeHtml(block.sub)}</text>
          </g>
        `;
      }

      prevY = curY + nodeH;
    });

    // 3. End Node
    const endY = startY + (flatBlocks.length + 1) * (nodeH + gapY);
    svg += `
      <line class="flow-link" x1="${centerX}" y1="${prevY}" x2="${centerX}" y2="${endY}" />
      <g class="flow-node flow-node-start" transform="translate(${centerX - nodeW / 2}, ${endY})">
        <rect x="0" y="0" width="${nodeW}" height="${nodeH}" rx="25" ry="25" />
        <text class="flow-text-main" x="${nodeW / 2}" y="${nodeH / 2 - 6}">🔴 KẾT THÚC CHƯƠNG TRÌNH</text>
        <text class="flow-text-sub" x="${nodeW / 2}" y="${nodeH / 2 + 10}">End Flow</text>
      </g>
    `;

    svg += '</svg>';
    // 30/08/2026 — TRIM. Chuỗi này dựng bằng template literal mở đầu bằng
    // xuống dòng + 6 dấu cách, nên nó bắt đầu bằng khoảng trắng chứ không phải
    // '<svg'. Hệ quả: chốt chặn `currentGeneratedSVG.startsWith('<svg')` trong
    // taiSVGSoDoKhoi() LUÔN LUÔN sai với mọi cây thẻ không rỗng, nên nút
    // "Tải File SVG" CHƯA TỪNG hoạt động — nó báo "Không có sơ đồ khối hợp lệ
    // để tải!" trong khi người dùng đang nhìn thẳng vào sơ đồ.
    // Đo tay: modal mở, `#flowchartModal svg` có thật, click -> 0 blob, 0 thẻ <a>
    // được bấm, và #nhanNhanh hiện đúng câu chối trên.
    // Sửa ở NGUỒN chứ không nới chốt chặn: chốt ấy đúng, chuỗi mới là thứ bẩn.
    // Trim ở đây thì cả nút tải, cả tệp flowchart.svg trong gói zip đều sạch
    // (gói hôm nay nhúng SVG mở đầu bằng 6 dấu cách — xem base64 đã giải).
    return svg.trim();
  }

  function sinhMaMermaid(treeNodes) {
    if (!treeNodes || treeNodes.length === 0) return 'flowchart TD\n  Start(["Bắt đầu"]) --> End(["Kết thúc"])';

    let code = 'flowchart TD\n  Start(["🟢 Bắt đầu"])';
    let prevId = 'Start';

    function addNodes(nodes) {
      nodes.forEach((n) => {
        const curId = `N_${n.id.replace(/[^a-zA-Z0-9_]/g, '_')}`;
        let label = '';
        if (n.ma === 'ham') {
          label = `def ${(n.o && n.o.ten_ham) || 'ham'}(${(n.o && n.o.tham_so) || ''})`;
          code += `\n  ${prevId} --> ${curId}(["${label}"])`;
        } else if (n.ma === 'neu') {
          label = `if ${(n.o && n.o.dieu_kien) || 'True'}`;
          code += `\n  ${prevId} --> ${curId}{"${label}?"}`;
        } else if (n.ma === 'lap_moi') {
          label = `for ${(n.o && n.o.bien) || 'i'} in ${(n.o && n.o.day) || 'day'}`;
          code += `\n  ${prevId} --> ${curId}[["${label}"]]`;
        } else if (n.ma === 'in_ra') {
          label = `print(${(n.o && n.o.noi_dung) || ''})`;
          code += `\n  ${prevId} --> ${curId}[/"${label}"/]`;
        } else if (n.ma === 'tra_ve') {
          label = `return ${(n.o && n.o.gia_tri) || ''}`;
          code += `\n  ${prevId} --> ${curId}(["${label}"])`;
        } else {
          label = `${(n.o && n.o.ten_bien) || 'x'} = ${(n.o && n.o.gia_tri) || '0'}`;
          code += `\n  ${prevId} --> ${curId}["${label}"]`;
        }

        prevId = curId;

        if (n.than && n.than.length > 0) {
          addNodes(n.than);
        }
      });
    }

    addNodes(treeNodes);
    code += `\n  ${prevId} --> End(["🔴 Kết thúc"])`;
    return code;
  }

  function capNhatZoomFlowchart() {
    const container = document.getElementById('flowchartCanvasContainer');
    if (container) {
      container.style.transform = `scale(${flowchartZoomLevel})`;
    }
  }

  function moSoDoKhoi() {
    const modal = document.getElementById('flowchartModal');
    const container = document.getElementById('flowchartCanvasContainer');
    if (!modal || !container) return;

    currentGeneratedSVG = sinhSVGSoDoKhoi(state.tree);
    currentGeneratedMermaid = sinhMaMermaid(state.tree);

    container.innerHTML = currentGeneratedSVG;
    flowchartZoomLevel = 1.0;
    capNhatZoomFlowchart();

    container.querySelectorAll('.flow-node[data-nodeid]').forEach(nodeEl => {
      nodeEl.addEventListener('click', () => {
        const nId = nodeEl.getAttribute('data-nodeid');
        if (nId) {
          chonThe(nId);
          modal.style.display = 'none';
          const targetHang = document.getElementById(`node_${nId}`);
          if (targetHang) targetHang.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          baoNhanh(`Đã định vị thẻ ${nId} trên Canvas!`);
        }
      });
    });

    modal.style.display = 'flex';
  }

  function dongSoDoKhoi() {
    const modal = document.getElementById('flowchartModal');
    if (modal) modal.style.display = 'none';
  }

  function taiSVGSoDoKhoi() {
    if (!currentGeneratedSVG || !currentGeneratedSVG.startsWith('<svg')) {
      baoNhanh('Không có sơ đồ khối hợp lệ để tải!');
      return;
    }

    const blob = new Blob([currentGeneratedSVG], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flowchart_${state.activeFileName || 'aura_program'}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    baoNhanh('Đã tải tệp vector SVG thành công!');
  }

  function saoChepMermaid() {
    if (!currentGeneratedMermaid) {
      baoNhanh('Chưa có mã Mermaid để sao chép!');
      return;
    }
    navigator.clipboard.writeText(currentGeneratedMermaid).then(() => {
      baoNhanh('Đã sao chép mã Mermaid vào bộ nhớ tạm!');
    }).catch(() => {
      baoNhanh('Không thể sao chép tự động, vui lòng thử lại!');
    });
  }

  function setupFlowchartControls() {
    const btnOpen = document.getElementById('btnFlowchart');
    const btnClose = document.getElementById('btnCloseFlowchart');
    const btnZoomIn = document.getElementById('btnFlowchartZoomIn');
    const btnZoomOut = document.getElementById('btnFlowchartZoomOut');
    const btnZoomReset = document.getElementById('btnFlowchartZoomReset');
    const btnDownload = document.getElementById('btnDownloadSVG');
    const btnCopy = document.getElementById('btnCopyMermaid');

    if (btnOpen) btnOpen.addEventListener('click', moSoDoKhoi);
    if (btnClose) btnClose.addEventListener('click', dongSoDoKhoi);

    if (btnZoomIn) {
      btnZoomIn.addEventListener('click', () => {
        flowchartZoomLevel = Math.min(2.5, flowchartZoomLevel + 0.15);
        capNhatZoomFlowchart();
      });
    }
    if (btnZoomOut) {
      btnZoomOut.addEventListener('click', () => {
        flowchartZoomLevel = Math.max(0.4, flowchartZoomLevel - 0.15);
        capNhatZoomFlowchart();
      });
    }
    if (btnZoomReset) {
      btnZoomReset.addEventListener('click', () => {
        flowchartZoomLevel = 1.0;
        capNhatZoomFlowchart();
      });
    }

    if (btnDownload) btnDownload.addEventListener('click', taiSVGSoDoKhoi);
    if (btnCopy) btnCopy.addEventListener('click', saoChepMermaid);
  }

  // ==========================================================================
  // BÁC SĨ LOGIC & TRỢ LÝ SỬA LỖI TỰ ĐỘNG (AI LOGIC DOCTOR & AUTO-FIX ENGINE)
  // ==========================================================================
  let currentRuntimePatch = null;

  function phanTichLoiRuntime(stderr, code, tree, sourceMap) {
    if (!stderr) return null;

    const nameMatch = stderr.match(/NameError:\s*name\s+'([^']+)'\s+is not defined/i);
    if (nameMatch) {
      const varName = nameMatch[1];
      const khopDong = [...stderr.matchAll(/File\s+"[^"]*run_script\.py",\s*line\s+(\d+)/g)];
      let targetNodeId = null;
      if (khopDong.length > 0 && sourceMap) {
        const soDong = parseInt(khopDong[khopDong.length - 1][1], 10);
        targetNodeId = sourceMap[soDong - 1];
      }

      return {
        tieuDe: `Biến '${varName}' chưa được gán giá trị`,
        moTaLoi: `Chương trình cố gắng sử dụng biến '${varName}' trước khi biến này được khai báo hoặc gán giá trị.`,
        nguyenNhan: `NameError: name '${varName}' is not defined`,
        cachSua: `Khởi tạo biến '${varName} = 0' trước khi sử dụng.`,
        theLoiId: targetNodeId,
        patch: {
          type: 'insert_before',
          targetId: targetNodeId,
          node: {
            id: `the_gan_${++state.nodeIdCounter}`,
            ma: 'gan',
            o: { ten_bien: varName, gia_tri: '0' },
            than: []
          }
        }
      };
    }

    const syntaxMatch = stderr.match(/SyntaxError:\s*invalid syntax/i) || stderr.match(/SyntaxError:\s*cannot assign to/i);
    if (syntaxMatch) {
      let badIfNode = null;
      function findBadIf(nodes) {
        for (const n of nodes) {
          if (n.ma === 'neu' && n.o && n.o.dieu_kien) {
            if (/(?<![=<>!])=(?!=)/.test(n.o.dieu_kien)) {
              badIfNode = n;
              return;
            }
          }
          if (n.than && n.than.length) findBadIf(n.than);
        }
      }
      findBadIf(tree);

      if (badIfNode) {
        const newCond = badIfNode.o.dieu_kien.replace(/(?<![=<>!])=(?!=)/g, '==');
        return {
          tieuDe: `Dùng nhầm dấu gán '=' trong câu điều kiện 'Nếu'`,
          moTaLoi: `Trong Python, so sánh bằng phải dùng hai dấu '==' thay vì một dấu '=' (dấu gán).`,
          nguyenNhan: `if ${badIfNode.o.dieu_kien}:`,
          cachSua: `Đổi thành '${newCond}'`,
          theLoiId: badIfNode.id,
          patch: {
            type: 'replace_field',
            nodeId: badIfNode.id,
            field: 'dieu_kien',
            newVal: newCond
          }
        };
      }
    }

    const zeroMatch = stderr.match(/ZeroDivisionError:\s*division by zero/i);
    if (zeroMatch) {
      return {
        tieuDe: `Lỗi chia cho số 0 (ZeroDivisionError)`,
        moTaLoi: `Trong toán học và lập trình, không thể thực hiện phép chia với mẫu số bằng 0.`,
        nguyenNhan: `ZeroDivisionError: division by zero`,
        cachSua: `Kiểm tra điều kiện mẫu số khác 0 trước khi thực hiện phép chia.`,
        theLoiId: null,
        patch: null
      };
    }

    const indexMatch = stderr.match(/IndexError:\s*list index out of range/i);
    if (indexMatch) {
      return {
        tieuDe: `Vượt quá giới hạn phần tử của danh sách (IndexError)`,
        moTaLoi: `Bạn đang cố lấy một phần tử ở vị trí không tồn tại trong danh sách.`,
        nguyenNhan: `IndexError: list index out of range`,
        cachSua: `Thêm thẻ 'Nếu len(ds) == 0' để xử lý trường hợp danh sách rỗng trước.`,
        theLoiId: null,
        patch: null
      };
    }

    return null;
  }

  function khamBenhToanDien(treeNodes) {
    const diagnoses = [];
    if (!treeNodes || treeNodes.length === 0) return diagnoses;

    function checkIfConditions(nodes) {
      nodes.forEach(n => {
        if (n.ma === 'neu' && n.o && n.o.dieu_kien) {
          if (/(?<![=<>!])=(?!=)/.test(n.o.dieu_kien)) {
            const fixedCond = n.o.dieu_kien.replace(/(?<![=<>!])=(?!=)/g, '==');
            diagnoses.push({
              id: 'diag_assign_in_if_' + n.id,
              mucDo: 'danger',
              tieuDe: `Thẻ [Nếu]: Dùng nhầm dấu gán '=' trong điều kiện`,
              moTa: `Điều kiện '${n.o.dieu_kien}' đang dùng dấu gán '='. Python yêu cầu so sánh bằng phải là '=='.`,
              nguyenNhan: `if ${n.o.dieu_kien}:`,
              cachSua: `Sửa thành: if ${fixedCond}:`,
              theLoiId: n.id,
              patch: {
                type: 'replace_field',
                nodeId: n.id,
                field: 'dieu_kien',
                newVal: fixedCond
              }
            });
          }
        }
        if (n.than && n.than.length) checkIfConditions(n.than);
      });
    }
    checkIfConditions(treeNodes);

    treeNodes.forEach(n => {
      if (n.ma === 'ham') {
        const fnName = (n.o && n.o.ten_ham) || 'ham';
        const hasReturn = (n.than || []).some(c => c.ma === 'tra_ve');
        const hasBody = (n.than && n.than.length > 0);
        if (hasBody && !hasReturn) {
          diagnoses.push({
            id: 'diag_missing_return_' + n.id,
            mucDo: 'warning',
            tieuDe: `Hàm '${fnName}' chưa có thẻ [Trả về] (return)`,
            moTa: `Hàm có các câu lệnh tính toán nhưng chưa trả kết quả về cho nơi gọi. Nếu không return, hàm sẽ mặc định trả về None.`,
            nguyenNhan: `def ${fnName}(...): (thiếu return)`,
            cachSua: `Thêm thẻ [Trả về] vào cuối hàm.`,
            theLoiId: n.id,
            patch: {
              type: 'insert_child',
              parentId: n.id,
              node: {
                id: `the_tra_ve_${++state.nodeIdCounter}`,
                ma: 'tra_ve',
                o: { gia_tri: 'ket_qua' },
                than: []
              }
            }
          });
        }
      }
    });

    function checkWhileLoops(nodes) {
      nodes.forEach(n => {
        if (n.ma === 'lap_khi' && n.o && n.o.dieu_kien) {
          const cond = n.o.dieu_kien.trim();
          const varMatch = cond.match(new RegExp(`^([\\p{L}_][\\p{L}\\p{N}\\p{M}_]*)\\s*(<|<=|>|>=|!=|==)`, 'u'));
          if (varMatch) {
            const loopVar = varMatch[1];
            const hasUpdate = (n.than || []).some(c => c.ma === 'gan' && c.o && c.o.ten_bien === loopVar);
            if (!hasUpdate) {
              diagnoses.push({
                id: 'diag_infinite_while_' + n.id,
                mucDo: 'warning',
                tieuDe: `Nguy cơ lặp vô tận trong thẻ [Lặp khi]`,
                moTa: `Biến điều kiện '${loopVar}' không thấy được thay đổi giá trị bên trong thân vòng lặp, có thể gây treo chương trình.`,
                nguyenNhan: `while ${cond}: (biến ${loopVar} không đổi)`,
                cachSua: `Thêm bước tăng biến '${loopVar} = ${loopVar} + 1' vào cuối vòng lặp.`,
                theLoiId: n.id,
                patch: {
                  type: 'insert_child',
                  parentId: n.id,
                  node: {
                    id: `the_gan_${++state.nodeIdCounter}`,
                    ma: 'gan',
                    o: { ten_bien: loopVar, gia_tri: `${loopVar} + 1` },
                    than: []
                  }
                }
              });
            }
          }
        }
        if (n.than && n.than.length) checkWhileLoops(n.than);
      });
    }
    checkWhileLoops(treeNodes);

    return diagnoses;
  }

  function thucHienAutoFix(patch) {
    if (!patch) return;

    if (patch.type === 'replace_field') {
      const boc = timTheTheoId(state.tree, patch.nodeId);
      if (boc && boc.node && boc.node.o) {
        boc.node.o[patch.field] = patch.newVal;
      }
    } else if (patch.type === 'insert_before') {
      if (patch.targetId) {
        const boc = timTheTheoId(state.tree, patch.targetId);
        if (boc) {
          boc.dsCha.splice(boc.chiSo, 0, patch.node);
        } else {
          state.tree.unshift(patch.node);
        }
      } else {
        state.tree.unshift(patch.node);
      }
    } else if (patch.type === 'insert_child') {
      const boc = timTheTheoId(state.tree, patch.parentId);
      if (boc && boc.node) {
        boc.node.than = boc.node.than || [];
        boc.node.than.push(patch.node);
      }
    }

    onTreeChanged();

    const modId = patch.nodeId || (patch.node && patch.node.id);
    if (modId) {
      setTimeout(() => {
        const el = document.getElementById(`node_${modId}`);
        if (el) {
          el.classList.add('card-autofix-highlight');
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          setTimeout(() => el.classList.remove('card-autofix-highlight'), 2500);
        }
      }, 100);
    }

    const banner = document.getElementById('terminalDoctorBanner');
    if (banner) banner.style.display = 'none';

    chayKhamBenhVaHienThi();

    baoNhanh('✨ Bác Sĩ AI: Đã tự động sửa thẻ thành công!');
  }

  function chayKhamBenhVaHienThi() {
    const box = document.getElementById('aiDoctorBox');
    if (!box) return;

    const diagnoses = khamBenhToanDien(state.tree);
    if (diagnoses.length === 0) {
      // KHÔNG ĐƯỢC TUYÊN BỐ "100% HEALTHY" KHI BỘ KIỂM KIA ĐANG BÁO LỖI.
      //
      // 30/08/2026. Đo bằng cách tự bấm: thêm một thẻ `Nếu` điều kiện rỗng,
      // rồi bấm "Bác Sĩ Khám Bệnh". Màn hình hiện ĐỒNG THỜI:
      //
      //     2 ĐỎ (Lỗi)                          <- ô đếm, ĐÚNG
      //     🔴 Thẻ 'Nếu' có thân nhưng chưa chứa lệnh nào bên trong
      //     🔴 Biến 'x' trong điều kiện 'Nếu' chưa được gán
      //     "Mã nguồn khoẻ mạnh! ... không phát hiện lỗi logic nào"
      //     "✓ 100% HEALTHY"                    <- SAI, ngay dưới ô đếm
      //
      // Nguyên nhân KHÔNG phải bảng cũ hay chuỗi cứng. Có HAI bộ chẩn đoán:
      //
      //     TheValidator.kiemTraCayThe   18 luật  -> ô đếm và danh sách đỏ
      //     khamBenhToanDien             nhỏ hơn  -> ô "Bác Sĩ AI"
      //
      // Hai phạm vi khác nhau là thiết kế hợp lý — bộ nhỏ chuyên bắt `=` thay
      // vì `==` và biết TỰ SỬA. Lỗi nằm ở CÂU CHỮ: "không phát hiện lỗi logic
      // nào" và "100% HEALTHY" là lời khẳng định về CẢ chương trình, trong khi
      // hàm này chỉ khám được một góc.
      //
      // Đúng họ bệnh "nhãn nói sai việc" (CLAUDE.md §4) — loại mà máy khó bắt
      // và phải tự bấm mới thấy. Nay câu chữ nói đúng phạm vi của nó, và khi
      // bộ kia có lỗi thì ô này KHÔNG được sơn xanh.
      const cd = state.diagnostics || {};
      const soDoKia = cd.so_loi_do || 0;
      const soVangKia = cd.so_canh_bao_vang || 0;
      const sach = soDoKia === 0 && soVangKia === 0;

      const mau = sach ? '#34D399' : 'var(--color-warn-vang)';
      const nen = sach ? 'rgba(16, 185, 129, 0.1)' : 'rgba(234, 179, 8, 0.10)';
      const vien = sach ? 'rgba(16, 185, 129, 0.3)' : 'rgba(234, 179, 8, 0.35)';
      const tieuDe = sach
        ? 'Mã nguồn khoẻ mạnh!'
        : 'Bác sĩ không tìm thấy lỗi NÓ KHÁM ĐƯỢC';
      const phu = sach
        ? 'Bác sĩ AI không phát hiện lỗi logic nào trên các thẻ hiện tại.'
        : `Nhưng bộ kiểm tra thẻ đang báo ${soDoKia} lỗi và ${soVangKia} cảnh `
          + 'báo — xem danh sách bên dưới. Bác sĩ chỉ khám một số lỗi logic '
          + 'quen thuộc, không thay cho bộ kiểm tra.';
      const nhan = sach ? '✓ 100% HEALTHY' : `⚠ CÒN ${soDoKia + soVangKia} MỤC`;

      box.style.display = 'block';
      box.innerHTML = `
        <div style="background: ${nen}; border: 1px solid ${vien}; border-radius: 8px; padding: 12px 14px; display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">🩺</span>
            <div>
              <div style="font-size: 12.5px; font-weight: 700; color: ${mau};">${tieuDe}</div>
              <div style="font-size: 11px; color: var(--text-secondary);">${phu}</div>
            </div>
          </div>
          <span style="color: ${mau}; font-weight: 800;">${nhan}</span>
        </div>
      `;
      return;
    }

    box.style.display = 'block';
    let html = '';
    diagnoses.forEach(diag => {
      html += `
        <div class="doctor-diagnosis-card ${diag.mucDo}">
          <div class="doctor-card-top">
            <span class="doctor-card-title">
              <span>${diag.mucDo === 'danger' ? '🔴' : '🟡'}</span>
              ${escapeHtml(diag.tieuDe)}
            </span>
          </div>
          <div class="doctor-card-body">
            <div>${escapeHtml(diag.moTa)}</div>
            <div class="doctor-cause">${escapeHtml(diag.nguyenNhan)}</div>
          </div>
          <div class="doctor-prescription">
            <span class="doctor-advice">💡 ${escapeHtml(diag.cachSua)}</span>
            ${diag.patch ? `<button class="btn-autofix" data-diagid="${diag.id}">✨ Sửa Thẻ Này</button>` : ''}
          </div>
        </div>
      `;
    });

    box.innerHTML = html;

    box.querySelectorAll('.btn-autofix').forEach(btn => {
      btn.addEventListener('click', () => {
        const diagId = btn.getAttribute('data-diagid');
        const d = diagnoses.find(x => x.id === diagId);
        if (d && d.patch) {
          thucHienAutoFix(d.patch);
        }
      });
    });
  }

  // ==========================================================================
  // BỘ ĐÓNG GÓI DỰ ÁN HOÀN CHỈNH & XUẤT FILE ZIP (1-CLICK PROJECT PACKAGER)
  // ==========================================================================
  const crcTable = (() => {
    let c;
    const table = [];
    for (let n = 0; n < 256; n++) {
      c = n;
      for (let k = 0; k < 8; k++) {
        c = ((c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1));
      }
      table[n] = c >>> 0;
    }
    return table;
  })();

  function tinhCRC32(uint8Arr) {
    let crc = 0 ^ (-1);
    for (let i = 0; i < uint8Arr.length; i++) {
      crc = (crc >>> 8) ^ crcTable[(crc ^ uint8Arr[i]) & 0xFF];
    }
    return (crc ^ (-1)) >>> 0;
  }

  function taoFileZip(fileList) {
    const encoder = new TextEncoder();
    const fileEntries = [];

    fileList.forEach(f => {
      const nameBytes = encoder.encode(f.name);
      const dataBytes = typeof f.content === 'string' ? encoder.encode(f.content) : (f.content instanceof Uint8Array ? f.content : new Uint8Array(f.content));
      const crc = tinhCRC32(dataBytes);

      fileEntries.push({
        nameBytes,
        dataBytes,
        crc,
        offset: 0
      });
    });

    let currentOffset = 0;
    const parts = [];

    fileEntries.forEach(entry => {
      entry.offset = currentOffset;
      const header = new Uint8Array(30);
      const view = new DataView(header.buffer);

      view.setUint32(0, 0x04034b50, true);
      view.setUint16(4, 10, true);
      view.setUint16(6, 0, true);
      view.setUint16(8, 0, true);
      view.setUint16(10, 0, true);
      view.setUint16(12, 0, true);
      view.setUint32(14, entry.crc, true);
      view.setUint32(18, entry.dataBytes.length, true);
      view.setUint32(22, entry.dataBytes.length, true);
      view.setUint16(26, entry.nameBytes.length, true);
      view.setUint16(28, 0, true);

      parts.push(header);
      parts.push(entry.nameBytes);
      parts.push(entry.dataBytes);

      currentOffset += header.length + entry.nameBytes.length + entry.dataBytes.length;
    });

    const centralDirOffset = currentOffset;
    let centralDirSize = 0;

    fileEntries.forEach(entry => {
      const cdHeader = new Uint8Array(46);
      const view = new DataView(cdHeader.buffer);

      view.setUint32(0, 0x02014b50, true);
      view.setUint16(4, 10, true);
      view.setUint16(6, 10, true);
      view.setUint16(8, 0, true);
      view.setUint16(10, 0, true);
      view.setUint16(12, 0, true);
      view.setUint14 ? null : null;
      view.setUint32(16, entry.crc, true);
      view.setUint32(20, entry.dataBytes.length, true);
      view.setUint32(24, entry.dataBytes.length, true);
      view.setUint16(28, entry.nameBytes.length, true);
      view.setUint16(30, 0, true);
      view.setUint16(32, 0, true);
      view.setUint16(34, 0, true);
      view.setUint16(36, 0, true);
      view.setUint32(38, 0, true);
      view.setUint32(42, entry.offset, true);

      parts.push(cdHeader);
      parts.push(entry.nameBytes);

      centralDirSize += cdHeader.length + entry.nameBytes.length;
    });

    const eocd = new Uint8Array(22);
    const eocdView = new DataView(eocd.buffer);

    eocdView.setUint32(0, 0x06054b50, true);
    eocdView.setUint16(4, 0, true);
    eocdView.setUint16(6, 0, true);
    eocdView.setUint16(8, fileEntries.length, true);
    eocdView.setUint16(10, fileEntries.length, true);
    eocdView.setUint32(12, centralDirSize, true);
    eocdView.setUint32(16, centralDirOffset, true);
    eocdView.setUint16(20, 0, true);

    parts.push(eocd);

    return new Blob(parts, { type: 'application/zip' });
  }

  function sinhRequirementsTxt(codeText) {
    const reqs = [];
    const code = codeText || '';

    if (/pandas|import\s+pandas|from\s+pandas/i.test(code)) reqs.push('pandas>=2.0.0');
    if (/numpy|import\s+numpy|from\s+numpy/i.test(code)) reqs.push('numpy>=1.24.0');
    if (/requests|import\s+requests/i.test(code)) reqs.push('requests>=2.31.0');
    if (/bs4|BeautifulSoup/i.test(code)) reqs.push('beautifulsoup4>=4.12.0');
    if (/pygame|import\s+pygame/i.test(code)) reqs.push('pygame>=2.5.0');
    if (/genai|google\.generativeai/i.test(code)) reqs.push('google-generativeai>=0.4.0');

    if (reqs.length === 0) {
      return '# Chuẩn Python Standard Library (Không cần cài thêm thư viện ngoại vi)\n';
    }
    return reqs.join('\n') + '\n';
  }

  function sinhReadmeMd(meta) {
    return `# ${meta.tenDuAn || 'Dự Án Lập Trình Python AURA'}

**Tác giả:** ${meta.tacGia || 'AURA Student'}  
**Ngày tạo:** ${new Date().toLocaleDateString('vi-VN')}  
**Mô tả:** ${meta.moTa || 'Chương trình được phát triển trên Nền tảng Thẻ AURA v1.'}

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Chương Trình

### Cách 1: Chạy Nhanh 1-Click (Khuyên Dùng)
- **Trên Windows**: Nhấp đúp vào tệp \`run.bat\` để tự động cài đặt thư viện và khởi chạy.
- **Trên macOS / Linux**: Mở Terminal và chạy:
  \`\`\`bash
  bash run.sh
  \`\`\`

### Cách 2: Chạy Thủ Công Bằng Dòng Lệnh (Terminal)
1. Cài đặt các thư viện phụ thuộc:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`
2. Thực thi chương trình:
   \`\`\`bash
   python main.py
   \`\`\`

---

## 📁 Cấu Trúc Gói Dự Án

- \`main.py\`: Mã nguồn Python chính của ứng dụng.
- \`project_tree.json\`: Cây thẻ cấu trúc gốc (kéo thả vào App Thẻ AURA để mở lại).
- \`flowchart.svg\`: Sơ đồ khối thuật toán vector trực quan.
- \`requirements.txt\`: Danh sách thư viện phụ thuộc.
- \`run.bat\` / \`run.sh\`: Script khởi chạy tự động.
`;
  }

  function sinhRunBat() {
    return `@echo off
chcp 65001 > nul
echo ===================================================
echo   DANG KHOI CHAY DU AN AURA
echo ===================================================
if exist requirements.txt (
  echo [*] Kiem tra va cai dat thu vien phu thuoc...
  pip install -r requirements.txt
)
echo.
echo [*] Dang thuc thi main.py...
python main.py
echo.
echo [✓] Chuong trinh da ket thuc.
pause
`;
  }

  function sinhRunSh() {
    return `#!/usr/bin/env bash
echo "==================================================="
echo "  DANG KHOI CHAY DU AN AURA"
echo "==================================================="
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
echo ""
echo "[*] Dang thuc thi main.py..."
python3 main.py
`;
  }

  function moModalDongGoi() {
    const modal = document.getElementById('packageModal');
    if (!modal) return;

    const nameInput = document.getElementById('pkgProjectName');
    const descInput = document.getElementById('pkgDescription');

    if (nameInput) {
      nameInput.value = (state.activeFileName || 'my_aura_project').replace(/\.[^/.]+$/, "").replace(/\s+/g, '_');
    }
    if (descInput && !descInput.value) {
      descInput.value = 'Chương trình được tạo bằng App Thẻ AURA v1.';
    }

    modal.style.display = 'flex';
  }

  function dongModalDongGoi() {
    const modal = document.getElementById('packageModal');
    if (modal) modal.style.display = 'none';
  }

  function thucHienDongGoiZip() {
    const nameInput = document.getElementById('pkgProjectName');
    const authorInput = document.getElementById('pkgAuthor');
    const descInput = document.getElementById('pkgDescription');

    const projectName = (nameInput && nameInput.value.trim()) || 'aura_project';
    const author = (authorInput && authorInput.value.trim()) || 'AURA Student';
    const desc = (descInput && descInput.value.trim()) || 'Chương trình lập trình bằng thẻ AURA.';

    const code = TheValidator.sinhMaPython(state.tree);
    const files = [];

    // 1. main.py
    files.push({ name: 'main.py', content: code || '# AURA Program\nprint("Hello World!")\n' });

    // 2. project_tree.json
    if (document.getElementById('chkPkgTreeJson')?.checked) {
      files.push({ name: 'project_tree.json', content: JSON.stringify(state.tree, null, 2) });
    }

    // 3. flowchart.svg
    if (document.getElementById('chkPkgSvg')?.checked) {
      const svg = sinhSVGSoDoKhoi(state.tree);
      files.push({ name: 'flowchart.svg', content: svg });
    }

    // 4. requirements.txt
    if (document.getElementById('chkPkgReqs')?.checked) {
      files.push({ name: 'requirements.txt', content: sinhRequirementsTxt(code) });
    }

    // 5. README.md
    if (document.getElementById('chkPkgReadme')?.checked) {
      files.push({
        name: 'README.md',
        content: sinhReadmeMd({ tenDuAn: projectName, tacGia: author, moTa: desc })
      });
    }

    // 6. run.bat & run.sh
    if (document.getElementById('chkPkgScripts')?.checked) {
      files.push({ name: 'run.bat', content: sinhRunBat() });
      files.push({ name: 'run.sh', content: sinhRunSh() });
    }

    try {
      const zipBlob = taoFileZip(files);
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${projectName}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      dongModalDongGoi();
      baoNhanh(`🎉 Đã đóng gói và tải về thành công: ${projectName}.zip!`);
    } catch (err) {
      baoNhanh(`Lỗi đóng gói: ${err.message}`);
    }
  }

  function setupPackageControls() {
    const btnOpen = document.getElementById('btnPackage');
    const btnClose = document.getElementById('btnClosePackage');
    const btnCancel = document.getElementById('btnCancelPackage');
    const btnConfirm = document.getElementById('btnConfirmPackage');

    if (btnOpen) btnOpen.addEventListener('click', moModalDongGoi);
    if (btnClose) btnClose.addEventListener('click', dongModalDongGoi);
    if (btnCancel) btnCancel.addEventListener('click', dongModalDongGoi);
    if (btnConfirm) btnConfirm.addEventListener('click', thucHienDongGoiZip);
  }

  // ==========================================================================
  // CHẾ ĐỘ TRÌNH CHIẾU GIẢNG DẠY & BÚT VẼ CHÚ THÍCH (PRESENTATION & WHITEBOARD)
  // ==========================================================================
  const presState = {
    isActive: false,
    currentTool: 'mouse',
    currentColor: '#EF4444',
    isDrawing: false,
    lastX: 0,
    lastY: 0,
    laserX: -100,
    laserY: -100
  };

  let presCanvas = null;
  let presCtx = null;

  function initPresentationCanvas() {
    presCanvas = document.getElementById('annotationCanvasOverlay');
    if (!presCanvas) return;
    presCtx = presCanvas.getContext('2d');

    function resizeCanvas() {
      if (!presCanvas) return;
      const dpr = window.devicePixelRatio || 1;
      presCanvas.width = window.innerWidth * dpr;
      presCanvas.height = window.innerHeight * dpr;
      presCanvas.style.width = window.innerWidth + 'px';
      presCanvas.style.height = window.innerHeight + 'px';
      presCtx.scale(dpr, dpr);
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    presCanvas.addEventListener('mousedown', startPresDraw);
    presCanvas.addEventListener('mousemove', presDraw);
    window.addEventListener('mouseup', stopPresDraw);

    presCanvas.addEventListener('touchstart', (e) => {
      if (e.touches.length > 0) {
        const t = e.touches[0];
        startPresDraw({ clientX: t.clientX, clientY: t.clientY });
      }
    });
    presCanvas.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) {
        const t = e.touches[0];
        presDraw({ clientX: t.clientX, clientY: t.clientY });
      }
    });
    window.addEventListener('touchend', stopPresDraw);
  }

  function startPresDraw(e) {
    if (!presState.isActive || presState.currentTool === 'mouse') return;
    presState.isDrawing = true;
    presState.lastX = e.clientX;
    presState.lastY = e.clientY;

    if (presState.currentTool === 'pen' || presState.currentTool === 'highlighter' || presState.currentTool === 'eraser') {
      presCtx.beginPath();
      presCtx.moveTo(e.clientX, e.clientY);
    }
  }

  function presDraw(e) {
    if (!presState.isActive) return;

    if (presState.currentTool === 'laser') {
      presState.laserX = e.clientX;
      presState.laserY = e.clientY;
      veConTroLaser();
      return;
    }

    if (!presState.isDrawing) return;

    const x = e.clientX;
    const y = e.clientY;

    if (presState.currentTool === 'pen') {
      presCtx.globalCompositeOperation = 'source-over';
      presCtx.strokeStyle = presState.currentColor;
      presCtx.lineWidth = 3.5;
      presCtx.lineCap = 'round';
      presCtx.lineJoin = 'round';
      presCtx.globalAlpha = 1.0;
      presCtx.lineTo(x, y);
      presCtx.stroke();
    } else if (presState.currentTool === 'highlighter') {
      presCtx.globalCompositeOperation = 'source-over';
      presCtx.strokeStyle = presState.currentColor;
      presCtx.lineWidth = 22;
      presCtx.lineCap = 'round';
      presCtx.lineJoin = 'round';
      presCtx.globalAlpha = 0.35;
      presCtx.lineTo(x, y);
      presCtx.stroke();
    } else if (presState.currentTool === 'eraser') {
      presCtx.globalCompositeOperation = 'destination-out';
      // 30/08/2026 — nhanh nay TUNG khong dat lai globalAlpha nen no thua ke 0.35
      // cua da quang. Do (tong alpha vung net but 448.795):
      //   but -> tay              448.795 -> 0        (1 luot, sach)
      //   but -> da quang -> tay  448.795 -> 25.192   (con 5,6% sau 1 luot)
      //                                    -> 1.978   (sau 5 luot)
      // Tren may chieu no hien ra thanh vet mo chui khong het.
      presCtx.globalAlpha = 1.0;
      presCtx.lineWidth = 30;
      presCtx.lineCap = 'round';
      presCtx.lineJoin = 'round';
      presCtx.lineTo(x, y);
      presCtx.stroke();
    }

    presState.lastX = x;
    presState.lastY = y;
  }

  function stopPresDraw() {
    if (!presState.isDrawing) return;
    presState.isDrawing = false;
    if (presCtx) presCtx.closePath();
  }

  function veConTroLaser() {
    if (!presCtx || presState.currentTool !== 'laser') return;
    const x = presState.laserX;
    const y = presState.laserY;

    presCtx.save();
    presCtx.globalCompositeOperation = 'source-over';
    presCtx.beginPath();
    presCtx.arc(x, y, 6, 0, Math.PI * 2);
    presCtx.fillStyle = '#EF4444';
    presCtx.shadowColor = '#EF4444';
    presCtx.shadowBlur = 15;
    presCtx.fill();
    presCtx.restore();
  }

  function xoaNetVe() {
    if (!presCtx || !presCanvas) return;
    presCtx.clearRect(0, 0, presCanvas.width, presCanvas.height);
  }

  function datCongCuTrinhChieu(tool) {
    presState.currentTool = tool;
    const overlay = document.getElementById('annotationCanvasOverlay');

    document.querySelectorAll('.pres-tool-btn').forEach(btn => btn.classList.remove('active'));
    if (tool === 'mouse') document.getElementById('btnPresMouse')?.classList.add('active');
    else if (tool === 'pen') document.getElementById('btnPresPen')?.classList.add('active');
    else if (tool === 'highlighter') document.getElementById('btnPresHighlighter')?.classList.add('active');
    else if (tool === 'laser') document.getElementById('btnPresLaser')?.classList.add('active');
    else if (tool === 'eraser') document.getElementById('btnPresEraser')?.classList.add('active');

    if (overlay) {
      overlay.className = 'annotation-canvas-overlay';
      if (tool === 'mouse') {
        overlay.classList.remove('drawing-mode', 'laser-mode');
      } else if (tool === 'laser') {
        overlay.classList.add('laser-mode');
      } else {
        overlay.classList.add('drawing-mode');
      }
    }
  }

  function batCheDoTrinhChieu() {
    presState.isActive = true;
    document.body.classList.add('presentation-mode-active');
    const overlay = document.getElementById('annotationCanvasOverlay');
    const controlBar = document.getElementById('presentationControlBar');

    if (overlay) overlay.style.display = 'block';
    if (controlBar) controlBar.style.display = 'flex';

    datCongCuTrinhChieu('mouse');

    try {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    } catch (_) {}

    baoNhanh('🖥️ Đã bật Chế độ Trình Chiếu! (Nhấn Esc để thoát, D để vẽ)');
  }

  function tatCheDoTrinhChieu() {
    presState.isActive = false;
    document.body.classList.remove('presentation-mode-active');
    const overlay = document.getElementById('annotationCanvasOverlay');
    const controlBar = document.getElementById('presentationControlBar');

    if (overlay) overlay.style.display = 'none';
    if (controlBar) controlBar.style.display = 'none';

    xoaNetVe();

    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    } catch (_) {}

    baoNhanh('Đã thoát Chế độ Trình Chiếu.');
  }

  function setupPresentationControls() {
    initPresentationCanvas();

    const btnOpen = document.getElementById('btnPresentation');
    const btnExit = document.getElementById('btnPresExit');
    const btnRun = document.getElementById('btnPresRun');
    const btnStep = document.getElementById('btnPresStep');
    const btnClear = document.getElementById('btnPresClearDraw');

    if (btnOpen) btnOpen.addEventListener('click', batCheDoTrinhChieu);
    if (btnExit) btnExit.addEventListener('click', tatCheDoTrinhChieu);
    if (btnRun) btnRun.addEventListener('click', runProgram);
    if (btnStep) {
      btnStep.addEventListener('click', () => {
        if (!debuggerState.isActive) {
          batDauGoLoi();
        } else {
          // 30/08/2026 — TỪNG gọi `buocTiepTheo()`, một cái tên KHÔNG TỒN TẠI
          // ở đâu trong tệp này. Hàm thật tên `buocTiep` (không có "Theo"), và
          // btnDebugStepNext ở thanh gỡ lỗi thường vẫn gọi đúng tên ấy.
          // Đo: vào Trình Chiếu, bấm "⏭ Bước" lần đầu -> mở gỡ lỗi (đúng);
          // bấm lần hai -> "Uncaught ReferenceError: buocTiepTheo is not
          // defined", bộ đếm đứng yên ở "Bước 1 / 3".
          // Không test nào bắt được: nút CÓ handler, và lỗi chỉ nổ ở NHÁNH
          // else — nhánh chỉ chạy sau khi gỡ lỗi đã bật.
          buocTiep();
        }
      });
    }
    if (btnClear) btnClear.addEventListener('click', xoaNetVe);

    document.getElementById('btnPresMouse')?.addEventListener('click', () => datCongCuTrinhChieu('mouse'));
    document.getElementById('btnPresPen')?.addEventListener('click', () => datCongCuTrinhChieu('pen'));
    document.getElementById('btnPresHighlighter')?.addEventListener('click', () => datCongCuTrinhChieu('highlighter'));
    document.getElementById('btnPresLaser')?.addEventListener('click', () => datCongCuTrinhChieu('laser'));
    document.getElementById('btnPresEraser')?.addEventListener('click', () => datCongCuTrinhChieu('eraser'));

    document.querySelectorAll('.pres-color-palette .color-dot').forEach(dot => {
      dot.addEventListener('click', () => {
        document.querySelectorAll('.pres-color-palette .color-dot').forEach(d => d.classList.remove('active'));
        dot.classList.add('active');
        presState.currentColor = dot.dataset.color || '#EF4444';
        if (presState.currentTool === 'mouse' || presState.currentTool === 'eraser') {
          datCongCuTrinhChieu('pen');
        }
      });
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && presState.isActive) {
        tatCheDoTrinhChieu();
      } else if (e.altKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        if (presState.isActive) tatCheDoTrinhChieu();
        else batCheDoTrinhChieu();
      } else if (presState.isActive && !e.ctrlKey && !e.metaKey && !e.altKey) {
        if (e.key === 'd' || e.key === 'D') {
          datCongCuTrinhChieu(presState.currentTool === 'pen' ? 'mouse' : 'pen');
        } else if (e.key === 'h' || e.key === 'H') {
          datCongCuTrinhChieu('highlighter');
        } else if (e.key === 'l' || e.key === 'L') {
          datCongCuTrinhChieu('laser');
        } else if (e.key === 'e' || e.key === 'E') {
          datCongCuTrinhChieu('eraser');
        } else if (e.key === 'c' || e.key === 'C') {
          xoaNetVe();
        }
      }
    });
  }

  // ==========================================================================
  // NHỚ TỆP ĐANG MỞ — thêm 26/08/2026
  // ==========================================================================
  //
  // Trước hôm nay, mở app lên LUÔN thấy bài mẫu "1. Hàm cộng hai số" — mã của
  // người khác, không nằm trong dự án của người dùng. Với người mở app trong
  // thư mục bài tập của mình, đó là câu chào bằng đồ của người lạ.
  //
  // Chua hơn: app ĐÃ CÓ SẴN màn hình chào cho canvas trống
  // (`#emptyCanvasGuide` — "Vùng soạn thảo đang trống", kèm nút "Thử bài
  // mẫu"), nhưng lúc khởi động mã nhét thẳng bài mẫu vào `state.tree` nên màn
  // hình ấy CHƯA TỪNG HIỆN.
  //
  // Nay: lần đầu vào một dự án thì vẫn bài mẫu (nó dạy được, và nút trong màn
  // hình chào cũng chỉ tới nó). Từ lần thứ hai thì mở lại tệp đang làm dở —
  // đúng lối mọi trình soạn thảo.
  //
  // Khoá theo TÊN DỰ ÁN, không dùng chung một khoá: hai dự án khác nhau thì
  // tệp đang làm dở cũng khác. Dùng chung thì mở dự án B lại đòi tệp của dự
  // án A và nhận 400.
  function khoaNhoTep() {
    return 'aura_tep_dang_mo:' + (state.tenDuAn || '(khong ro)');
  }

  function nhoTepDangMo(duongDan) {
    try {
      if (duongDan) localStorage.setItem(khoaNhoTep(), duongDan);
      else localStorage.removeItem(khoaNhoTep());
    } catch (_) {
      // Trình duyệt chặn lưu trữ (cửa sổ ẩn danh, chặn dữ liệu trang) thì bỏ
      // qua — mất tiện nghi, không mất dữ liệu.
    }
  }

  async function moLaiTepLanTruoc() {
    let duongDan = null;
    try { duongDan = localStorage.getItem(khoaNhoTep()); } catch (_) { return false; }
    if (!duongDan) return false;
    // Tệp có thể đã bị xoá hay đổi tên từ lần trước. `openPyFile` tự báo lỗi
    // qua ô báo nhẹ; ở đây chỉ cần quên nó đi để lần sau khỏi đòi lại.
    const truoc = state.activeFilePath;
    await openPyFile(duongDan);
    if (state.activeFilePath === truoc) { nhoTepDangMo(null); return false; }
    return true;
  }

  // ==========================================================================
  // BAO SOM: TEP MO TU DIA CHI SUA DUOC NOI DUNG O
  // ==========================================================================
  //
  // 26/08/2026. Nguoi dung keo mot the moi vao mot tep dang mo, tiep tuc lam
  // them muoi phut, roi bam Ctrl+S va nhan:
  //
  //   422: Ban public v1 chi ho tro sua o cua the da co;
  //        them/xoa/doi thu tu/doi loai chua duoc phep
  //
  // Bao o BUOC CUOI la bao qua muon. Nay bao ngay luc the dau tien duoc
  // them, kem loi thoat ("Luu thanh tep moi") chu khong chi bao la khong duoc.
  //
  // VI SAO HANG RAO AY DUNG — da do, khong phai doan. Bo ghi sua TAI CHO tren
  // CST cua tep goc, nen the moi khong co cho tuong ung de ghi vao. Duong con
  // lai la sinh lai ca tep tu cay the, va do tren 33 tep that:
  //
  //   ma nguon AURA (phuc tap)   26/28 tep MAT NOI DUNG THAT khi sinh lai
  //                              (chu ky ham nhieu dong bi gop, thut le
  //                               docstring doi)
  //   tep kieu nguoi moi hoc      5/5 chi khac DONG TRONG, 0 mat noi dung
  //
  // Nen hang rao dung voi tep phuc tap. Voi tep don gian thi mo duoc, nhung
  // phai vá `sinh_ma_python` giu dong trong + xuong dong cuoi tep truoc da —
  // viec do nam trong `core/the_v1.py`, dang co phep do chay tren no.
  //
  // Truoc mat: noi that, noi som, va chi duong.

  /** Chu ky CAU TRUC cua cay the: chi loai the va hinh long nhau, khong o. */
  function chuKyCauTruc(ds) {
    return (ds || []).map(
      t => t.ma + '(' + chuKyCauTruc(t.than) + ')').join(',');
  }

  let daBaoCauTruc = false;

  /** Bao mot lan khi cau truc lech khoi luc mo tep. */
  function kiemCauTrucDoi() {
    // 26/08, BUOI CHIEU: chi bao khi tep NAY that su khong cho them/bot the.
    //
    // Sang nay bao cho MOI tep mo tu dia, vi luc do backend tu choi het. Chieu
    // nay `sinh_ma_python` da giu dong trong + xuong dong cuoi tep, nen tep
    // bieu dien tron ven bang the thi them the LUU DUOC that — do bang API
    // song: `don_gian.py` tra 200, `chat_contract.py` van 422.
    //
    // Neu van bao thi cau canh bao sai voi dung nhung tep no can dung, va
    // nguoi dung se hoc cach lo no di. Backend noi ngay luc mo tep
    // (`them_bot_the_duoc`), tinh bang CHINH phep do dung o duong luu.
    if (state.themBotTheDuoc) return;
    if (!state.activeFilePath || !state.chuKyLucMo) return;
    const gio = chuKyCauTruc(state.tree);
    if (gio === state.chuKyLucMo) { daBaoCauTruc = false; return; }
    if (daBaoCauTruc) return;
    daBaoCauTruc = true;
    baoNhanh(
      'Tệp mở từ đĩa chỉ sửa được NỘI DUNG Ô. Thêm/bớt thẻ thì bấm ' +
      '"Lưu Tệp" rồi đổi tên để lưu thành tệp mới.', 'hong');
  }

  async function openPyFile(filePath) {
    if (!filePath || !filePath.trim()) return;
    try {
      const resp = await authFetch('/api/mo_tep', {
        method: 'POST',
        body: JSON.stringify({ duong_dan: filePath.trim() })
      });
      if (resp.ok) {
        const data = await readJsonSafely(resp);
        if (!Array.isArray(data.tree) || typeof data.duong_dan !== 'string' ||
            !/^[0-9a-f]{64}$/.test(data.sha256 || '')) {
          throw new Error('Phản hồi mở tệp không hợp lệ');
        }
        // Mở tệp = MỞ MỘT TAB. Đã mở rồi thì chuyển sang, không mở bản
        // thứ hai — hai tab cùng một tệp là hai cây thẻ ghi đè nhau lúc lưu.
        nhoTepDangMo(data.duong_dan);
        // Chup chu ky cau truc NGAY LUC MO, de biet nguoi dung co them/bot
        // the hay khong. So bang chu ky chu khong dem so the: doi mot the
        // `neu` thanh `lap` khong lam so the doi, nhung backend van tu choi.
        state.chuKyLucMo = chuKyCauTruc(data.tree);
        // Mặc định COI LÀ KHÔNG ĐƯỢC khi máy chủ không nói gì (bản cũ, hay
        // trường bị mất): thà báo thừa một câu còn hơn để người dùng dựng cả
        // chương trình rồi mới biết không lưu được. Fail-closed.
        state.themBotTheDuoc = data.them_bot_the_duoc === true;
        daBaoCauTruc = false;
        moTrongTab({ duong_dan: data.duong_dan, ten_tep: data.ten_tep,
                     tree: data.tree, sha256: data.sha256 });
        xoaLichSu();
        document.getElementById('currentFileName').textContent = data.ten_tep;
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('openFileModal').style.display = 'none';
        // `pushHistory=false` để không đánh dấu tệp là "đã sửa" ngay khi vừa
        // mở, nhưng vẫn phải GHI MỘT MỐC GỐC: nếu không, thao tác sửa ĐẦU
        // TIÊN sau khi mở tệp trở thành bước gốc và không lùi về đâu được.
        // Đo 24/08: mở dong_ho.py (7 thẻ) rồi thêm 1 thẻ -> bấm Hoàn tác vẫn
        // là 8 thẻ, không lùi.
        onTreeChanged(false, false);
        ghiLichSu();

        const testPath = data.duong_dan.startsWith('core/')
          ? data.duong_dan.replace('core/', 'tests/test_')
          : (data.duong_dan.startsWith('tests/') ? data.duong_dan : 'tests/test_' + data.ten_tep);
        loadAvailableTests(testPath);
        yeuCauChinhCotDoc();
      } else {
        const err = await readJsonSafely(resp);
        baoNhanh(`Không mở được tệp: ${err.error}`, 'hong');
      }
    } catch (err) {
      baoNhanh(`Không nối được máy chủ khi mở tệp: ${err.message}`, 'hong');
    }
  }

  async function saveFile(filePath, saveType) {
    if (!filePath || !filePath.trim()) return;
    const target = filePath.trim();
    const sameTarget = Boolean(
      state.activeFilePath && normalizedPath(target) === normalizedPath(state.activeFilePath)
    );
    const payload = {
      duong_dan: target,
      tree: state.tree,
      kieu_luu: saveType,
      has_modifications: state.hasModifications
    };
    if (sameTarget && state.activeFileSha256) {
      payload.expected_sha256 = state.activeFileSha256;
    }
    if (state.activeFilePath && state.activeFileSha256) {
      payload.source_path = state.activeFilePath;
      payload.source_sha256 = state.activeFileSha256;
    }
    try {
      const resp = await authFetch('/api/luu_tep', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (resp.status === 409) {
        const err = await readJsonSafely(resp);
        state.hasModifications = true;
        document.getElementById('fileModifiedBadge').style.display = 'inline-block';
        const reload = confirm(
          'Tệp trên đĩa đã thay đổi bên ngoài. Tải lại sẽ bỏ các thay đổi chưa lưu trong app. ' +
          'Bạn có muốn tải lại ngay không?'
        );
        if (reload) await openPyFile(target);
        else if (err.error) console.warn(err.error);
        return;
      }
      if (resp.ok) {
        const data = await readJsonSafely(resp);
        if (typeof data.duong_dan !== 'string' || !/^[0-9a-f]{64}$/.test(data.sha256 || '')) {
          throw new Error('Máy chủ không trả SHA-256 hợp lệ sau khi lưu');
        }
        state.activeFilePath = data.duong_dan;
        state.activeFileSha256 = data.sha256;
        state.hasModifications = false;
        dongBoTabHienTai();
        veThanhTab();
        clearNodeDirtyFlags(state.tree);
        document.getElementById('currentFileName').textContent = data.duong_dan.split('/').pop().split('\\').pop();
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('saveFileModal').style.display = 'none';
        // Lưu vào tệp nào thì lần sau mở lại tệp ấy — kể cả khi vừa "lưu
        // thành tệp mới", vì đó mới là tệp người dùng đang làm.
        nhoTepDangMo(target);
        // ĐƯỜNG LƯU KHÔNG ĐI QUA `onTreeChanged`, nên phải vẽ lại thanh
        // trạng thái ở đây.
        //
        // Bắt được 26/08 bằng cách tự bấm Ctrl+S: lưu THÀNH CÔNG, tệp trên
        // đĩa đúng, `state.hasModifications` đã về `false`, dấu chấm trên tab
        // đã tắt — mà thanh trạng thái vẫn ghi "● chưa lưu". Và cờ ấy còn kéo
        // theo `beforeunload`: đóng tab sẽ bị hỏi vô cớ trong khi không còn
        // gì để mất.
        //
        // Đúng cái chú thích của chính tôi ở `veThanhTrangThai` cảnh báo:
        // cắm vào một chỗ thì sẽ có nhánh KHÔNG đi qua chỗ ấy. Viết ra rồi
        // vẫn vấp.
        // Luu duoc thi cau truc tren dia = cau truc dang xem.
        state.chuKyLucMo = chuKyCauTruc(state.tree);
        daBaoCauTruc = false;
        veThanhTrangThai();
        // Lưu được thì KHÔNG chặn màn hình: thanh trạng thái đáy đã ghi
        // "✓ đã lưu" và dấu chấm trên tab đã tắt. Một câu ngắn tự mờ là đủ.
        //
        // Chỉ hiện TÊN TỆP, không hiện đường dẫn đầy đủ: đường dẫn tuyệt đối
        // dài hơn 100 ký tự, tràn hết ô báo và chẳng nói thêm gì — người dùng
        // biết mình đang ở dự án nào rồi (thanh trạng thái ghi bên trái).
        baoNhanh(`✓ Đã lưu ${target.split('/').pop().split('\\').pop()}`);
      } else {
        const err = await readJsonSafely(resp);
        if (String(err.error || '').includes('422')) {
          // Biến câu 422 của máy chủ thành việc người dùng LÀM ĐƯỢC.
          //
          // Câu gốc — "Bản public v1 chỉ hỗ trợ sửa ô của thẻ đã có;
          // thêm/xóa/đổi thứ tự/đổi loại chưa được phép (root: số thẻ đã thay
          // đổi)" — đúng về kỹ thuật nhưng không nói người dùng phải làm gì,
          // và "Bản public v1" là chuyện nội bộ của người viết app.
          baoNhanh('Tệp này mở từ đĩa nên chỉ sửa được nội dung ô. '
                   + 'Bấm "Lưu Tệp" rồi đổi tên để lưu thành tệp mới.', 'hong');
        } else {
          baoNhanh(`Không lưu được: ${err.error}`, 'hong');
        }
      }
    } catch (err) {
      baoNhanh(`Không nối được máy chủ khi lưu: ${err.message}`, 'hong');
    }
  }

  // ==========================================================================
  // 6. MẪU BÀI, DUYỆT TỆP, MỞ TỆP & LƯU TỆP
  // ==========================================================================
  async function loadRepoFiles(dir = 'core') {
    const listContainer = document.getElementById('repoFileListContainer');
    if (!listContainer) return;
    listContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 11px; padding: 6px;">Đang tải danh sách tệp...</div>';

    try {
      // 24/08: tham số & tên trường từng viết theo API tưởng tượng, không phải
      // API thật (interface/the_api.py:396 chỉ đọc `thu_muc`, trả về `danh_sach`
      // với trường `kich_thuoc`). Hộp "Mở tệp" vì vậy LUÔN báo rỗng, mọi thư mục
      // — bắt được khi tự dùng thử, đối chiếu thẳng response JSON.
      const resp = await authFetch(`/api/tep_tin?thu_muc=${encodeURIComponent(dir)}`);
      if (resp.ok) {
        const data = await resp.json();
        const files = data.danh_sach || [];
        listContainer.innerHTML = '';
        if (files.length === 0) {
          listContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 11px; padding: 6px;">Không có tệp .py nào trong thư mục này.</div>';
          return;
        }

        const chipsWrap = document.createElement('div');
        chipsWrap.className = 'file-chips';

        files.forEach(f => {
          const chip = document.createElement('span');
          chip.className = 'chip';
          chip.dataset.path = f.duong_dan;
          chip.textContent = f.duong_dan;
          chip.title = `Mở tệp ${f.duong_dan} (${f.kich_thuoc} bytes)`;
          chip.addEventListener('click', () => {
            document.getElementById('openFilePath').value = f.duong_dan;
            openPyFile(f.duong_dan);
          });
          chipsWrap.appendChild(chip);
        });

        listContainer.appendChild(chipsWrap);
      } else {
        listContainer.innerHTML = '<div style="color: var(--color-error-do); font-size: 11px; padding: 6px;">Lỗi khi tải tệp từ kho.</div>';
      }
    } catch (err) {
      listContainer.innerHTML = `<div style="color: var(--color-error-do); font-size: 11px; padding: 6px;">Lỗi kết nối: ${escapeHtml(err.message)}</div>`;
    }
  }

  // ==========================================================================
  // 6. CÂY THƯ MỤC TỆP TIN & CHUYỂN ĐỔI CHẾ ĐỘ CỘT TRÁI (1 CLICK)
  // ==========================================================================
  async function loadFileTree() {
    const container = document.getElementById('fileTreeContainer');
    if (!container) return;
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; padding: 12px;">Đang tải danh sách tệp từ kho...</div>';

    try {
      const resp = await authFetch('/api/tep_tin');
      if (!resp.ok) {
        container.innerHTML = '<div style="color: var(--color-error-do); font-size: 12px; padding: 12px;">Không tải được danh sách tệp.</div>';
        return;
      }
      const data = await resp.json();
      const files = data.danh_sach || [];
      renderFileTree(files, container);
    } catch (err) {
      container.innerHTML = `<div style="color: var(--color-error-do); font-size: 12px; padding: 12px;">Lỗi: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderFileTree(files, container) {
    // Ghi lại tên đã dùng làm nhãn gốc, để chỗ nhận `/api/status` biết cây
    // đang mang tên cũ hay tên đúng. Xem `state.tenDuAn` bên dưới.
    state.tenDuAnDaVeCay = state.tenDuAn || 'root';
    container.innerHTML = '';
    const groups = {};
    files.forEach(f => {
      const p = f.duong_dan || f;
      const parts = p.split(/[\\/]/);
      // 26/08: tệp ở gốc dự án từng gom vào nhóm tên `root`, nên cây hiện
      // `root/` — không cho biết đang mở dự án nào. Nay dùng tên thư mục
      // thật; chỉ lùi về `root` khi chưa hỏi được máy chủ.
      const dir = parts.length > 1 ? parts[0] : (state.tenDuAn || 'root');
      if (!groups[dir]) groups[dir] = [];
      groups[dir].push(p);
    });

    for (const dir in groups) {
      const dirNode = document.createElement('div');
      dirNode.className = 'file-tree-node';

      const dirRow = document.createElement('div');
      dirRow.className = 'file-tree-row folder';
      dirRow.innerHTML = `<span class="folder-icon">📂</span> <span style="font-weight:600;">${escapeHtml(dir)}/</span>`;
      dirNode.appendChild(dirRow);

      const childrenContainer = document.createElement('div');
      childrenContainer.className = 'file-tree-children';

      groups[dir].forEach(filePath => {
        const fileRow = document.createElement('div');
        fileRow.className = `file-tree-row ${state.activeFilePath === filePath ? 'active' : ''}`;
        fileRow.dataset.path = filePath;
        const fileName = filePath.split(/[\\/]/).pop();
        fileRow.innerHTML = `<span class="file-icon">🐍</span> <span>${escapeHtml(fileName)}</span>`;

        fileRow.addEventListener('click', () => {
          document.querySelectorAll('.file-tree-row').forEach(r => r.classList.remove('active'));
          fileRow.classList.add('active');
          openPyFile(filePath);
        });

        childrenContainer.appendChild(fileRow);
      });

      dirRow.addEventListener('click', () => {
        const isHidden = childrenContainer.style.display === 'none';
        childrenContainer.style.display = isHidden ? 'flex' : 'none';
        dirRow.querySelector('.folder-icon').textContent = isHidden ? '📂' : '📁';
      });

      dirNode.appendChild(childrenContainer);
      container.appendChild(dirNode);
    }
  }

  function setupBottomSplitter() {
    const splitter = document.getElementById('middleSplitter');
    const bottomPane = document.getElementById('canvasBottomPane');
    if (!splitter || !bottomPane) return;

    let isDragging = false;
    let startY = 0;
    let startHeight = 0;

    splitter.addEventListener('mousedown', (e) => {
      isDragging = true;
      startY = e.clientY;
      startHeight = bottomPane.getBoundingClientRect().height;
      splitter.classList.add('dragging');
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaY = startY - e.clientY;
      const newHeight = Math.max(100, Math.min(window.innerHeight * 0.65, startHeight + deltaY));
      bottomPane.style.height = `${newHeight}px`;
      yeuCauChinhCotDoc();
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        splitter.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        chinhCotDoc();
      }
    });
  }

  // ==========================================================================
  // TRỢ LÝ AURA SIDECAR (AI AGENT CHAT)
  // ==========================================================================
  function capNhatAiContextBanner() {
    const oTep = document.getElementById('aiContextFile');
    const oThe = document.getElementById('aiContextCardCount');
    const oLoi = document.getElementById('aiContextDiagCount');
    if (!oTep || !oThe || !oLoi) return;

    const tenTep = state.activeFileName || (state.activeFilePath ? state.activeFilePath.split(/[\\/]/).pop() : 'Chương trình mới');
    oTep.textContent = tenTep;

    const soThe = demTheSau(state.tree || []);
    oThe.textContent = `${soThe} thẻ`;

    const soLoiDo = (state.diagnostics && state.diagnostics.so_loi_do) || 0;
    const soVang = (state.diagnostics && state.diagnostics.so_canh_bao_vang) || 0;

    if (soLoiDo > 0) {
      oLoi.textContent = `${soLoiDo} lỗi`;
      oLoi.className = 'context-pill err';
    } else if (soVang > 0) {
      oLoi.textContent = `${soVang} cảnh báo`;
      oLoi.className = 'context-pill err';
    } else {
      oLoi.textContent = '0 lỗi';
      oLoi.className = 'context-pill ok';
    }
  }

  function themTinNhanAi(vaiTro, htmlNoiDung) {
    const container = document.getElementById('aiMessagesContainer');
    if (!container) return;

    const msgEl = document.createElement('div');
    msgEl.className = `ai-message ${vaiTro}`;

    const avatarEl = document.createElement('div');
    avatarEl.className = 'msg-avatar';
    avatarEl.textContent = vaiTro === 'assistant' ? '✨' : '👤';

    const contentEl = document.createElement('div');
    contentEl.className = 'msg-content';
    contentEl.innerHTML = htmlNoiDung;

    msgEl.appendChild(avatarEl);
    msgEl.appendChild(contentEl);

    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
  }

  function hienThiDangSuyNghi() {
    const container = document.getElementById('aiMessagesContainer');
    if (!container) return null;

    const indEl = document.createElement('div');
    indEl.className = 'ai-message assistant ai-typing-wrapper';
    indEl.id = 'aiTypingIndicator';

    const avatarEl = document.createElement('div');
    avatarEl.className = 'msg-avatar';
    avatarEl.textContent = '✨';

    const typingBox = document.createElement('div');
    typingBox.className = 'msg-content ai-typing-indicator';
    typingBox.innerHTML = `
      <div class="ai-typing-dot"></div>
      <div class="ai-typing-dot"></div>
      <div class="ai-typing-dot"></div>
    `;

    indEl.appendChild(avatarEl);
    indEl.appendChild(typingBox);
    container.appendChild(indEl);
    container.scrollTop = container.scrollHeight;
    return indEl;
  }

  function xoaDangSuyNghi() {
    const ind = document.getElementById('aiTypingIndicator');
    if (ind) ind.remove();
  }

  function phanTichLoiThe() {
    const dsLoi = (state.diagnostics && state.diagnostics.danh_sach) || [];
    const soLoiDo = (state.diagnostics && state.diagnostics.so_loi_do) || 0;
    const soVang = (state.diagnostics && state.diagnostics.so_canh_bao_vang) || 0;

    if (dsLoi.length === 0) {
      return `
        <p>✨ <strong>Toàn bộ thẻ hợp lệ!</strong></p>
        <p>Không phát hiện lỗi cú pháp hoặc cảnh báo nào trên cây thẻ hiện tại. Bạn có thể:</p>
        <ul>
          <li>Bấm <strong>Chạy Thử</strong> (Ctrl+Enter) để kiểm tra kết quả thực thi.</li>
          <li>Chuyển qua tab <strong>Dò Vết & Mạch Nước Ngầm</strong> để quan sát dòng biến số.</li>
        </ul>
      `;
    }

    let html = `<p>🔍 <strong>Phát hiện ${soLoiDo} lỗi ĐỎ và ${soVang} cảnh báo VÀNG:</strong></p><ul>`;
    dsLoi.forEach(l => {
      const icon = l.muc_do === 'do' ? '🔴' : '🟡';
      const theId = l.node_id ? ` (Thẻ <code>${escapeHtml(l.node_id)}</code>)` : '';
      html += `<li>${icon} <strong>${escapeHtml(l.thong_diep)}</strong>${theId}</li>`;
    });
    html += `</ul><p class="msg-tip">💡 <em>Mẹo: Nhấp vào từng mục trong tab "Chẩn Đoán" bên dưới để nhảy nhanh tới thẻ cần sửa.</em></p>`;
    return html;
  }

  function giaiThichKichBan() {
    if (!state.tree || state.tree.length === 0) {
      return '<p>Chương trình hiện đang rỗng. Hãy kéo hoặc nhấp thẻ từ khay bên trái để bắt đầu xây dựng logic.</p>';
    }

    let html = `<p>📖 <strong>Kịch bản luồng chương trình (${escapeHtml(state.activeFileName || 'Hiện tại')}):</strong></p><ol style="padding-left: 18px; margin-bottom: 6px;">`;

    function docNode(node) {
      const o = node.o || {};
      switch (node.ma) {
        case 'ham':
          html += `<li>Định nghĩa hàm <code>${escapeHtml(o.ten_ham || 'f')}</code> với tham số <code>(${escapeHtml(o.tham_so || '')})</code>.`;
          if (node.than && node.than.length) {
            html += '<ul style="margin-top: 4px;">';
            node.than.forEach(docNode);
            html += '</ul>';
          }
          html += `</li>`;
          break;
        case 'gan':
          html += `<li>Khởi tạo/gán biến <code>${escapeHtml(o.ten_bien || 'x')} = ${escapeHtml(o.gia_tri || '0')}</code>.</li>`;
          break;
        case 'neu':
          html += `<li>Kiểm tra điều kiện: Nếu <code>${escapeHtml(o.dieu_kien || 'True')}</code>.`;
          if (node.than && node.than.length) {
            html += '<ul style="margin-top: 4px;">';
            node.than.forEach(docNode);
            html += '</ul>';
          }
          html += `</li>`;
          break;
        case 'lap_moi':
          html += `<li>Vòng lặp: Duyệt biến <code>${escapeHtml(o.bien || 'i')}</code> trong dãy <code>${escapeHtml(o.tap_hop || '[]')}</code>.`;
          if (node.than && node.than.length) {
            html += '<ul style="margin-top: 4px;">';
            node.than.forEach(docNode);
            html += '</ul>';
          }
          html += `</li>`;
          break;
        case 'tra_ve':
          html += `<li>Trả về kết quả <code>${escapeHtml(o.gia_tri || '')}</code> kết thúc hàm.</li>`;
          break;
        case 'in_ra':
          html += `<li>In kết quả <code>${escapeHtml(o.noi_dung || '')}</code> ra màn hình.</li>`;
          break;
        default:
          html += `<li>Thực hiện lệnh thẻ <code>${escapeHtml(node.ma)}</code>.</li>`;
          break;
      }
    }

    state.tree.forEach(docNode);
    html += `</ol><p class="msg-tip">✨ <em>Cấu trúc thẻ đảm bảo tính liên tục và không bị lỗi indentation như gõ code chay.</em></p>`;
    return html;
  }

  function goiYThePhuHop() {
    const coHam = state.tree.some(n => n.ma === 'ham');
    const coInRa = state.tree.some(n => n.ma === 'in_ra');
    const coLap = state.tree.some(n => n.ma === 'lap_moi' || n.ma === 'lap_khi');

    let html = '<p>🧩 <strong>Gợi ý xây dựng logic tiếp theo:</strong></p><ul>';
    if (coHam && !state.tree.some(n => n.than && n.than.some(c => c.ma === 'tra_ve'))) {
      html += '<li>Thêm thẻ <strong>Trả về (return)</strong> vào cuối hàm để trả kết quả tính toán.</li>';
    }
    if (!coInRa) {
      html += '<li>Thêm thẻ <strong>In ra (print)</strong> ở ngoài hàm để kiểm tra kết quả khi chạy thử.</li>';
    }
    if (!coLap) {
      html += '<li>Nếu cần duyệt qua danh sách dữ liệu, bạn có thể dùng thẻ <strong>Lặp mới (for)</strong> từ nhóm Điều Khiển.</li>';
    }
    html += '<li>Thêm thẻ <strong>Gán biến</strong> để lưu kết quả trung gian, giúp Dò Vết biến số rõ ràng hơn.</li>';
    html += '</ul>';
    return html;
  }

  function huongDanMachNuocNgam() {
    return `
      <p>🌊 <strong>Khái niệm Mạch Nước Ngầm (Dataflow Tracing):</strong></p>
      <p>Khác với việc đọc code thụ động, Mạch Nước Ngầm ghi lại <strong>dòng chảy của từng biến số</strong> qua từng nhịp thực thi:</p>
      <ul>
        <li><strong>[K] Khởi tạo:</strong> Biến được cấp phát giá trị ban đầu.</li>
        <li><strong>[B] Biến đổi:</strong> Giá trị được tính toán hoặc thay đổi trong vòng lặp/nhánh.</li>
        <li><strong>[X] Xuất ra:</strong> Giá trị được in ra màn hình hoặc trả về (return).</li>
      </ul>
      <p class="msg-tip">💡 <em>Mở tab "Dò Vết & Mạch Nước Ngầm" bên dưới để trực quan hoá toàn bộ nhịp thực thi!</em></p>
    `;
  }

  function xuLyTinNhanNguoiDung(noiDung) {
    const raw = (noiDung || '').trim();
    if (!raw) return;

    themTinNhanAi('user', escapeHtml(raw));

    const inputEl = document.getElementById('aiChatInput');
    if (inputEl) inputEl.value = '';

    hienThiDangSuyNghi();

    setTimeout(() => {
      xoaDangSuyNghi();
      const q = raw.toLowerCase();
      let traLoi = '';

      if (q.includes('lỗi') || q.includes('sai') || q.includes('đỏ') || q.includes('sửa') || q.includes('fix') || q.includes('bug')) {
        traLoi = phanTichLoiThe();
      } else if (q.includes('kịch bản') || q.includes('luồng') || q.includes('giải thích') || q.includes('làm gì') || q.includes('chạy sao')) {
        traLoi = giaiThichKichBan();
      } else if (q.includes('gợi ý') || q.includes('thêm') || q.includes('thẻ') || q.includes('lắp')) {
        traLoi = goiYThePhuHop();
      } else if (q.includes('trace') || q.includes('mạch nước') || q.includes('ngầm') || q.includes('dò')) {
        traLoi = huongDanMachNuocNgam();
      } else {
        traLoi = `
          <p>Em đã nhận câu hỏi: <em>"${escapeHtml(raw)}"</em>.</p>
          <p>Hiện tại chương trình đang có <strong>${demTheSau(state.tree || [])} thẻ</strong> (${escapeHtml(state.activeFileName || 'Chưa đặt tên')}).</p>
          <p>Sếp có thể bấm các nút gợi ý nhanh ở trên hoặc hỏi em về <strong>lỗi thẻ</strong>, <strong>kịch bản luồng</strong> hay <strong>dò vết mạch nước ngầm</strong> nhé!</p>
        `;
      }

      themTinNhanAi('assistant', traLoi);
    }, 280);
  }

  function setupAiSidecarChat() {
    const btnSend = document.getElementById('btnSendAiChat');
    const input = document.getElementById('aiChatInput');
    const btnClear = document.getElementById('btnClearChat');
    const btnClose = document.getElementById('btnCloseSidebarRight') || document.getElementById('btnToggleSidebarRightClose');
    const quickActions = document.getElementById('aiQuickActions');

    if (btnSend && input) {
      btnSend.addEventListener('click', () => {
        xuLyTinNhanNguoiDung(input.value);
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          xuLyTinNhanNguoiDung(input.value);
        }
      });
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => {
        const container = document.getElementById('aiMessagesContainer');
        if (container) {
          container.innerHTML = `
            <div class="ai-message assistant">
              <div class="msg-avatar">✨</div>
              <div class="msg-content">
                <p>Đã làm sạch hội thoại. Sếp cần em hỗ trợ phân tích thẻ nào tiếp theo ạ?</p>
              </div>
            </div>
          `;
        }
      });
    }

    if (btnClose) {
      btnClose.addEventListener('click', toggleSidebarRight);
    }

    if (quickActions) {
      quickActions.addEventListener('click', (e) => {
        const chip = e.target.closest('.quick-chip');
        if (!chip) return;
        const act = chip.dataset.action;
        if (act === 'analyze-errors') {
          themTinNhanAi('user', '🔍 Phân tích lỗi thẻ');
          hienThiDangSuyNghi();
          setTimeout(() => {
            xoaDangSuyNghi();
            themTinNhanAi('assistant', phanTichLoiThe());
          }, 200);
        } else if (act === 'explain-logic') {
          themTinNhanAi('user', '📖 Giải thích kịch bản luồng');
          hienThiDangSuyNghi();
          setTimeout(() => {
            xoaDangSuyNghi();
            themTinNhanAi('assistant', giaiThichKichBan());
          }, 200);
        } else if (act === 'suggest-card') {
          themTinNhanAi('user', '🧩 Gợi ý lắp ghép thẻ');
          hienThiDangSuyNghi();
          setTimeout(() => {
            xoaDangSuyNghi();
            themTinNhanAi('assistant', goiYThePhuHop());
          }, 200);
        } else if (act === 'trace-help') {
          themTinNhanAi('user', '🌊 Hướng dẫn Mạch Nước Ngầm');
          hienThiDangSuyNghi();
          setTimeout(() => {
            xoaDangSuyNghi();
            themTinNhanAi('assistant', huongDanMachNuocNgam());
          }, 200);
        }
      });
    }

    capNhatAiContextBanner();
  }

  // ==========================================================================
  // 7. SỰ KIỆN & LẮNG NGHE NGƯỜI DÙNG
  // ==========================================================================
  function setupEventListeners() {
    // 1. Sidebar Toggles
    const btnToggleLeft = document.getElementById('btnToggleSidebarLeft');
    if (btnToggleLeft) btnToggleLeft.addEventListener('click', toggleSidebarLeft);

    const btnCloseLeft = document.getElementById('btnCloseSidebarLeft');
    if (btnCloseLeft) btnCloseLeft.addEventListener('click', toggleSidebarLeft);

    const btnToggleRight = document.getElementById('btnToggleSidebarRight');
    if (btnToggleRight) btnToggleRight.addEventListener('click', toggleSidebarRight);

    const btnCloseRight = document.getElementById('btnToggleSidebarRightClose') || document.getElementById('btnCloseSidebarRight');
    if (btnCloseRight) btnCloseRight.addEventListener('click', toggleSidebarRight);

    // Khởi tạo bảng Trợ lý AI Sidecar
    setupAiSidecarChat();

    // Khởi tạo Trình Soạn Thảo Mã & Bộ Chuyển Chế Độ
    setupCodeEditorPane();

    // 2. Chuyển đổi chế độ Khay Thẻ ⇅ Cây Thư Mục ⇅ Gói Thẻ Extension (1 Bấm)
    const btnModeToolbox = document.getElementById('btnModeToolbox');
    const btnModeFiles = document.getElementById('btnModeFiles');
    const btnModeExt = document.getElementById('btnModeExt');
    const toolboxContainer = document.getElementById('toolboxContainer');
    const fileTreeContainer = document.getElementById('fileTreeContainer');
    const extSidebarContainer = document.getElementById('extSidebarContainer');
    const sidebarTitle = document.getElementById('sidebarLeftTitle');
    const toolSearch = document.getElementById('toolSearch');
    const footerTip = document.getElementById('leftFooterTip');

    if (btnModeToolbox && btnModeFiles) {
      btnModeToolbox.addEventListener('click', () => {
        btnModeToolbox.classList.add('active');
        btnModeFiles.classList.remove('active');
        if (btnModeExt) btnModeExt.classList.remove('active');
        if (toolboxContainer) toolboxContainer.style.display = 'flex';
        if (fileTreeContainer) fileTreeContainer.style.display = 'none';
        if (extSidebarContainer) extSidebarContainer.style.display = 'none';
        if (sidebarTitle) sidebarTitle.textContent = 'Khay Thẻ Lệnh';
        if (toolSearch) toolSearch.placeholder = 'Tìm thẻ...';
        if (footerTip) footerTip.textContent = 'Nhấp hoặc kéo thẻ vào vùng soạn thảo.';
      });

      btnModeFiles.addEventListener('click', () => {
        btnModeFiles.classList.add('active');
        btnModeToolbox.classList.remove('active');
        if (btnModeExt) btnModeExt.classList.remove('active');
        if (toolboxContainer) toolboxContainer.style.display = 'none';
        if (fileTreeContainer) fileTreeContainer.style.display = 'flex';
        if (extSidebarContainer) extSidebarContainer.style.display = 'none';
        if (sidebarTitle) sidebarTitle.textContent = 'Cây Thư Mục';
        if (toolSearch) toolSearch.placeholder = 'Tìm tệp python...';
        if (footerTip) footerTip.textContent = 'Click vào tệp để mở trực tiếp trên canvas.';
        loadFileTree();
      });

      if (btnModeExt) {
        btnModeExt.addEventListener('click', () => {
          btnModeExt.classList.add('active');
          btnModeToolbox.classList.remove('active');
          btnModeFiles.classList.remove('active');
          if (toolboxContainer) toolboxContainer.style.display = 'none';
          if (fileTreeContainer) fileTreeContainer.style.display = 'none';
          if (extSidebarContainer) extSidebarContainer.style.display = 'flex';
          if (sidebarTitle) sidebarTitle.textContent = 'Gói Thẻ Extension';
          if (toolSearch) toolSearch.placeholder = 'Tìm gói thẻ...';
          if (footerTip) footerTip.textContent = 'Quản lý và kích hoạt các gói thẻ chuyên dụng.';
          veSidebarExtensions();
        });
      }

      // 26/08: MỞ APP LÊN THÌ HIỆN CÂY TỆP, KHÔNG PHẢI KHAY THẺ.
      btnModeFiles.click();
    }

    // 3. Toolbar buttons
    document.getElementById('btnRun').addEventListener('click', runProgram);
    
    document.getElementById('btnNew').addEventListener('click', () => {
      if (confirm('Tạo chương trình mới? Thao tác này sẽ dọn sạch vùng soạn thảo.')) {
        state.tree = [];
        xoaLichSu();
        state.activeFilePath = '';
        state.activeFileSha256 = null;
        document.getElementById('currentFileName').textContent = 'Chương trình mới (Chưa lưu)';
        document.getElementById('fileModifiedBadge').style.display = 'none';
        onTreeChanged();
      }
    });

    document.getElementById('btnClearCanvas').addEventListener('click', () => {
      if (confirm('Xoá toàn bộ thẻ trên canvas?')) {
        state.tree = [];
        onTreeChanged();
      }
    });

    // Hoàn tác / Làm lại. 24/08: hai nút này CÓ trong index.html (dòng 126,
    // 127) nhưng chưa từng có handler nào — bấm vào im lặng, không gì xảy ra.
    // `state.history`/`historyIndex` cũng khai báo sẵn từ đầu rồi bỏ đó.
    // Bắt được lúc tự dùng thử: thêm một thẻ rồi bấm Hoàn tác, số thẻ vẫn là 3.
    const btnUndo = document.getElementById('btnUndo');
    const btnRedo = document.getElementById('btnRedo');
    if (btnUndo) btnUndo.addEventListener('click', hoanTac);
    if (btnRedo) btnRedo.addEventListener('click', lamLai);

    // Ba nút chỉnh cỡ chữ. 24/08: cùng bệnh với Hoàn tác — CÓ nút trên
    // giao diện (index.html dòng 37-39), CÓ sẵn hàm setCodeFontSize, có cả
    // phím tắt Ctrl+= / Ctrl+- / Ctrl+0, nhưng ba nút thì chưa từng nối.
    // Đo: bấm A+ -> 14px vẫn là 14px; nhấn Ctrl+= -> 15px. Người dùng bấm
    // nút trước, không ai đọc tooltip để biết có phím tắt.
    const btnZoomIn = document.getElementById('btnZoomIn');
    const btnZoomOut = document.getElementById('btnZoomOut');
    const btnZoomReset = document.getElementById('btnZoomReset');
    if (btnZoomIn) btnZoomIn.addEventListener('click', () => setCodeFontSize(state.codeFontSize + 1));
    if (btnZoomOut) btnZoomOut.addEventListener('click', () => setCodeFontSize(state.codeFontSize - 1));
    if (btnZoomReset) btnZoomReset.addEventListener('click', () => setCodeFontSize(14));

    // Tìm trong chương trình
    const btnFind = document.getElementById('btnFindInFile');
    const findInput = document.getElementById('findInput');
    if (btnFind) btnFind.addEventListener('click', moThanhTim);
    if (findInput) {
      findInput.addEventListener('input', (e) => chayTimKiem(e.target.value));
      findInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          nhayKetQua(e.shiftKey ? -1 : 1);
        } else if (e.key === 'Escape') {
          e.preventDefault();
          dongThanhTim();
        }
      });
    }
    const btnFindNext = document.getElementById('btnFindNext');
    const btnFindPrev = document.getElementById('btnFindPrev');
    const btnFindClose = document.getElementById('btnFindClose');
    if (btnFindNext) btnFindNext.addEventListener('click', () => nhayKetQua(1));
    if (btnFindPrev) btnFindPrev.addEventListener('click', () => nhayKetQua(-1));
    if (btnFindClose) btnFindClose.addEventListener('click', dongThanhTim);

    const btnReplaceOne = document.getElementById('btnReplaceOne');
    const btnReplaceAll = document.getElementById('btnReplaceAll');
    const replaceInput = document.getElementById('replaceInput');
    if (btnReplaceOne) btnReplaceOne.addEventListener('click', thayMotCho);
    if (btnReplaceAll) btnReplaceAll.addEventListener('click', thayTatCa);
    if (replaceInput) {
      replaceInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          // Enter = thay MỘT chỗ. "Thay tất cả" phải bấm nút — thao tác xoá
          // được cả chương trình thì không nên nằm dưới một phím Enter lỡ tay.
          e.preventDefault();
          thayMotCho();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          dongThanhTim();
        }
      });
    }

    // Khởi tạo bộ điều khiển Kho Workflow Hub
    setupWorkflowHubControls();

    // Khởi tạo bộ điều khiển Cửa Hàng Extension
    setupExtensionHubControls();
    veSidebarExtensions();

    const btnExt = document.getElementById('btnExtensions');
    const modalExt = document.getElementById('extensionsModal');
    const btnCloseExt = document.getElementById('btnCloseExtensions');

    if (btnExt && modalExt) {
      btnExt.addEventListener('click', () => {
        modalExt.style.display = 'flex';
        veDanhSachExtensions();
      });
    }
    if (btnCloseExt && modalExt) {
      btnCloseExt.addEventListener('click', () => {
        modalExt.style.display = 'none';
      });
    }

    // Khởi tạo Phòng Thử Thách Lập Trình & Auto-Grader
    setupChallengeHubControls();

    // Khởi tạo Sơ Đồ Khối Thuật Toán (Flowchart Generator)
    setupFlowchartControls();

    // Khởi tạo Bộ Đóng Gói Dự Án Zip (1-Click Project Packager)
    setupPackageControls();

    // Khởi tạo Chế Độ Trình Chiếu Giảng Dạy & Bút Vẽ Canvas
    setupPresentationControls();

    const btnChallenges = document.getElementById('btnChallenges');
    const modalChallenges = document.getElementById('challengesModal');
    const btnCloseChallenges = document.getElementById('btnCloseChallenges');

    if (btnChallenges && modalChallenges) {
      btnChallenges.addEventListener('click', () => {
        modalChallenges.style.display = 'flex';
        veDanhSachThuThach();
      });
    }
    if (btnCloseChallenges && modalChallenges) {
      btnCloseChallenges.addEventListener('click', () => {
        modalChallenges.style.display = 'none';
      });
    }

    const btnGrade = document.getElementById('btnGradeChallenge');
    const btnGradeAgain = document.getElementById('btnRunGraderAgain');
    const btnCloseBanner = document.getElementById('btnCloseChallengeBanner');

    if (btnGrade) btnGrade.addEventListener('click', chamDiemBaiTap);
    if (btnGradeAgain) btnGradeAgain.addEventListener('click', chamDiemBaiTap);
    if (btnCloseBanner) btnCloseBanner.addEventListener('click', dongThuThach);

    // Mẫu bài Modal
    document.getElementById('btnSamples').addEventListener('click', () => {
      loadSamples();
      document.getElementById('samplesModal').style.display = 'flex';
    });
    document.getElementById('btnCloseSamples').addEventListener('click', () => {
      document.getElementById('samplesModal').style.display = 'none';
    });
    document.getElementById('btnLoadSampleIntro').addEventListener('click', () => {
      state.tree = [
        { id: "m1_1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
          { id: "m1_2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
        ]},
        { id: "m1_3", ma: "in_ra", o: { noi_dung: "cong(5, 7)" }, than: [] }
      ];
      state.activeFilePath = '';
      state.activeFileSha256 = null;
      document.getElementById('currentFileName').textContent = '1. Hàm cộng hai số';
      onTreeChanged();
    });

    // Mở tệp Modal & Bộ duyệt tệp động
    document.getElementById('btnOpenFile').addEventListener('click', () => {
      loadRepoFiles('core');
      // 24/08: bat gap khi tu dung thu — o nay KHONG duoc don khi mo lai
      // modal, nen van con duong dan cua lan mo truoc. Bam vao roi go tiep
      // (thao tac tu nhien nhat) noi chuoi cu voi chuoi moi thanh mot duong
      // dan vo nghia, vi input KHONG tu chon toan bo chu khi duoc focus.
      document.getElementById('openFilePath').value = '';
      document.getElementById('openFileModal').style.display = 'flex';
    });
    document.getElementById('btnCloseOpenFile').addEventListener('click', () => {
      document.getElementById('openFileModal').style.display = 'none';
    });
    document.getElementById('btnCancelOpenFile').addEventListener('click', () => {
      document.getElementById('openFileModal').style.display = 'none';
    });
    document.getElementById('btnConfirmOpenFile').addEventListener('click', () => {
      const p = document.getElementById('openFilePath').value;
      openPyFile(p);
    });
    // Bam vao chip trong danh sach van dien san duong dan (dong 2015) roi
    // nguoi dung co the muon sua tay — focus thi chon san toan bo chu, kieu
    // o dia chi trinh duyet, de go de la thay ngay chu bam khong noi vao.
    document.getElementById('openFilePath').addEventListener('focus', function () {
      this.select();
    });

    // Bộ điều khiển Trình Gỡ Lỗi Trực Quan (Visual Card Debugger)
    const btnDebug = document.getElementById('btnDebug');
    if (btnDebug) {
      btnDebug.addEventListener('click', () => {
        if (debuggerState.isActive) {
          dungGoLoi();
        } else {
          batDauGoLoi();
        }
      });
    }

    const btnDebugStepNext = document.getElementById('btnDebugStepNext');
    const btnDebugStepPrev = document.getElementById('btnDebugStepPrev');
    const btnDebugAutoPlay = document.getElementById('btnDebugAutoPlay');
    const btnDebugStop = document.getElementById('btnDebugStop');
    const debugSlider = document.getElementById('debugTimelineSlider');

    if (btnDebugStepNext) btnDebugStepNext.addEventListener('click', buocTiep);
    if (btnDebugStepPrev) btnDebugStepPrev.addEventListener('click', buocTruoc);
    if (btnDebugAutoPlay) btnDebugAutoPlay.addEventListener('click', batTatTuDongChay);
    if (btnDebugStop) btnDebugStop.addEventListener('click', dungGoLoi);
    if (debugSlider) {
      debugSlider.addEventListener('input', (e) => {
        nhayToiBuoc(parseInt(e.target.value, 10) - 1);
      });
    }

    document.querySelectorAll('.filter-tag').forEach(tag => {
      tag.addEventListener('click', () => {
        document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        loadRepoFiles(tag.dataset.dir || 'core');
      });
    });

    // Lưu tệp Modal
    document.getElementById('btnSaveFile').addEventListener('click', () => {
      document.getElementById('saveFilePath').value = state.activeFilePath || 'my_program.py';
      document.getElementById('saveFileModal').style.display = 'flex';
    });
    document.getElementById('btnCloseSaveFile').addEventListener('click', () => {
      document.getElementById('saveFileModal').style.display = 'none';
    });
    document.getElementById('btnCancelSaveFile').addEventListener('click', () => {
      document.getElementById('saveFileModal').style.display = 'none';
    });
    document.getElementById('btnConfirmSaveFile').addEventListener('click', () => {
      const p = document.getElementById('saveFilePath').value;
      const type = document.querySelector('input[name="saveType"]:checked').value;
      saveFile(p, type);
    });
    // Cùng bệnh với ô openFilePath (24/08): ô này luôn điền sẵn đường dẫn tệp
    // đang mở, có khi dài. Focus thì chọn hết để gõ đè sạch, không nối chuỗi.
    document.getElementById('saveFilePath').addEventListener('focus', function () {
      this.select();
    });

    // Bottom Pane Tabs Switch (6 tabs)
    document.querySelectorAll('.canvas-bottom-pane .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.canvas-bottom-pane .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.canvas-bottom-pane .tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const targetTab = document.getElementById(btn.dataset.tab);
        if (targetTab) targetTab.classList.add('active');
        if (btn.dataset.tab === 'tabDiag') {
          chayKhamBenhVaHienThi();
        }
      });
    });

    // Khởi tạo Bác Sĩ AI Bắt Bệnh & Tự Động Sửa Lỗi
    const btnDoctorScan = document.getElementById('btnDoctorScan');
    const btnTerminalAutoFix = document.getElementById('btnTerminalAutoFix');
    const btnCloseTermDoctor = document.getElementById('btnCloseTerminalDoctor');

    if (btnDoctorScan) {
      btnDoctorScan.addEventListener('click', chayKhamBenhVaHienThi);
    }
    if (btnTerminalAutoFix) {
      btnTerminalAutoFix.addEventListener('click', () => {
        if (currentRuntimePatch) {
          thucHienAutoFix(currentRuntimePatch);
        }
      });
    }
    if (btnCloseTermDoctor) {
      btnCloseTermDoctor.addEventListener('click', () => {
        const b = document.getElementById('terminalDoctorBanner');
        if (b) b.style.display = 'none';
      });
    }

    // Nút Dò Dòng Dữ Liệu (Mạch Nước Ngầm)
    const btnRunTrace = document.getElementById('btnRunTrace');
    if (btnRunTrace) {
      btnRunTrace.addEventListener('click', () => {
        chayMachNuocNgam();
      });
    }

    // Nút Định Vị Lỗi E1
    const btnRunE1 = document.getElementById('btnRunE1');
    if (btnRunE1) {
      btnRunE1.addEventListener('click', () => {
        chayDinhViLoiE1();
      });
    }

    // Tìm kiếm thẻ hoặc tệp
    if (toolSearch) {
      toolSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (btnModeToolbox && btnModeToolbox.classList.contains('active')) {
          document.querySelectorAll('.tool-item').forEach(item => {
            const ma = item.dataset.ma;
            const def = TheValidator.BO_THE_V1[ma];
            const match = ma.includes(query) || (def && def.ten.toLowerCase().includes(query));
            item.style.display = match ? 'flex' : 'none';
          });
        } else {
          document.querySelectorAll('.file-tree-row:not(.folder)').forEach(row => {
            const path = (row.dataset.path || '').toLowerCase();
            const match = path.includes(query);
            row.style.display = match ? 'flex' : 'none';
          });
        }
      });
    }

    // Drag-and-drop vào Canvas Root
    const workspace = document.getElementById('canvasWorkspace');
    if (workspace) {
      workspace.addEventListener('dragover', (e) => {
        e.preventDefault();
      });
      workspace.addEventListener('dragleave', (e) => {
        // Rời hẳn khung canvas (không phải chỉ đi qua một thẻ con) — dọn dấu
        // "sẽ chèn ở đây" còn sót lại nếu chuột rê ra vùng chết giữa hai thẻ.
        if (e.target === workspace) xoaDanhDauViTriTha();
      });
      workspace.addEventListener('drop', (e) => {
        e.preventDefault();
        const raw = e.dataTransfer.getData('text/plain');
        if (!raw) return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === 'NEW_CARD') {
            addNewCardToRoot(payload.ma);
          } else if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
            // Thả vào nền canvas (không trúng dòng thẻ nào) -> đưa xuống
            // CUỐI cấp gốc. Thả trúng một dòng cụ thể thì dòng đó tự xử lý.
            if (diChuyenThe(payload.nodeId, state.tree, null, state.tree.length)) {
              onTreeChanged();
            }
          }
        } catch (_) {}
      });
    }

    // ResizeObserver trên khung chứa thẻ để tự động chỉnh cột dọc khi DOM reflow
    const cardRoot = document.getElementById('cardChainRoot');
    if (cardRoot && typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => {
        yeuCauChinhCotDoc();
      });
      ro.observe(cardRoot);
    }

    // Thiết lập Splitter chia đôi kéo được
    setupBottomSplitter();

    // Lắng nghe window resize để tính lại chiều cao cột dọc
    window.addEventListener('resize', () => {
      yeuCauChinhCotDoc();
    });

    // Phím tắt bàn phím IDE chuẩn
    // ======================================================================
    // CHẶN MẤT DỮ LIỆU KHI ĐÓNG TAB — thêm 26/08/2026
    // ======================================================================
    //
    // Trước hôm nay `grep -rn beforeunload interface/web/the_v1/` ra KHÔNG
    // MỘT DÒNG NÀO. Nghĩa là đóng tab trình duyệt — bấm ✕, hay Ctrl+W —
    // thì mọi thẻ chưa lưu bay sạch, im lặng, không một câu hỏi.
    //
    // Ctrl+W làm chuyện này TỰ NHIÊN đến mức nguy hiểm: trong VS Code nó đóng
    // MỘT TỆP; ở đây nó không được app bắt (đo 26/08: `defaultPrevented` là
    // `false`) nên trình duyệt đóng cả cửa sổ app.
    //
    // Đúng họ bệnh CLAUDE.md §4 — app cho sửa mà không giữ. Và nó không lộ ra
    // trong test nào: 707 test xanh suốt trong khi chỗ này trống.
    //
    // Phải xét CẢ CÁC TAB KHÁC, không chỉ tab đang mở: `state.hasModifications`
    // là cờ của tab đang xem, các tab kia giữ cờ riêng trong ảnh chụp của
    // chúng (xem `anhTabHienTai`). Chỉ xét tab đang xem thì mở ba tệp, sửa hai
    // tệp đầu, đứng ở tệp thứ ba mà đóng là vẫn mất hai tệp kia.
    function coThayDoiChuaLuu() {
      if (state.hasModifications) return true;
      return (state.tabs || []).some(
        (t, i) => i !== state.tabActive && t && t.hasModifications);
    }

    window.addEventListener('beforeunload', (e) => {
      if (!coThayDoiChuaLuu()) return;
      // Trình duyệt đời nay KHÔNG hiện câu chữ của mình, chỉ hiện hộp mặc
      // định của nó. Cả `preventDefault()` lẫn `returnValue` đều cần: Chrome
      // theo cái sau, chuẩn HTML theo cái trước.
      e.preventDefault();
      e.returnValue = '';
      return '';
    });

    window.addEventListener('keydown', (e) => {
      if (e.ctrlKey && !e.shiftKey && (e.key === 's' || e.key === 'S')) {
        // 26/08/2026: Ctrl+S TRƯỚC ĐÂY KHÔNG ĐƯỢC BẮT.
        //
        // Đo bằng cách gửi phím thật vào trang: `defaultPrevented` là `false`,
        // tức phím rơi xuống trình duyệt — và ở trình duyệt Ctrl+S mở hộp
        // "Lưu trang web". Không phải "không làm gì", mà là LÀM SAI: người
        // dùng quen IDE bấm phản xạ số một của họ và nhận một hộp thoại lạc đề.
        //
        // Chỉ 4 trong 15 phím tắt IDE chuẩn được bắt (đo 26/08):
        //   bắt được  Ctrl+F · Ctrl+H · Ctrl+B · Ctrl+Z/Y · Ctrl+C/X/V · Ctrl+Enter
        //   rơi xuống Ctrl+S · Ctrl+P · Ctrl+O · Ctrl+N · Ctrl+W
        //
        // Lưu THẲNG khi tệp đã có đường dẫn, giống mọi trình soạn thảo. Hộp
        // hỏi đường dẫn chỉ bật khi tệp chưa có tên — đó là "Lưu thành tệp
        // mới", việc khác. Nút "Lưu Tệp" trên thanh trên vẫn mở hộp như cũ,
        // không đụng tới.
        e.preventDefault();
        if (state.activeFilePath) {
          const kieu = /\.json$/i.test(state.activeFilePath) ? 'json' : 'py';
          saveFile(state.activeFilePath, kieu);
        } else {
          const oDuong = document.getElementById('saveFilePath');
          const hop = document.getElementById('saveFileModal');
          if (oDuong && hop) {
            oDuong.value = 'my_program.py';
            hop.style.display = 'flex';
            oDuong.focus();
            oDuong.select();
          }
        }
      } else if (e.ctrlKey && !e.shiftKey && (e.key === 'p' || e.key === 'P')) {
        // Ctrl+P — MỞ NHANH TỆP. Thêm 27/08/2026.
        //
        // Đo 26/08: Ctrl+P rơi xuống trình duyệt (mở hộp In). Với người quen
        // VS Code / Cursor thì đây là phím dùng nhiều thứ hai sau Ctrl+S.
        //
        // Chặn được — khác Ctrl+N và Ctrl+W mà Chrome giữ riêng, trang web
        // không nhận được. Đã đo từng phím bằng cách gửi vào `document.body`
        // rồi đọc `defaultPrevented`.
        //
        // Dựng từ đồ CÓ SẴN, không viết hộp tìm mới: ô tìm của cột trái đã
        // lọc cây tệp theo đường dẫn khi đang ở chế độ tệp (xem handler
        // `toolSearch` bên dưới). Ctrl+P chỉ cần chuyển sang cây tệp, xoá ô
        // tìm, rồi đặt con trỏ vào đó. Viết hộp mới là thêm một chỗ nữa để
        // lệch với cây tệp thật.
        e.preventDefault();
        const nutTep = document.getElementById('btnModeFiles');
        const oTim = document.getElementById('toolSearch');
        // Mở cột trái nếu đang thu gọn — nếu không thì bấm Ctrl+P xong không
        // thấy gì xảy ra, đúng loại hỏng lặng lẽ.
        if (state.sidebarLeftCollapsed) toggleSidebarLeft();
        if (nutTep) nutTep.click();
        if (oTim) {
          oTim.value = '';
          oTim.dispatchEvent(new Event('input', { bubbles: true }));
          oTim.focus();
        }
      } else if (e.ctrlKey && (e.key === 'o' || e.key === 'O')) {
        // Ctrl+O — MỞ TỆP bằng đường dẫn. Cũng rơi xuống trình duyệt trước
        // 27/08 (mở hộp chọn tệp của trình duyệt, vô dụng ở đây vì app đọc
        // tệp qua máy chủ chứ không qua trình duyệt).
        e.preventDefault();
        const nutMo = document.getElementById('btnOpenFile');
        if (nutMo) nutMo.click();
      } else if (e.key === 'F9') {
        e.preventDefault();
        if (debuggerState.isActive) dungGoLoi();
        else batDauGoLoi();
      } else if (e.key === 'F10' || (e.altKey && (e.key === 'ArrowRight' || e.key === 'Right'))) {
        e.preventDefault();
        if (e.shiftKey) buocTruoc();
        else buocTiep();
      } else if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'Left')) {
        e.preventDefault();
        buocTruoc();
      } else if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) {
          chamDiemBaiTap();
        } else {
          runProgram();
        }
      } else if (e.ctrlKey && (e.key === 'b' || e.key === 'B')) {
        e.preventDefault();
        toggleSidebarLeft();
      } else if (e.ctrlKey && (e.key === 'j' || e.key === 'J')) {
        e.preventDefault();
        toggleSidebarRight();
      } else if (e.altKey && e.key === '1') {
        e.preventDefault();
        setEditorMode('cards');
      } else if (e.altKey && e.key === '2') {
        e.preventDefault();
        setEditorMode('split');
      } else if (e.altKey && e.key === '3') {
        e.preventDefault();
        setEditorMode('code');
      } else if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
        e.preventDefault();
        setCodeFontSize(state.codeFontSize + 1);
      } else if (e.ctrlKey && (e.key === '-' || e.key === '_')) {
        e.preventDefault();
        setCodeFontSize(state.codeFontSize - 1);
      } else if (e.ctrlKey && e.key === '0') {
        e.preventDefault();
        setCodeFontSize(14);
      } else if (e.ctrlKey && (e.key === 'f' || e.key === 'F')) {
        // Cướp Ctrl+F khỏi trình duyệt: tìm trong CÂY THẺ mới đúng thứ người
        // dùng cần, chứ không phải tìm chữ trong toàn trang HTML (sẽ khớp cả
        // tên nút, nhãn khay thẻ, chữ trong terminal...).
        e.preventDefault();
        moThanhTim();
      } else if (e.key === 'F12') {
        // F12 khi ĐANG GÕ trong ô: nhảy theo từ dưới con trỏ, sát với lối
        // quen của trình soạn thảo. Ngoài ô thì nhảy theo thẻ đang chọn.
        const o = e.target.closest('input, textarea');
        if (o) {
          const tu = tuDuoiConTro(o);
          if (tu) { e.preventDefault(); nhayToiDinhNghia(tu); }
        } else if (state.selectedNodeId) {
          e.preventDefault();
          nhayTuTheDangChon();
        }
      } else if (e.ctrlKey && (e.key === 'c' || e.key === 'C')) {
        // Đang gõ trong ô nhập thì để trình duyệt chép CHỮ, đừng cướp phím
        // để chép cả thẻ. Cùng lối phòng thủ như Ctrl+Z ở dưới.
        if (e.target.closest('input, textarea')) return;
        if (state.selectedNodeId) { e.preventDefault(); chepThe(); }
      } else if (e.ctrlKey && (e.key === 'x' || e.key === 'X')) {
        if (e.target.closest('input, textarea')) return;
        if (state.selectedNodeId) { e.preventDefault(); catThe(); }
      } else if (e.ctrlKey && (e.key === 'v' || e.key === 'V')) {
        if (e.target.closest('input, textarea')) return;
        if (bangGhiThe.node) { e.preventDefault(); danThe(); }
      } else if (e.ctrlKey && (e.key === 'h' || e.key === 'H')) {
        // Ctrl+H mở CẢ hàng thay thế. Ctrl+F chỉ mở hàng tìm — người chỉ muốn
        // tìm thì không phải nhìn thấy nút xoá được cả chương trình.
        e.preventDefault();
        moThanhThayThe();
      } else if (e.key === 'Escape') {
        const bar = document.getElementById('findBar');
        if (bar && bar.style.display !== 'none') dongThanhTim();
        else if (debuggerState.isActive) dungGoLoi();
        else if (state.selectedNodeId) chonThe(null);
      } else if (e.ctrlKey && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) {
        // Đang gõ trong ô nhập thì để trình duyệt tự hoàn tác CHỮ trong ô đó,
        // đừng cướp phím để hoàn tác cả cây thẻ — người dùng sẽ mất nguyên
        // câu vừa gõ chỉ vì lỡ tay.
        if (e.target.closest('input, textarea')) return;
        e.preventDefault();
        hoanTac();
      } else if (e.ctrlKey && ((e.key === 'y' || e.key === 'Y') ||
                               ((e.key === 'z' || e.key === 'Z') && e.shiftKey))) {
        if (e.target.closest('input, textarea')) return;
        e.preventDefault();
        lamLai();
      }
    });
  }

  // ==========================================================================
  // KHỞI ĐỘNG ỨNG DỤNG
  // ==========================================================================
  window.addEventListener('DOMContentLoaded', async () => {
    initAuthToken();
    initLayoutPreferences();
    renderToolbox();
    setupEventListeners();
    // 26/08: CHỜ lượt này xong. Nó gọi `/api/status`, và `state.tenDuAn` lấy
    // từ đó là KHOÁ để nhớ tệp đang mở của từng dự án. Không chờ thì
    // `moLaiTepLanTruoc()` ở dưới đọc khoá '(khong ro)' — sai dự án, và lần
    // sau mở lại đòi nhầm tệp.
    //
    // Đây là lần thứ hai trong buổi tôi vấp đúng chuyện này (lần trước: cây
    // tệp vẽ xong trước khi tên dự án về, nên nhãn gốc vẫn là `root/`). Một
    // lượt gọi mạng loopback tốn vài mili giây; chờ nó rẻ hơn nhiều so với
    // một lỗi chỉ hiện ra ở lần chạy thứ hai.
    await configureRuntimeCapabilities();

    // Nạp mặc định bài mẫu "Hàm cộng hai số" để người dùng mở ra có thể trải nghiệm ngay
    state.tree = [
      { id: "m1_1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
        { id: "m1_2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
      ]},
      { id: "m1_3", ma: "in_ra", o: { noi_dung: "cong(5, 7)" }, than: [] }
    ];
    // Tab ĐẦU TIÊN là bài mẫu, chưa gắn với tệp nào trên đĩa.
    // Không có nó thì `dongBoTabHienTai` không có chỗ để chụp, và tab tệp
    // đầu người dùng mở sẽ NUỐT MẤT bài mẫu mà không ai thấy.
    state.activeFileName = '1. Hàm cộng hai số';
    state.tabs = [{
      duong_dan: '', ten_tep: state.activeFileName, tree: state.tree,
      sha256: null, hasModifications: false,
      history: [], historyIndex: -1, selectedNodeId: null
    }];
    state.tabActive = 0;
    document.getElementById('currentFileName').textContent = state.activeFileName;
    // `markDirty=false`: bài mẫu vừa nạp thì CHƯA CÓ ai sửa gì.
    //
    // 25/08, bắt được khi làm thanh tab: bản cũ gọi `onTreeChanged()` trơn
    // nên `hasModifications = true` ngay từ giây đầu. Trước đây không ai thấy
    // vì huy hiệu "ĐÃ SỬA" chỉ hiện khi đã có đường dẫn tệp — mà bài mẫu thì
    // chưa có. Thanh tab phơi nó ra: tab hiện dấu • "chưa lưu" trong khi
    // người dùng chưa chạm vào gì.
    //
    // Vẫn phải GHI MỘT MỐC GỐC (`ghiLichSu`), đúng như đường mở tệp: không có
    // mốc thì thao tác sửa ĐẦU TIÊN thành bước gốc và Ctrl+Z không lùi về đâu.
    onTreeChanged(false, false);
    ghiLichSu();
    veThanhTab();
    loadAvailableTests();
    yeuCauChinhCotDoc();

    // 26/08: mở lại tệp đang làm dở — SAU khi tab bài mẫu đã dựng xong.
    //
    // Thứ tự này bắt buộc: `moTrongTab` gọi `dongBoTabHienTai()` để chụp tab
    // hiện tại trước khi mở tab mới. Chưa có tab nào thì không có chỗ chụp,
    // và bài mẫu bị nuốt mất — đúng lỗi chú thích phía trên đã ghi.
    //
    // Không `await`: mở tệp là một lượt gọi mạng. Chờ nó thì màn hình đứng
    // im cho tới khi xong; để nó tự chạy thì người dùng thấy bài mẫu trước,
    // rồi tệp của mình thế chỗ ngay sau đó.
    moLaiTepLanTruoc();
  });

  if (typeof window !== 'undefined') {
    window.state = state;
    window.updateButtonsState = updateButtonsState;
    window.renderE1Results = renderE1Results;
    window.renderE1Error = renderE1Error;
    window.escapeHtml = escapeHtml;
    window.openPyFile = openPyFile;
    window.saveFile = saveFile;
    window.chayDinhViLoiE1 = chayDinhViLoiE1;
    window.chinhCotDoc = chinhCotDoc;
    window.yeuCauChinhCotDoc = yeuCauChinhCotDoc;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      state,
      escapeHtml,
      configureRuntimeCapabilities,
      updateButtonsState,
      chayMachNuocNgam,
      chayDinhViLoiE1,
      renderE1Results,
      renderE1Error,
      loadAvailableTests,
      openPyFile,
      saveFile,
      chinhCotDoc,
      yeuCauChinhCotDoc,
    };
  }

})();
