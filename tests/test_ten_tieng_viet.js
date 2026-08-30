// tests/test_ten_tieng_viet.js
//
// 30/08/2026. Trục "nội dung tiếng Việt trong mã người dùng" chưa ai đi qua.
// Nó lộ ra khi bấm tay bài 4 của Phòng Thử Thách, rồi kéo theo hai lỗi:
//
//   1) /api/chay không ép UTF-8 cho tiến trình con -> print("Chuột") nổ
//      UnicodeEncodeError. Cửa cho lỗi đó nằm ở tests/test_the_v1.py.
//   2) Bộ kiểm tra tĩnh coi tên biến tiếng Việt là CHƯA TỪNG ĐƯỢC GÁN. Đo:
//         ten_bien "loi_chao"  -> hợp lệ, 0 lỗi
//         ten_bien "lời_chào"  -> 1 lỗi ĐỎ "chưa từng được gán"
//      Lỗi đỏ CHẶN CỨNG nút CHẠY (runProgram trong app.js), nên người học đặt
//      tên biến bằng tiếng Việt vừa bị vu oan vừa không chạy nổi chương trình.
//      Nguyên nhân: 23 chỗ dùng mẫu `[a-zA-Z_][a-zA-Z0-9_]*` — 9 ở core/the_v1.py,
//      12 ở validator.js, 2 ở app.js. Python 3 cho phép định danh Unicode.
//
// Cửa này CHẠY THẬT bộ kiểm phía trình duyệt, không dò mẫu regex trong mã: đổi
// mẫu về chỉ-ASCII thì nó phải đỏ vì HÀNH VI. Và nó giữ luôn chiều ngược lại —
// biến thật sự chưa gán vẫn phải bị bắt, để bản vá không biến thành "tắt luật".
//
// GIỚI HẠN: chỉ kiểm bộ phía trình duyệt. Bộ phía Python có cửa song song ở
// tests/test_the_v1.py; hai bên còn được test_the_parity.js canh cho khớp nhau.

const assert = require('node:assert');
const { test } = require('node:test');
const path = require('node:path');

const V = require(path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'validator.js'));

function cayGanRoiDung(ten) {
  return [
    { id: 'n1', ma: 'gan', o: { ten_bien: ten, gia_tri: '"Chào Sếp"' }, than: [] },
    { id: 'n2', ma: 'in_ra', o: { noi_dung: ten }, than: [] },
  ];
}

const TEN_TIENG_VIET = ['lời_chào', 'tổng', 'số', 'biến_đếm', '_riêng', 'dữ_liệu'];

test('tên biến tiếng Việt KHÔNG được bị coi là chưa từng gán', () => {
  for (const ten of TEN_TIENG_VIET) {
    const r = V.kiemTraCayThe(cayGanRoiDung(ten));
    assert.strictEqual(r.so_loi_do, 0,
      `tên biến "${ten}" bị báo ${r.so_loi_do} lỗi đỏ: ` +
      JSON.stringify((r.danh_sach || []).map((d) => d.thong_diep)));
  }
});

test('cùng cây thẻ, tên ASCII và tên tiếng Việt phải cho cùng kết quả', () => {
  const ascii = V.kiemTraCayThe(cayGanRoiDung('loi_chao'));
  for (const ten of TEN_TIENG_VIET) {
    const viet = V.kiemTraCayThe(cayGanRoiDung(ten));
    assert.strictEqual(viet.so_loi_do, ascii.so_loi_do,
      `"${ten}" cho ${viet.so_loi_do} lỗi trong khi "loi_chao" cho ${ascii.so_loi_do}`);
  }
});

test('biến vòng lặp for bằng tiếng Việt phải được tính là đã gán', () => {
  const r = V.kiemTraCayThe([
    { id: 'a', ma: 'gan', o: { ten_bien: 'dãy_số', gia_tri: '[1, 2, 3]' }, than: [] },
    { id: 'b', ma: 'lap_moi', o: { bien: 'phần_tử', day: 'dãy_số' }, than: [
      { id: 'c', ma: 'in_ra', o: { noi_dung: 'phần_tử' }, than: [] },
    ] },
  ]);
  assert.strictEqual(r.so_loi_do, 0,
    JSON.stringify((r.danh_sach || []).map((d) => d.thong_diep)));
});

test('hàm và tham số bằng tiếng Việt phải được tính là đã gán', () => {
  const r = V.kiemTraCayThe([
    { id: 'h', ma: 'ham', o: { ten_ham: 'cộng', tham_so: 'số_một, số_hai' }, than: [
      { id: 'r', ma: 'tra_ve', o: { gia_tri: 'số_một + số_hai' }, than: [] },
    ] },
    { id: 'p', ma: 'in_ra', o: { noi_dung: 'cộng(2, 3)' }, than: [] },
  ]);
  assert.strictEqual(r.so_loi_do, 0,
    JSON.stringify((r.danh_sach || []).map((d) => d.thong_diep)));
});

// Chiều ngược lại. Không có khẳng định này thì cách "sửa" dễ nhất là tắt luật
// undefined_variable đi, và mọi khẳng định trên vẫn xanh.
test('biến tiếng Việt THẬT SỰ chưa gán thì vẫn phải bị bắt', () => {
  const r = V.kiemTraCayThe([
    { id: 'n2', ma: 'in_ra', o: { noi_dung: 'chưa_gán_bao_giờ' }, than: [] },
  ]);
  assert.strictEqual(r.so_loi_do, 1,
    'bản vá đã nới thành tắt luật: biến chưa gán không còn bị bắt');
  assert.ok(
    (r.danh_sach || []).some((d) => d.ma_loi === 'undefined_variable'),
    'lỗi bắt được không phải undefined_variable: ' + JSON.stringify(r.danh_sach));
});

test('biến ASCII thật sự chưa gán cũng vẫn phải bị bắt', () => {
  const r = V.kiemTraCayThe([
    { id: 'n2', ma: 'in_ra', o: { noi_dung: 'chua_gan_bao_gio' }, than: [] },
  ]);
  assert.strictEqual(r.so_loi_do, 1, JSON.stringify(r.danh_sach));
});
