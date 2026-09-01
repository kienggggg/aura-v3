// tests/test_dong_tab_giu_cho.js
//
// Đóng một tab KHÁC thì phải ở nguyên tệp mình đang xem.
//
// VÌ SAO CÓ TỆP NÀY. 01/09/2026, trong lúc mở lại thanh tab cho điện thoại,
// bấm thử ✕ như người dùng thì màn hình nhảy sang tệp khác. Đo trên cả hai
// khung nên không phải chuyện bố cục:
//
//     mobile 375    đang ở tab 0 "1. Hàm cộng hai số", bấm ✕ của tab 3
//                   ->  màn hình thành dong_ho.py
//     desktop 1476  active 0 -> 1, tên "1. Hàm cộng hai số" -> paths.py
//
// `dongTab()` gọi `napTab(Math.min(i, ...))` cho MỌI trường hợp, không hỏi tab
// nào đang mở. Dọn một tệp không liên quan là mất chỗ mình đang làm.
//
// KHÔNG MẤT DỮ LIỆU — đã đo, và đây là chỗ tôi suýt báo sai: lúc đầu tôi kết
// luận "mất cả sửa chưa lưu" vì sau khi đóng thì `hasModifications` là false.
// Quay lại tab cũ thì sửa vẫn còn nguyên (`state.tree` là CÙNG MỘT tham chiếu
// với bản trong `state.tabs`). Nên đây là mất CHỖ ĐANG XEM, không phải mất
// việc đã làm. Vẫn phải sửa: người đang gõ dở bị ném sang tệp khác.
//
// Cửa này CHẠY THẬT `dongTab` trích ra khỏi app.js, không dò chuỗi trên nó —
// theo lối `test_o_tim.js`, cửa duy nhất trong sáu cửa ngày 30/08 không bị chú
// thích lừa, vì nó thi hành mã chứ không đọc mã.
//
// GIỚI HẠN: cửa chạy `dongTab` tách khỏi trình duyệt với `napTab` giả, nên nó
// KHÔNG chứng minh nút ✕ nối đúng vào hàm này. Phần ấy vẫn phải bấm tay — và
// đã bấm: bốn ca A/B/C/D trên trình duyệt thật, xem thân bài commit.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');

function trichKhoi(neo) {
  const i = APP_JS.indexOf(neo);
  assert.notStrictEqual(i, -1, 'không tìm thấy: ' + neo);
  let j = APP_JS.indexOf('{', i) + 1;
  let sau = 1;
  while (sau > 0) {
    assert.ok(j < APP_JS.length, 'ngoặc không đóng sau: ' + neo);
    const ch = APP_JS[j];
    if (ch === '{') sau += 1;
    else if (ch === '}') sau -= 1;
    j += 1;
  }
  return APP_JS.slice(i, j);
}

/**
 * Dựng một bàn thử: `dongTab` thật, còn mọi thứ nó gọi thì giả.
 *
 * `napTab` giả chỉ ghi lại NÓ ĐƯỢC GỌI VỚI CHỈ SỐ NÀO và đặt `tabActive` —
 * đúng phần việc mà lỗi nằm ở đó. Không giả lập DOM.
 */
function banThu({ tabs, tabActive, dongY = true }) {
  const state = { tabs: tabs.map((t) => ({ ...t })), tabActive };
  const nhatKy = { napTab: [], veThanhTab: 0, xoaLichSu: 0, hoi: [] };

  const nguon = `
    const nhatKy = arguments[0], state = arguments[1], dongY = arguments[2];
    const window = { confirm: (c) => { nhatKy.hoi.push(c); return dongY; } };
    function napTab(i) { nhatKy.napTab.push(i); state.tabActive = i; }
    function veThanhTab() { nhatKy.veThanhTab += 1; }
    function xoaLichSu() { nhatKy.xoaLichSu += 1; }
    ${trichKhoi('function dongTab(i) {')}
    return dongTab;
  `;
  const dongTab = new Function(nguon)(nhatKy, state, dongY);
  return { state, nhatKy, dongTab };
}

const BA_TAB = [
  { ten_tep: 'a.py', hasModifications: false },
  { ten_tep: 'b.py', hasModifications: false },
  { ten_tep: 'c.py', hasModifications: false },
];

test('bàn thử tự nó phải chạy — không thì mọi khẳng định dưới vô nghĩa', () => {
  // Ca đối chứng cho chính máy đo: một lời gọi CHẮC CHẮN không làm gì.
  const b = banThu({ tabs: BA_TAB, tabActive: 0 });
  b.dongTab(99);
  assert.strictEqual(b.state.tabs.length, 3, 'chỉ số ngoài khoảng phải bị bỏ qua');
  b.dongTab(-1);
  assert.strictEqual(b.state.tabs.length, 3);
  assert.deepStrictEqual(b.nhatKy.napTab, [], 'không được nạp gì cả');
});

