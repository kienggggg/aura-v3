// tests/test_luoi_khong_bi_transition_dong_bang.js
//
// 30/08/2026. HAI NÚT MỞ/ĐÓNG PANEL CHƯA TỪNG HOẠT ĐỘNG. Bấm thử tay:
//
//   bấm btnToggleSidebarLeft
//     lớp    app-main            -> app-main left-collapsed       ĐÚNG
//     biến   --sidebar-left-width  240px -> 0px                   ĐÚNG
//     LƯỚI   240px 786.4px 340px -> 240px 786.4px 340px           KHÔNG ĐỔI
//     panel  240px               -> 240px                         KHÔNG ĐỔI
//
// Chờ 900ms (transition chỉ khai 200ms) vẫn y nguyên. Tách biến bằng cách tắt
// transition ngay tại chỗ trong trang: lưới LẬP TỨC nhảy đúng `0px 1366.4px 0px`.
// Tức `grid-template-columns` lấy giá trị từ `var()` mà bị đặt transition thì KẸT
// lại ở giá trị cũ, không bao giờ tới đích.
//
// Vì sao 72 khẳng định JS khác không bắt được: `test_moi_nut_co_handler.js` hỏi
// "nút này có ai nghe không" — có. Không cửa nào hỏi "bấm rồi có gì đổi không".
// Đúng hai câu hỏi khác nhau đã ghi ở CLAUDE.md mục 4, và câu thứ hai mới là câu
// người dùng hỏi.
//
// Cửa này giữ luật CHUNG chứ không vá riêng một dòng: không luật CSS nào được
// transition một thuộc tính bố cục lấy giá trị từ `var()`. Đó là cái bẫy, không
// phải cái dòng cụ thể.
//
// GIỚI HẠN, nói luôn: đây là kiểm trên MÃ CSS, không phải bấm thử. Nó chặn việc
// cài lại cái bẫy; nó KHÔNG chứng minh hai nút chạy. Phần ấy vẫn phải bấm tay,
// và đã bấm: đóng trái -> 0px 1026px 340px · đóng cả hai -> 0px 1366px 0px ·
// mở lại -> 240px 786px 340px.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const CSS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'style.css'), 'utf8');

// Thuộc tính bố cục mà giá trị hay đến từ var(), và transition thì kẹt.
const THUOC_TINH_BO_CUC = [
  'grid-template-columns',
  'grid-template-rows',
  'grid-template-areas',
];

/** Tách các khối luật `sel { ... }`, bỏ chú thích trước khi tách. */
function cacKhoiLuat(css) {
  const sach = css.replace(/\/\*[\s\S]*?\*\//g, ' ');
  const ra = [];
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m;
  while ((m = re.exec(sach)) !== null) {
    ra.push({ sel: m[1].trim().replace(/\s+/g, ' '), than: m[2] });
  }
  return ra;
}

test('không luật nào transition một thuộc tính bố cục lấy từ var()', () => {
  const pham = [];
  for (const { sel, than } of cacKhoiLuat(CSS)) {
    const tr = /(?:^|[;\s])transition(?:-property)?\s*:([^;]*)/i.exec(than);
    if (!tr) continue;
    const dsChuyen = tr[1];
    for (const tt of THUOC_TINH_BO_CUC) {
      if (!dsChuyen.includes(tt) && !/\ball\b/.test(dsChuyen)) continue;
      // chỉ là bẫy khi CHÍNH luật này đặt thuộc tính đó bằng var()
      const dat = new RegExp(tt + '\\s*:([^;]*)', 'i').exec(than);
      if (dat && /var\(/.test(dat[1])) {
        pham.push(`${sel} { transition:${dsChuyen.trim().slice(0, 40)} ; ${tt}: ${dat[1].trim().slice(0, 46)} }`);
      }
    }
  }
  assert.deepStrictEqual(pham, [],
    'transition một thuộc tính bố cục lấy giá trị từ var() làm nó KẸT ở giá trị ' +
    'cũ — nút đổi bố cục sẽ im lặng không làm gì');
});

test('lưới của .app-main vẫn dùng biến cho hai cột bên', () => {
  const luat = cacKhoiLuat(CSS).find(x => x.sel === '.app-main');
  assert.ok(luat, 'không còn luật .app-main');
  const gtc = /grid-template-columns\s*:([^;]*)/i.exec(luat.than);
  assert.ok(gtc, '.app-main không còn grid-template-columns');
  assert.match(gtc[1], /var\(--sidebar-left-width\)/);
  assert.match(gtc[1], /var\(--sidebar-right-width\)/);
});

test('hai lớp thu gọn vẫn đặt biến về 0', () => {
  for (const [sel, bien] of [
    ['.app-main.left-collapsed', '--sidebar-left-width'],
    ['.app-main.right-collapsed', '--sidebar-right-width'],
  ]) {
    const luat = cacKhoiLuat(CSS).find(x => x.sel === sel);
    assert.ok(luat, `không còn luật ${sel} — nút thu gọn sẽ không có tác dụng`);
    const m = new RegExp(bien + '\\s*:\\s*0(px)?', 'i').exec(luat.than);
    assert.ok(m, `${sel} không còn đặt ${bien} về 0`);
  }
});

// Chiều ngược lại: đừng "sửa" bằng cách bỏ hết transition trong tệp. Hiệu ứng mờ
// của panel là thứ khác và phải giữ.
test('panel vẫn giữ hiệu ứng mờ — không bỏ transition bừa', () => {
  for (const sel of ['.sidebar-left', '.sidebar-right']) {
    const luat = cacKhoiLuat(CSS).find(x => x.sel === sel);
    assert.ok(luat, `không còn luật ${sel}`);
    assert.match(luat.than, /transition\s*:[^;]*opacity/i,
      `${sel} mất transition opacity — bỏ transition quá tay`);
  }
});
