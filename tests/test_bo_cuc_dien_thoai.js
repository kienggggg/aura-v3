// tests/test_bo_cuc_dien_thoai.js
//
// Bố cục điện thoại: khay thẻ trượt lên như bàn phím, ô nhập chạm được.
//
// VÌ SAO CÓ TỆP NÀY. Đo app ở 375x812 ngày 01/09/2026 — trước khi có
// `mobile.css`:
//
//     grid-template-columns   240px / 135px / 0px   (khay / canvas / cột mã)
//     trang tràn ngang        628px, 194 phần tử ngoài khung
//     ba nút Thẻ/Chia/Mã      toạ độ 515-712  ->  NGOÀI màn hình, không bấm được
//     ô nhập trong thẻ        14/14 cao 18px, ngưỡng chạm của iOS là 44px
//
// Ý của Sếp — cho khay thẻ trượt lên như bàn phím ảo — đo ra đúng: canvas đi từ
// 135px lên 375px. Sau khi có tệp này, cùng khung 375x812:
//
//     canvas 375 · tràn 0 · ô nhập 390/390 cao 44px, cỡ chữ 16px
//     khay đóng sẵn lúc mở app · nút CHẠY THỬ trong màn · chia đôi xếp DỌC
//
// Cửa này canh những khai báo mà PHÉP ĐO chứng minh là cần. Nó KHÔNG thay được
// việc mở app ra bấm — CLAUDE.md mục 4: cửa chỉ bắt được "có nút mà không ai
// nghe", ba loại còn lại vẫn phải bắt bằng tay.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { bocChuThich, bocMoiChuThich } = require('../tools/boc_chu_thich.js');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const doc = (ten) => fs.readFileSync(path.join(THU_MUC, ten), 'utf8');

// Bọc chú thích: chú thích ở ĐẦU tệp này và ở đầu `mobile.css` mang đủ mọi chữ
// mà các khẳng định dưới đang tìm. 30/08 đo được 5/6 cửa dò chuỗi bị lừa đúng
// kiểu ấy.
const CSS = bocChuThich(doc('mobile.css'));
const HTML = bocChuThich(doc('index.html'));
const APP_JS = bocMoiChuThich(doc('app.js'));

const NGUONG_CSS = 820;

function khaiBaoCua(boChon, css = CSS) {
  const cacKhoi = [];
  const re = new RegExp(
    `(^|}|\\{)([^{}]*?(?:^|,|\\s)${boChon.replace(/[.#]/g, '\\$&')}\\s*(?:,[^{}]*?)?)\\{([^}]*)\\}`,
    'gm');
  let m;
  while ((m = re.exec(css)) !== null) {
    const dungLa = m[2].split(',').map((s) => s.trim()).some((s) => s === boChon);
    if (dungLa) cacKhoi.push(m[3]);
  }
  const ra = new Map();
  for (const than of cacKhoi) {
    for (const dong of than.split(';')) {
      const i = dong.indexOf(':');
      if (i < 0) continue;
      ra.set(dong.slice(0, i).trim(), dong.slice(i + 1).trim());
    }
  }
  return ra;
}

test('bộ đọc CSS tự nó phải đúng', () => {
  // Ca đối chứng cho chính máy đo. Không có nó thì `khaiBaoCua` trả Map rỗng
  // cho mọi thứ và cả tệp xanh vì lý do sai.
  assert.ok(khaiBaoCua('.sidebar-left').size > 0, 'không đọc nổi .sidebar-left');
  assert.strictEqual(khaiBaoCua('.khong-he-co-abc123').size, 0,
    'đọc ra khai báo cho bộ chọn không tồn tại — bộ đọc khớp bừa');
});

test('mobile.css được nạp SAU style.css', () => {
  const vtStyle = HTML.indexOf('style.css');
  const vtMobile = HTML.indexOf('mobile.css');
  assert.ok(vtMobile > 0, 'index.html chưa nạp mobile.css — cả tệp thành vô nghĩa');
  assert.ok(vtMobile > vtStyle,
    'mobile.css phải nạp SAU: nó cố ý không dùng !important và dựa vào thứ tự ' +
    'để đè. Đảo lại thì mọi luật trong đó im lặng thua');
});

test('ngưỡng của JS TRÙNG ngưỡng của media query', () => {
  // Lệch nhau thì có một dải bề rộng mà CSS vẽ khay trượt còn JS tưởng vẫn ba
  // cột: nền mờ không hiện, chạm ra ngoài không đóng được gì, và khay che 62%
  // màn hình không có lối thoát.
  const mq = CSS.match(/@media\s*\(max-width:\s*(\d+)px\)/);
  assert.ok(mq, 'mobile.css không có @media max-width');
  assert.strictEqual(Number(mq[1]), NGUONG_CSS);

  const js = APP_JS.match(/NGUONG_DIEN_THOAI\s*=\s*(\d+)/);
  assert.ok(js, 'app.js không khai báo NGUONG_DIEN_THOAI');
  assert.strictEqual(Number(js[1]), NGUONG_CSS,
    `JS dùng ${js[1]}px còn CSS dùng ${mq[1]}px — dải ở giữa hai số là vùng chết`);
});

test('khay thẻ là lớp phủ, KHÔNG bóp canvas', () => {
  const kb = khaiBaoCua('.sidebar-left');
  assert.strictEqual(kb.get('position'), 'fixed',
    'không `fixed` thì nó vẫn là một cột và canvas lại còn 135px — đúng thứ ' +
    'tệp này sinh ra để chống');
  assert.strictEqual(kb.get('bottom'), '0', 'khay phải mọc lên từ ĐÁY, như bàn phím');
  assert.ok(kb.has('height'));
  assert.ok(Number(kb.get('z-index')) > 50,
    'khay phải nằm trên thanh chế độ ở đáy, không thì hai thứ chồng chữ lên nhau');
});

