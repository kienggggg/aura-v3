// tests/test_nut_chi_icon.js
//
// Nút thu về chỉ còn biểu tượng, và chú thích hiện khi di chuột vào.
//
// VÌ SAO CÓ TỆP NÀY. 01/09/2026, Sếp: "các nút cảm giác hơi to, làm cái biểu
// tượng là được rồi, khi di chuột vào là có chú thích". Đo trước khi sửa: 18
// nút trên thanh đầu cộng lại 1.536px bề ngang, riêng chín nút nhóm phụ đã
// 991px. Sau khi sửa: nhóm phụ 350px, tổng 807px.
//
// HAI ĐIỀU PHẢI KIỂM TRƯỚC KHI GIẤU CHỮ — giấu bừa là để lại ô vuông câm:
//     18/18 nút đã có `title` sẵn     -> không nút nào mất tên gọi
//     9/9 nút nhóm phụ đều có <svg>   -> không nút nào thành ô rỗng
// Cửa này đóng đinh điều thứ nhất thành LUẬT trong mã: nút nào không có tên
// gọi thì KHÔNG được giấu chữ.
//
// Ô chú thích phải nằm ở gốc `<body>`, không vẽ bằng `::after` trên chính nút.
// Đo bằng cách chèn một ô thật vào `#btnSamples`: đáy ô ở y=67 còn hộp cuộn
// `.header-actions-scroll` kết thúc ở y=49 — BỊ CẮT 18px, vì hộp ấy phải có
// `overflow-y: hidden` để `overflow-x: auto` hoạt động.
//
// Cửa CHẠY THẬT `dungNutChiIcon` trích ra khỏi app.js trên một DOM giả, theo
// lối `test_o_tim.js` — thi hành mã chứ không đọc mã.
//
// GIỚI HẠN: DOM giả không có bố cục thật, nên phép kẹp mép màn hình được kiểm
// bằng số do chính bàn thử đặt ra, không phải bằng bố cục thật của app. Việc
// tooltip có ra đúng chỗ trên màn hình thì đã bấm tay (xem thân bài commit).

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { bocChuThich } = require('../tools/boc_chu_thich.js');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const doc = (ten) => fs.readFileSync(path.join(THU_MUC, ten), 'utf8');
const APP_JS = doc('app.js');
const HTML = bocChuThich(doc('index.html'));
const CSS = bocChuThich(doc('style.css'));

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

/** Nút giả — chỉ đủ những gì `dungNutChiIcon` thật sự đụng tới. */
function nutGia(id, thuoc, hop = { left: 100, right: 135, top: 10, bottom: 42, width: 35 }) {
  const t = { ...thuoc };
  return {
    id,
    _hop: hop,
    lop: new Set(),
    classList: { add: (c) => t && undefined, contains: (c) => false },
    getAttribute: (k) => (k in t ? t[k] : null),
    setAttribute: (k, v) => { t[k] = v; },
    removeAttribute: (k) => { delete t[k]; },
    getBoundingClientRect: () => hop,
    closest: () => null,
    _thuoc: t,
  };
}

function banThu({ nut, coOChuThich = true, manHinh = { w: 1000, h: 800 } }) {
  // `classList.add` thật (ghi vào Set) — phần trên chỉ là khung.
  nut.forEach((b) => { b.classList = { add: (c) => b.lop.add(c), contains: (c) => b.lop.has(c) }; });

  const o = coOChuThich ? {
    id: 'chuThichNoi', hidden: true, textContent: '', style: {},
    _w: 170, _h: 28,
    getBoundingClientRect() { return { width: this._w, height: this._h }; },
  } : null;

  const nghe = {};
  const doc_ = {
    getElementById: (id) => (id === 'chuThichNoi' ? o : null),
    querySelectorAll: () => nut,
    addEventListener: (loai, f) => { (nghe[loai] = nghe[loai] || []).push(f); },
    documentElement: { clientWidth: manHinh.w, clientHeight: manHinh.h },
  };
  const win = { addEventListener: (loai, f) => { (nghe[loai] = nghe[loai] || []).push(f); } };

  const nguon = `
    const document = arguments[0], window = arguments[1];
    const setTimeout = arguments[2], clearTimeout = arguments[3];
    ${trichKhoi("const NUT_CHI_ICON = '")};
    ${trichKhoi('function dungNutChiIcon() {')}
    return { dungNutChiIcon, NUT_CHI_ICON };
  `;
  // Đồng hồ giả: `hen` chạy ngay khi ta gọi `chayHen()`, không chờ thật.
  const cacHen = [];
  const setTimeoutGia = (f, ms) => { cacHen.push({ f, ms }); return cacHen.length - 1; };
  const clearTimeoutGia = (i) => { if (cacHen[i]) cacHen[i].f = null; };

  const api = new Function(nguon)(doc_, win, setTimeoutGia, clearTimeoutGia);
  api.dungNutChiIcon();
  return {
    o, nghe, nut, api, cacHen,
    chayHen: () => cacHen.forEach((h) => h.f && h.f()),
  };
}

