// tests/test_phim_tat_phai_duoc_nghe.js
//
// 30/08/2026. Tooltip của btnPresentation ghi "(Alt+P / F11)" từ đầu, nhưng
// chuỗi 'F11' KHÔNG xuất hiện một lần nào trong app.js.
//
// Đo tay, cùng một trạng thái, chỉ khác cái phím:
//     Alt+P  ->  vào Trình Chiếu, defaultPrevented = true
//     F11    ->  không đổi gì,    defaultPrevented = FALSE
// `defaultPrevented = false` nghĩa là KHÔNG handler nào chạm tới phím đó. Một
// lời hứa in ngay trên tooltip mà mã không giữ — cùng họ với nhãn nút nói sai
// việc ở CLAUDE.md mục 4.
//
// Mỗi dòng "Ctrl+S" trong một tooltip LÀ một lời hứa. Cửa này đòi: phím nào app
// quảng cáo thì mã phải nghe.
//
// ĐỘ NHIỄU, đo trước khi viết: sau khi nối F11, 19 phím được quảng cáo và 0 phím
// thiếu. Nếu con số ấy phình lên thì ĐỪNG nới danh sách — hoặc nối phím vào, hoặc
// bỏ nó khỏi tooltip. Hứa rồi không làm là thứ tệ hơn cả hai.
//
// GIỚI HẠN: cửa so PHẦN PHÍM (chữ cuối sau dấu +), không so tổ hợp phím bổ trợ.
// "Ctrl+B" được coi là đủ nếu mã có so `e.key === 'b'` ở đâu đó — kể cả khi chỗ
// ấy đòi Alt chứ không phải Ctrl. Nó bắt được cái ĐÃ bắt: một phím không được
// nghe Ở ĐÂU CẢ. Tổ hợp sai thì vẫn phải bấm tay.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

// 30/08/2026 — bọc qua bocChuThich(). Gieo thử chứng minh cửa này TỪNG bị
// lừa: xoá dòng mã thật và để lại một chú thích mang đúng chữ cửa tìm thì nó
// VẪN XANH. 5/6 cửa dò chuỗi dính bệnh này; cái duy nhất thoát là cái CHẠY mã.
// Xem tools/boc_chu_thich.js.
const { bocChuThich, bocMoiChuThich } = require('../tools/boc_chu_thich.js');

const W = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const HTML = bocChuThich(fs.readFileSync(path.join(W, 'index.html'), 'utf8'));
const APP_JS = bocMoiChuThich(fs.readFileSync(path.join(W, 'app.js'), 'utf8'));

const RE_PHIM = /\b((?:Ctrl|Alt|Shift)\s*\+\s*(?:Shift\s*\+\s*)?[A-Za-z0-9]+|F\d{1,2})\b/g;

// Tên hiển thị -> giá trị e.key mà trình duyệt thật sự gửi.
const DOI_TEN = {
  left: 'arrowleft', right: 'arrowright', up: 'arrowup', down: 'arrowdown',
  esc: 'escape', del: 'delete', ins: 'insert', space: ' ',
};

function phimDuocQuangCao() {
  const ra = new Map();   // phím -> danh sách tooltip nhắc tới nó
  const re = /(?:title|aria-label|placeholder)="([^"]*)"/g;
  let m;
  while ((m = re.exec(HTML)) !== null) {
    const chu = m[1];
    for (const p of chu.match(RE_PHIM) || []) {
      const k = p.replace(/\s+/g, '');
      if (!ra.has(k)) ra.set(k, []);
      ra.get(k).push(chu.slice(0, 56));
    }
  }
  return ra;
}

function phimDuocNghe() {
  const ra = new Set();
  for (const m of APP_JS.matchAll(/\.key\s*===?\s*['"]([^'"]+)['"]/g)) ra.add(m[1].toLowerCase());
  for (const m of APP_JS.matchAll(/\.code\s*===?\s*['"]([^'"]+)['"]/g)) ra.add(m[1].toLowerCase());
  return ra;
}

test('mọi phím tắt app quảng cáo trên tooltip đều phải được mã nghe', () => {
  const quangCao = phimDuocQuangCao();
  const nghe = phimDuocNghe();
  const thieu = [];
  for (const [phim, cho] of quangCao) {
    const phan = phim.split('+').pop().toLowerCase();
    const ten = DOI_TEN[phan] || phan;
    if (!nghe.has(ten) && !nghe.has(phan)) {
      thieu.push(`${phim} — hứa ở: "${cho[0]}"`);
    }
  }
  assert.deepStrictEqual(thieu, [],
    'phím được quảng cáo nhưng không dòng nào trong app.js so với nó. ' +
    'Hoặc nối phím vào, hoặc bỏ nó khỏi tooltip — hứa rồi không làm là tệ hơn cả hai');
});

test('phép quét thật sự tìm được gì đó — không phải xanh rỗng', () => {
  const quangCao = phimDuocQuangCao();
  const nghe = phimDuocNghe();

  // KHÔNG canh bằng một NGƯỠNG ĐẾM. Gieo thử đo được: đổi MỘT `title=` thành
  // `data-title=` chỉ làm mất 2 phím, còn 17 — vẫn qua ngưỡng 15, cửa VẪN XANH
  // dù bộ tách đã mù đúng chỗ đó. Một con số đặt tay thì lần sau lại sai.
  // Canh bằng những phím CỤ THỂ phải tìm ra được: mất bất kỳ cái nào là bộ tách
  // đã đánh rơi đúng tooltip mang nó.
  const PHAI_TIM_RA = ['Ctrl+S', 'Ctrl+F', 'Ctrl+B', 'Ctrl+J', 'Alt+P', 'F11', 'F9', 'F10'];
  const mat = PHAI_TIM_RA.filter((p) => !quangCao.has(p));
  assert.deepStrictEqual(mat, [],
    'bộ tách HTML không còn thấy các phím này trên tooltip nữa. Hoặc tooltip đã ' +
    'đổi (thì sửa danh sách một cách CÓ Ý), hoặc bộ tách đã hỏng — mà bộ tách ' +
    'hỏng thì khẳng định chính xanh vì không quét được gì');

  const PHAI_NGHE = ['s', 'f', 'b', 'j', 'p', 'f11', 'f9', 'f10'];
  const khongNghe = PHAI_NGHE.filter((k) => !nghe.has(k));
  assert.deepStrictEqual(khongNghe, [],
    'bộ tách JS không còn thấy các giá trị e.key này trong app.js');
});

test('F11 phải còn được nghe — đúng chỗ đã hỏng', () => {
  assert.ok(phimDuocNghe().has('f11'),
    'F11 lại biến mất khỏi app.js trong khi tooltip vẫn hứa "Alt+P / F11"');
  assert.match(HTML, /Alt\+P \/ F11/,
    'tooltip đổi rồi — nếu đã bỏ F11 khỏi lời hứa thì bỏ luôn khẳng định này');
});
