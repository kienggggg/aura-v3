/**
 * test_e1_ui.js — UI & Renderer unit tests cho E1 trong App Thẻ v1.
 *
 * Chạy bằng runner thuần của Node.js: `node --test tests/test_e1_ui.js`
 * Không dùng jsdom, không tải dependency ngoài.
 */
const { test, describe, beforeEach } = require('node:test');
const assert = require('node:assert');

// Fake DOM tối thiểu cho Node.js
class FakeElement {
  constructor(tagName = 'div') {
    this.tagName = tagName.toUpperCase();
    this.id = '';
    this.className = '';
    this.textContent = '';
    this.innerHTML = '';
    this.style = {};
    this.disabled = false;
    this.title = '';
    this.children = [];
    this.parentElement = null;
    this.dataset = {};
    this.value = '';
    this.classList = {
      _classes: new Set(),
      add: (cls) => this.classList._classes.add(cls),
      remove: (cls) => this.classList._classes.delete(cls),
      contains: (cls) => this.classList._classes.has(cls),
    };
  }

  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  querySelector(selector) {
    // Basic selector support for simple tags/classes
    for (const ch of this.children) {
      if (selector.startsWith('.') && ch.className.includes(selector.slice(1))) return ch;
      if (ch.tagName.toLowerCase() === selector.toLowerCase()) return ch;
      const found = ch.querySelector ? ch.querySelector(selector) : null;
      if (found) return found;
    }
    return null;
  }

  querySelectorAll(selector) {
    const results = [];
    const walk = (node) => {
      for (const ch of node.children) {
        if (selector.startsWith('.') && ch.className.includes(selector.slice(1))) {
          results.push(ch);
        } else if (ch.tagName.toLowerCase() === selector.toLowerCase()) {
          results.push(ch);
        }
        if (ch.children) walk(ch);
      }
    };
    walk(this);
    return results;
  }
}

class FakeDocument {
  constructor() {
    this.elements = new Map();
  }

  createElement(tagName) {
    return new FakeElement(tagName);
  }

  getElementById(id) {
    if (!this.elements.has(id)) {
      const el = new FakeElement();
      el.id = id;
      this.elements.set(id, el);
    }
    return this.elements.get(id);
  }

  querySelectorAll() {
    return [];
  }
}

// Cài đặt global môi trường fake
global.window = {
  addEventListener: () => {},
  removeEventListener: () => {},
  location: { search: '' },
  localStorage: {
    getItem: () => null,
    setItem: () => {},
  },
};
global.document = new FakeDocument();
global.TheValidator = {
  BO_THE_V1: {}
};

// Nạp module app.js
const app = require('../interface/web/the_v1/app.js');