test('bàn thử tự nó phải chạy', () => {
  // Ca đối chứng cho chính máy đo.
  const b = banThu({ nut: [nutGia('x', { title: 'Một nút' })] });
  assert.ok(b.api.NUT_CHI_ICON.includes('header-actions-scroll'),
    'bộ chọn phải nhắm nhóm phụ, không thì cửa đang đo một thứ khác');
  assert.ok(b.nghe.mouseover && b.nghe.mouseover.length > 0,
    'không có handler `mouseover` — chú thích sẽ không bao giờ hiện');
});

test('title chuyển sang aria-label và title bị bỏ (khỏi chú thích kép)', () => {
  const n = nutGia('btnSamples', { title: 'Kho Workflow & Dự án mẫu' });
  banThu({ nut: [n] });
  assert.strictEqual(n.getAttribute('aria-label'), 'Kho Workflow & Dự án mẫu',
    'không chép sang aria-label là nút mất tên gọi với trình đọc màn hình');
  assert.strictEqual(n.getAttribute('title'), null,
    'còn `title` thì trình duyệt hiện thêm ô chú thích thứ hai của chính nó, ' +
    'chậm hơn và khác kiểu — hai ô chồng nhau');
  assert.ok(n.lop.has('nut-chi-icon'));
});

test('NÚT KHÔNG CÓ TÊN GỌI thì KHÔNG được giấu chữ', () => {
  // Đây là luật an toàn, không phải tiện nghi: giấu nhãn của một nút không có
  // `title` lẫn `aria-label` là biến nó thành ô vuông câm, không ai đoán nổi.
  const cam = nutGia('btnKhongTen', {});
  const rong = nutGia('btnTitleRong', { title: '   ' });
  banThu({ nut: [cam, rong] });
  for (const n of [cam, rong]) {
    assert.ok(!n.lop.has('nut-chi-icon'),
      `${n.id}: bị giấu chữ dù không có tên gọi nào thay thế`);
  }
});

test('aria-label có sẵn thì dùng luôn, không cần title', () => {
  const n = nutGia('btnCoAria', { 'aria-label': 'Đã có sẵn' });
  banThu({ nut: [n] });
  assert.ok(n.lop.has('nut-chi-icon'));
  assert.strictEqual(n.getAttribute('aria-label'), 'Đã có sẵn');
});

test('chuột phải CHỜ rồi mới hiện; rời chuột là ẩn', () => {
  const n = nutGia('btnNew', { title: 'Tạo chương trình mới' });
  const b = banThu({ nut: [n] });
  const nut = { closest: (s) => (s === '.nut-chi-icon' ? n : null) };
  n.closest = (s) => (s === '.nut-chi-icon' ? n : null);

  b.nghe.mouseover.forEach((f) => f({ target: nut }));
  assert.strictEqual(b.o.hidden, true,
    'hiện NGAY khi chuột lướt qua thì kéo ngang chín nút thành một dải chớp nháy');
  assert.ok(b.cacHen.length > 0 && b.cacHen[0].ms >= 150,
    `độ trễ ${b.cacHen[0] && b.cacHen[0].ms}ms — quá ngắn thì vẫn nháy`);

  b.chayHen();
  assert.strictEqual(b.o.hidden, false);
  assert.strictEqual(b.o.textContent, 'Tạo chương trình mới');

  b.nghe.mouseout.forEach((f) => f({ target: nut }));
  assert.strictEqual(b.o.hidden, true, 'rời chuột mà ô chú thích còn nằm đó');
});

test('bàn phím: Tab tới nút là hiện NGAY, không chờ', () => {
  const n = nutGia('btnSaveFile', { title: 'Lưu tệp' });
  const b = banThu({ nut: [n] });
  n.closest = (s) => (s === '.nut-chi-icon' ? n : null);
  b.nghe.focusin.forEach((f) => f({ target: n }));
  assert.strictEqual(b.o.hidden, false,
    'người dùng đã cố ý Tab tới nút rồi, bắt chờ thêm là vô lý');
  assert.strictEqual(b.o.textContent, 'Lưu tệp');
  b.nghe.focusout.forEach((f) => f({ target: n }));
  assert.strictEqual(b.o.hidden, true);
});