test('lớp collapsed đẩy khay xuống dưới màn hình', () => {
  const kb = khaiBaoCua('.app-main.left-collapsed .sidebar-left');
  assert.strictEqual(kb.get('transform'), 'translateY(100%)',
    'thiếu dòng này thì khay đứng yên và luôn che màn hình — đo được: bấm nút ' +
    'khay ba lần, y giữ nguyên 304 cả ba lần');
});

test('ô nhập đủ ngưỡng chạm và không làm iOS tự phóng to', () => {
  const kb = khaiBaoCua('.the input.the-inline-input');
  const cao = parseInt(kb.get('min-height'), 10);
  assert.ok(cao >= 44,
    `min-height ${kb.get('min-height')} — ngưỡng chạm của iOS là 44px. Trước ` +
    'khi có tệp này, 14/14 ô cao 18px');
  const co = parseInt(kb.get('font-size'), 10);
  assert.ok(co >= 16,
    `font-size ${kb.get('font-size')} — Safari trên iOS TỰ PHÓNG TO cả trang ` +
    'khi chạm vào ô có cỡ chữ dưới 16px, và không tự thu lại');
});

test('chia đôi xếp DỌC, và ngắm đúng phần tử', () => {
  const kb = khaiBaoCua('.canvas-center-body.mode-split-view');
  assert.strictEqual(kb.get('flex-direction'), 'column',
    'ở 375px chia ngang thì mỗi nửa còn 187px, không đọc nổi');
  assert.strictEqual(khaiBaoCua('.canvas-workspace').size, 0,
    'lượt viết đầu ngắm `.canvas-workspace` và luật nằm im — nó là khung TRONG ' +
    'của nửa bên trái, không phải chỗ chia. Đừng ngắm lại vào đó');
});

test('nền mờ có thật trong HTML và app.js có nghe nó', () => {
  assert.ok(/id="mobileBackdrop"/.test(HTML), 'thiếu phần tử nền mờ');
  assert.ok(/mobileBackdrop/.test(APP_JS), 'app.js không đụng tới nền mờ');
  assert.ok(/getElementById\('mobileBackdrop'\)[\s\S]{0,400}addEventListener\('click'/.test(APP_JS),
    'nền mờ không có handler `click` — khay che 62% màn hình và lối ra duy ' +
    'nhất là tìm đúng nút nhỏ trên thanh đầu');
});

test('lần mở đầu trên điện thoại phải là khay ĐÓNG', () => {
  assert.ok(/laManHinhHep\(\)[\s\S]{0,200}sidebarLeftCollapsed = true/.test(APP_JS),
    'không ép đóng thì `collapsed` mặc định `false` nghĩa là hai khay trượt ' +
    'lên sẵn: mở app ra thấy một tấm phủ, không thấy canvas');
  assert.ok(/localStorage\.getItem\('aura_sidebar_left_collapsed'\) === null/.test(APP_JS),
    'chỉ được ép ở LẦN ĐẦU. Ép mỗi lần mở là đè lên lựa chọn của người dùng');
});

test('câu báo lỗi bị cắt thì phải còn đường đọc đủ', () => {
  // Bản vá desktop từng ghim `.nhan-nhanh` bằng `flex-shrink: 0`. Đo ở 375:
  // câu 78 ký tự làm ô rộng 473px, trang tràn 243px, btnRun mép phải 526.
  // Nay ô bị cắt bằng `…` — nên câu đầy đủ phải sang `title`, không thì chính
  // câu lỗi người dùng đang cần bị giấu mất.
  const style = bocChuThich(doc('style.css'));
  const kb = khaiBaoCua('.nhan-nhanh', style);
  assert.strictEqual(kb.get('text-overflow'), 'ellipsis');
  assert.notStrictEqual(kb.get('flex-shrink'), '0',
    'ghim lại là thanh đầu lại bị đẩy ra ngoài mỗi khi CÓ lỗi — đúng lúc ' +
    'người dùng cần nó nhất');
  // Neo vào TỪNG HÀM, không dò `o.title = chu` trên cả tệp: gieo thử cho thấy
  // cửa mù đúng chỗ đó. Có hai hàm cùng ghi vào `#nhanNhanh`, nên gỡ `title`
  // khỏi một hàm mà cửa vẫn xanh vì hàm kia còn.
  for (const ten of ['baoNhanh', 'baoDinhNghia']) {
    const bd = APP_JS.indexOf(`function ${ten}(`);
    assert.ok(bd > 0, `không tìm thấy ${ten}()`);
    // Cắt ở KHAI BÁO HÀM KẾ TIẾP, không lấy một cửa sổ đặt tay bao nhiêu ký
    // tự. Bản đầu lấy 900 ký tự và nó trùm sang `baoDinhNghia` — gieo thử gỡ
    // `title` khỏi `baoNhanh` mà cửa VẪN XANH, vì nó bắt được `o.title` của
    // hàm bên cạnh. Cùng họ với lỗi "cửa sổ 260 ký tự" ở CLAUDE.md mục 4.
    const ke = APP_JS.indexOf('\n  function ', bd + 1);
    const than = APP_JS.slice(bd, ke > bd ? ke : bd + 900);
    assert.ok(/o\.title = chu/.test(than),
      `${ten}() không gán \`title\` — nó ghi vào #nhanNhanh, mà ô đó nay bị ` +
      'cắt bằng `…`. Không có title là giấu mất câu người dùng cần đọc');
  }
});