test('đang xem tab 2, đóng tab 0 (TRƯỚC nó) — ở nguyên chỗ, chỉ số tụt 1', () => {
  const b = banThu({ tabs: BA_TAB, tabActive: 2 });
  b.dongTab(0);
  assert.deepStrictEqual(b.state.tabs.map((t) => t.ten_tep), ['b.py', 'c.py']);
  assert.strictEqual(b.state.tabs[b.state.tabActive].ten_tep, 'c.py',
    'phải vẫn là c.py — đây đúng là lỗi đo được trên trình duyệt 01/09');
  assert.strictEqual(b.state.tabActive, 1, 'c.py trượt từ vị trí 2 xuống 1');
  assert.deepStrictEqual(b.nhatKy.napTab, [],
    'KHÔNG được gọi napTab: màn hình đã đúng rồi, nạp lại chỉ dựng lại DOM và ' +
    'mất vị trí con trỏ người dùng đang gõ');
  assert.strictEqual(b.nhatKy.veThanhTab, 1, 'vẫn phải vẽ lại thanh tab');
});

test('đang xem tab 0, đóng tab 2 (SAU nó) — ở nguyên, chỉ số không đổi', () => {
  const b = banThu({ tabs: BA_TAB, tabActive: 0 });
  b.dongTab(2);
  assert.deepStrictEqual(b.state.tabs.map((t) => t.ten_tep), ['a.py', 'b.py']);
  assert.strictEqual(b.state.tabs[b.state.tabActive].ten_tep, 'a.py');
  assert.strictEqual(b.state.tabActive, 0, 'đóng tab nằm SAU thì chỉ số giữ nguyên');
  assert.deepStrictEqual(b.nhatKy.napTab, []);
});

test('đóng CHÍNH tab đang xem — buộc phải sang tệp khác', () => {
  const b = banThu({ tabs: BA_TAB, tabActive: 1 });
  b.dongTab(1);
  assert.deepStrictEqual(b.state.tabs.map((t) => t.ten_tep), ['a.py', 'c.py']);
  assert.deepStrictEqual(b.nhatKy.napTab, [1],
    'tệp đang xem vừa bị đóng nên phải nạp tệp đã trượt vào chỗ trống');
  assert.strictEqual(b.state.tabs[b.state.tabActive].ten_tep, 'c.py');
});

test('đóng chính tab CUỐI DÃY — lùi về tab liền trước, không lỗi chỉ số', () => {
  const b = banThu({ tabs: BA_TAB, tabActive: 2 });
  b.dongTab(2);
  assert.deepStrictEqual(b.state.tabs.map((t) => t.ten_tep), ['a.py', 'b.py']);
  assert.deepStrictEqual(b.nhatKy.napTab, [1],
    'không kẹp lại thì napTab(2) trên mảng còn 2 phần tử -> ra ngoài khoảng');
  assert.strictEqual(b.state.tabs[b.state.tabActive].ten_tep, 'b.py');
});

test('đóng tab CUỐI CÙNG còn lại — về bản nháp, không để màn hình trống', () => {
  const b = banThu({ tabs: [{ ten_tep: 'a.py', hasModifications: false }], tabActive: 0 });
  b.dongTab(0);
  assert.strictEqual(b.state.tabs.length, 1);
  assert.strictEqual(b.state.tabs[0].ten_tep, 'Chưa đặt tên');
  assert.deepStrictEqual(b.state.tabs[0].tree, []);
  assert.deepStrictEqual(b.nhatKy.napTab, [0]);
  assert.strictEqual(b.nhatKy.xoaLichSu, 1, 'lịch sử của tệp cũ phải bị dọn');
});

test('tab có sửa chưa lưu thì phải HỎI, và trả lời KHÔNG là không đóng', () => {
  const tabs = [
    { ten_tep: 'a.py', hasModifications: false },
    { ten_tep: 'b.py', hasModifications: true },
    { ten_tep: 'c.py', hasModifications: false },
  ];
  const khong = banThu({ tabs, tabActive: 0, dongY: false });
  khong.dongTab(1);
  assert.strictEqual(khong.state.tabs.length, 3, 'trả lời KHÔNG mà vẫn đóng');
  assert.strictEqual(khong.nhatKy.hoi.length, 1);
  assert.ok(khong.nhatKy.hoi[0].includes('b.py'),
    'câu hỏi phải gọi TÊN tệp sắp mất, không thì người dùng không biết đang bỏ gì');

  const co = banThu({ tabs, tabActive: 0, dongY: true });
  co.dongTab(1);
  assert.strictEqual(co.state.tabs.length, 2);
  assert.strictEqual(co.state.tabActive, 0, 'đồng ý đóng b.py thì vẫn ở a.py');
});

test('không hỏi thừa khi tab sạch — hỏi mỗi lần là dạy người dùng bấm bừa', () => {
  const b = banThu({ tabs: BA_TAB, tabActive: 0 });
  b.dongTab(1);
  assert.deepStrictEqual(b.nhatKy.hoi, []);
});