test('bấm nút · Escape · cuộn trang đều làm ẩn chú thích', () => {
  for (const loai of ['click', 'keydown', 'scroll']) {
    const n = nutGia('btnNew', { title: 'Tạo chương trình mới' });
    const b = banThu({ nut: [n] });
    n.closest = (s) => (s === '.nut-chi-icon' ? n : null);
    b.nghe.focusin.forEach((f) => f({ target: n }));
    assert.strictEqual(b.o.hidden, false, 'chưa hiện thì không kiểm được việc ẩn');
    assert.ok(b.nghe[loai], `không ai nghe \`${loai}\``);
    b.nghe[loai].forEach((f) => f({ key: 'Escape', target: n }));
    assert.strictEqual(b.o.hidden, true,
      loai === 'click'
        ? 'bấm nút là mở hộp thoại — giữ ô chú thích thì nó đè lên thứ vừa mở'
        : `\`${loai}\` không làm ẩn ô chú thích`);
  }
});

test('ô chú thích luôn nằm TRONG màn hình', () => {
  // Nút sát mép phải: nếu cứ đặt giữa nút thì ô 170px sẽ thò ra ngoài.
  const n = nutGia('btnPresentation', { title: 'Chế độ Trình chiếu toàn màn hình' },
    { left: 950, right: 985, top: 10, bottom: 42, width: 35 });
  const b = banThu({ nut: [n], manHinh: { w: 1000, h: 800 } });
  n.closest = (s) => (s === '.nut-chi-icon' ? n : null);
  b.nghe.focusin.forEach((f) => f({ target: n }));
  const trai = parseInt(b.o.style.left, 10);
  assert.ok(trai >= 0, `left = ${trai}px, âm là thò ra khỏi mép trái`);
  assert.ok(trai + b.o._w <= 1000,
    `mép phải ${trai + b.o._w} > 1000 — ô chú thích thò ra ngoài màn hình`);
});

test('không đủ chỗ bên dưới thì LẬT LÊN TRÊN', () => {
  const n = nutGia('btnX', { title: 'Nút sát đáy' },
    { left: 100, right: 135, top: 760, bottom: 792, width: 35 });
  const b = banThu({ nut: [n], manHinh: { w: 1000, h: 800 } });
  n.closest = (s) => (s === '.nut-chi-icon' ? n : null);
  b.nghe.focusin.forEach((f) => f({ target: n }));
  const tren = parseInt(b.o.style.top, 10);
  assert.ok(tren < 760,
    `top = ${tren}px, vẫn vẽ bên dưới một nút cách đáy 8px — ô sẽ bị cắt`);
});

test('ô chú thích ở gốc body và position: fixed', () => {
  // Không phải chuyện thẩm mỹ: `.header-actions-scroll` buộc phải có
  // `overflow-y: hidden`, và đo được là nó cắt mất 18px của ô vẽ dưới nút.
  assert.ok(/id="chuThichNoi"/.test(HTML), 'thiếu ô chú thích trong index.html');
  const vtHeader = HTML.indexOf('</header>');
  const vtO = HTML.indexOf('id="chuThichNoi"');
  assert.ok(vtO > vtHeader,
    'ô chú thích nằm TRONG <header> — hộp cuộn ở đó sẽ cắt mất nó');

  const khoi = CSS.match(/\.chu-thich-noi\s*\{([^}]*)\}/);
  assert.ok(khoi, 'thiếu luật .chu-thich-noi');
  assert.ok(/position:\s*fixed/.test(khoi[1]),
    'không `fixed` thì nó trôi theo trang khi cuộn');
  assert.ok(/pointer-events:\s*none/.test(khoi[1]),
    'ô chú thích ăn mất cú bấm chuột nếu không tắt pointer-events');
});

test('nhãn bị nuốt bằng font-size, không phải display', () => {
  const khoi = CSS.match(/\.nut-chi-icon\s*\{([^}]*)\}/);
  assert.ok(khoi, 'thiếu luật .nut-chi-icon');
  assert.ok(/font-size:\s*0/.test(khoi[1]),
    'nhãn là TEXT NODE TRẦN (`<svg/> + "Kho Workflow"`) — không bộ chọn CSS ' +
    'nào trỏ tới nó được, nên `display: none` vô dụng ở đây');
});

test('CHẠY THỬ giữ nguyên chữ — có chủ đích', () => {
  const bc = trichKhoi("const NUT_CHI_ICON = '").match(/'([^']*)'/)[1];
  assert.ok(!bc.includes('btnRun'),
    'btnRun là nút người mới học phải tìm thấy ngay lần đầu mở app; một tam ' +
    'giác ▶ không nói được "CHẠY THỬ". Thu nhỏ mọi thứ quanh nó là đủ');
  assert.ok(bc.includes('#btnDebug'),
    'GỠ LỖI thì thu được — nó là việc của người đã biết lập trình');
});