// 24/08/2026: bay phep khang dinh o day tung viet `assert.ok(x !== null)` trong khi
// `x` den tu `Array.prototype.find`, ma `find` tra ve `undefined` chu khong phai
// `null` — nen `undefined !== null` la true va cua LUON XANH. Do that: doi chuoi
// badge trong app.js thanh 'Suite: XYZ HONG' roi chay lai -> van pass 7/7.
// Doi sang kiem truthy thi gieo dung loi ay -> DO ngay.
describe('E1 UI & Renderer Tests', () => {

  beforeEach(() => {
    global.document = new FakeDocument();
  });

  test('escapeHtml() vô hiệu hóa các ký tự nhạy cảm XSS', () => {
    const payload = '<script>alert("xss")</script>';
    const escaped = app.escapeHtml(payload);
    assert.strictEqual(escaped, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');

    assert.strictEqual(app.escapeHtml("a & b < c > 'd'"), 'a &amp; b &lt; c &gt; &#039;d&#039;');
    assert.strictEqual(app.escapeHtml(null), '');
    assert.strictEqual(app.escapeHtml(undefined), '');
  });

  test('configureRuntimeCapabilities() khi cờ tắt vô hiệu hóa 3 nút', async () => {
    const btnRun = global.document.getElementById('btnRun');
    const btnRunTrace = global.document.getElementById('btnRunTrace');
    const btnRunE1 = global.document.getElementById('btnRunE1');
    const tracePill = global.document.getElementById('traceStatusPill');
    const e1Pill = global.document.getElementById('e1StatusPill');

    // Mock authFetch trả về code_execution_enabled = false
    global.fetch = async () => ({
      ok: true,
      json: async () => ({ code_execution_enabled: false })
    });

    await app.configureRuntimeCapabilities();

    assert.strictEqual(btnRun.disabled, true);
    assert.strictEqual(btnRunTrace.disabled, true);
    assert.strictEqual(btnRunE1.disabled, true);
    assert.strictEqual(tracePill.textContent, 'TẮT');
    assert.strictEqual(e1Pill.textContent, 'TẮT');
    assert.strictEqual(app.state.codeExecutionEnabled, false);
  });

  test('configureRuntimeCapabilities() khi cờ bật kích hoạt 3 nút', async () => {
    const btnRun = global.document.getElementById('btnRun');
    const btnRunTrace = global.document.getElementById('btnRunTrace');
    const btnRunE1 = global.document.getElementById('btnRunE1');

    // Mock authFetch trả về code_execution_enabled = true
    global.fetch = async () => ({
      ok: true,
      json: async () => ({ code_execution_enabled: true })
    });

    await app.configureRuntimeCapabilities();

    assert.strictEqual(btnRun.disabled, false);
    assert.strictEqual(btnRunTrace.disabled, false);
    assert.strictEqual(btnRunE1.disabled, false);
    assert.strictEqual(app.state.codeExecutionEnabled, true);
  });

  test('loadAvailableTests() gọi toàn dự án và chỉ giữ hai quy ước tên pytest', async () => {
    const select = global.document.getElementById('e1TestSelect');
    let requestedUrl = '';
    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify({
          danh_sach: [
            { duong_dan: 'test_bai_tap.py', ten_tep: 'test_bai_tap.py', sha256: 'a'.repeat(64) },
            { duong_dan: 'goi/phep_tinh_test.py', ten_tep: 'phep_tinh_test.py', sha256: 'b'.repeat(64) },
            { duong_dan: 'goi/helper.py', ten_tep: 'helper.py', sha256: 'c'.repeat(64) },
            { duong_dan: 'test_du_lieu.json', ten_tep: 'test_du_lieu.json', sha256: 'd'.repeat(64) },
          ]
        })
      };
    };

    await app.loadAvailableTests('tests/test_bai_tap.py');

    assert.strictEqual(requestedUrl, '/api/tep_tin');
    assert.deepStrictEqual(
      select.children.map(option => option.value),
      ['test_bai_tap.py', 'goi/phep_tinh_test.py']
    );
    assert.strictEqual(select.children[0].selected, true, 'Phải ghép tệp ở gốc theo basename');
    assert.deepStrictEqual(
      Object.keys(app.state.testFilesInventory),
      ['test_bai_tap.py', 'goi/phep_tinh_test.py']
    );
  });

  test('loadAvailableTests() giải thích khi API 200 nhưng không có tệp pytest', async () => {
    const select = global.document.getElementById('e1TestSelect');
    const statusPill = global.document.getElementById('e1StatusPill');
    global.fetch = async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        danh_sach: [
          { duong_dan: 'bai_tap.py', ten_tep: 'bai_tap.py' },
          { duong_dan: 'test_du_lieu.json', ten_tep: 'test_du_lieu.json' },
        ]
      })
    });

    await app.loadAvailableTests();

    assert.strictEqual(select.children.length, 1);
    assert.strictEqual(select.children[0].disabled, true);
    assert.ok(select.children[0].textContent.includes('Không tìm thấy tệp pytest'));
    assert.strictEqual(statusPill.className, 'trace-status-pill cut');
    assert.ok(statusPill.textContent.includes('Không tìm thấy tệp pytest'));
  });

  test('loadAvailableTests() hiện HTTP 403 ngay trong ô chọn và trạng thái', async () => {
    const select = global.document.getElementById('e1TestSelect');
    const statusPill = global.document.getElementById('e1StatusPill');
    global.fetch = async () => ({
      ok: false,
      status: 403,
      text: async () => JSON.stringify({ error: '403 Forbidden: không có quyền' })
    });

    await app.loadAvailableTests();

    assert.strictEqual(select.children.length, 1);
    assert.strictEqual(select.children[0].disabled, true);
    assert.ok(select.children[0].textContent.includes('403 Forbidden: không có quyền'));
    assert.strictEqual(statusPill.className, 'trace-status-pill error');
    assert.ok(statusPill.textContent.includes('403 Forbidden: không có quyền'));
  });

  test('loadAvailableTests() không nuốt ngoại lệ kết nối', async () => {
    const select = global.document.getElementById('e1TestSelect');
    const statusPill = global.document.getElementById('e1StatusPill');
    global.fetch = async () => {
      throw new Error('mất kết nối thử nghiệm');
    };

    await app.loadAvailableTests();

    assert.strictEqual(select.children.length, 1);
    assert.strictEqual(select.children[0].disabled, true);
    assert.ok(select.children[0].textContent.includes('mất kết nối thử nghiệm'));
    assert.strictEqual(statusPill.className, 'trace-status-pill error');
    assert.ok(statusPill.textContent.includes('mất kết nối thử nghiệm'));
  });

  test('renderE1Results() dựng cây DOM với đầy đủ thông tin mốc E1', () => {
    const container = new FakeElement('div');
    const statusPill = global.document.getElementById('e1StatusPill');

    const fakeResponse = {
      trang_thai: 'tim_thay',
      source_path: 'core/dong_ho.py',
      source_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      test_file: 'tests/test_dong_ho.py',
      test_sha256: 'a' * 64,
      selected_test: 'tests/test_dong_ho.py::test_dong_ho_chay_dung',
      other_red_test_count: 0,
      candidate_count_before: 1,
      candidate_count_after: 1,
      elapsed_filter_mutate_s: 1.25,
      elapsed_full_suite_s: 0.85,
      reason: '1 ứng viên vượt qua toàn bộ test suite',
      limitation: 'Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.',
      candidates: [
        {
          line: 23,
          operation: 'so sánh Lt -> LtE',
          selected_test_status: 'XANH',
          full_suite_status: 'XANH',
          unified_diff: '--- a/core/dong_ho.py\n+++ b/core/dong_ho.py\n@@ -23,1 +23,1 @@\n-    return x < 0\n+    return x <= 0\n'
        }
      ]
    };

    app.renderE1Results(fakeResponse, container);

    assert.strictEqual(statusPill.textContent, 'TÌM THẤY');
    assert.strictEqual(container.children.length, 5);

    // 1. Notice tạm
    assert.strictEqual(container.children[0].className, 'e1-notice-box e1-notice-temp');
    assert.ok(container.children[0].textContent.includes('Phân tích trên bản sao; tệp thật chưa đổi'));

    // 2. Summary Card
    assert.strictEqual(container.children[1].className, 'e1-summary-card');

    // 3. Candidates
    assert.strictEqual(container.children[2].className, 'e1-summary-title');
    assert.strictEqual(container.children[3].className, 'e1-candidate-card');

    // 4. Diff content inside candidate card
    const diffContainer = container.children[3].children.find(c => c.className === 'e1-diff-container');
    assert.ok(diffContainer, 'Phải có e1-diff-container');
    assert.strictEqual(diffContainer.children.length, 6);
  });

  test('renderE1Error() hiển thị thông báo lỗi đã escape', () => {
    const container = new FakeElement('div');
    app.renderE1Error('Lỗi <tag> nguy hiểm', container);
    assert.ok(container.innerHTML.includes('&lt;tag&gt;'));
  });

  test('renderE1Results() cho ca ung_vien_khong_qua_suite hiển thị giải thích và không có nút áp dụng', () => {
    const container = new FakeElement('div');
    const statusPill = global.document.getElementById('e1StatusPill');

    const fakeRejectedResponse = {
      trang_thai: 'ung_vien_khong_qua_suite',
      source_path: 'core/may_tinh.py',
      source_sha256: 'a'.repeat(64),
      test_file: 'tests/test_may_tinh.py',
      test_sha256: 'b'.repeat(64),
      selected_test: 'tests/test_may_tinh.py::test_may_tinh_co_ban',
      other_red_test_count: 2,
      candidate_count_before: 65,
      candidate_count_after: 15,
      elapsed_filter_mutate_s: 3.5,
      elapsed_full_suite_s: 18.2,
      reason: 'Có 1 ứng viên làm xanh test chọn nhưng không vượt qua toàn bộ test suite.',
      limitation: 'Chỉ dò được 5 họ lỗi so sánh/logic. Đã thử 64 lỗi NGOÀI 5 họ đó — không dò ra ca nào.',
      candidates: [
        {
          line: 40,
          operation: 'bỏ return, hàm trả None',
          selected_test_status: 'XANH',
          full_suite_status: 'ĐỎ',
          so_test_hong: 4,
          unified_diff: '--- a/core/may_tinh.py\n+++ b/core/may_tinh.py\n@@ -40,1 +40,1 @@\n-    return res\n+    res\n',
          ma: 'def f(): pass\n'
        }
      ]
    };

    app.renderE1Results(fakeRejectedResponse, container, 22.5);

    assert.strictEqual(statusPill.textContent, 'ỨNG VIÊN KHÔNG QUA TOÀN BỘ TEST');

    // Kiểm tra Summary card chứa câu giải thích sư phạm
    const summaryCard = container.children[1];
    const noticeRejected = summaryCard.children.find(c => c.className && c.className.includes('e1-notice-rejected'));
    assert.ok(noticeRejected, 'Phải có notice e1-notice-rejected');
    assert.ok(noticeRejected.innerHTML.includes('Sửa một chỗ mà hỏng chỗ khác thì không phải sửa'));
    assert.ok(noticeRejected.innerHTML.includes('KHÔNG đề nghị áp dụng'));

    // Kiểm tra danh sách ứng viên có tiêu đề "Danh Sách Ứng Viên Bị Loại"
    const candTitle = container.children.find(c => c.className === 'e1-summary-title' && c.textContent.includes('Danh Sách Ứng Viên Bị Loại'));
    assert.ok(candTitle, 'Tiêu đề phải là Danh Sách Ứng Viên Bị Loại');

    // Kiểm tra candidate card chứa badge báo số test khác hỏng
    const candCard = container.children.find(c => c.className === 'e1-candidate-card');
    assert.ok(candCard);
    const suiteBadge = candCard.children[0].children[1].children.find(b => b.textContent.includes('Suite: ĐỎ (4 test khác hỏng)'));
    assert.ok(suiteBadge, 'Phải có badge ghi rõ số test hỏng');

    // Khẳng định KHÔNG có nút 'Áp dụng'
    const allButtons = container.querySelectorAll('button');
    assert.strictEqual(allButtons.length, 0, 'Tuyệt đối không có nút bấm Áp dụng cho ứng viên bị loại');

    // Kiểm tra limitation notice đọc động
    const limitNotice = container.children[container.children.length - 1];
    assert.ok(limitNotice.textContent.includes('Đã thử 64 lỗi NGOÀI 5 họ đó — không dò ra ca nào'));
  });

  test('renderE1Results() cho ca suite_khong_do_duoc hiển thị đúng chữ không đo được và lý do', () => {
    const container = new FakeElement('div');
    const statusPill = global.document.getElementById('e1StatusPill');

    const fakeTimeoutResponse = {
      trang_thai: 'suite_khong_do_duoc',
      source_path: 'core/dong_ho.py',
      source_sha256: 'a'.repeat(64),
      test_file: 'tests/test_dong_ho.py',
      test_sha256: 'b'.repeat(64),
      selected_test: 'tests/test_dong_ho.py::test_dong_ho_chay_dung',
      other_red_test_count: 0,
      candidate_count_before: 1,
      candidate_count_after: 1,
      elapsed_filter_mutate_s: 0.5,
      elapsed_full_suite_s: 1.0,
      reason: 'Ứng viên làm xanh test chọn nhưng suite không đo được (Quá giờ (1.0s)).',
      candidates: [
        {
          index: 0,
          line: 23,
          operation: 'logic And -> Or',
          selected_test_status: 'XANH',
          full_suite_status: 'suite_khong_do_duoc',
          ly_do_suite: 'Quá giờ (1.0s)',
          so_test_hong: 0,
          unified_diff: '--- a/core/dong_ho.py\n+++ b/core/dong_ho.py\n@@ -23,1 +23,1 @@\n-    now and ...\n+    now or ...\n'
        }
      ]
    };

    app.renderE1Results(fakeTimeoutResponse, container);

    assert.strictEqual(statusPill.textContent, 'SUITE KHÔNG ĐO ĐƯỢC');
    const candCard = container.children.find(c => c.className === 'e1-candidate-card');
    assert.ok(candCard);
    const suiteBadge = candCard.children[0].children[1].children.find(b => b.textContent.includes('Suite: không đo được (Quá giờ (1.0s))'));
    assert.ok(suiteBadge, 'Phải có badge ghi rõ không đo được kèm lý do');
    assert.ok(!container.textContent.includes('1 test khác hỏng'), 'Không được bịa số 1 test khác hỏng');
  });

});
