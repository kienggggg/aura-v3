// tests/test_soi_chuong_trinh_khong_gia_vo.js
//
// Bảng bên phải KHÔNG được giả vờ suy nghĩ, và không được đoán bừa ý câu hỏi.
//
// VÌ SAO CÓ TỆP NÀY. 01/09/2026, soi mã panel "Trợ Lý AURA":
//
//     xuLyTinNhanNguoiDung()
//       -> hienThiDangSuyNghi()        ba chấm nhấp nháy
//       -> setTimeout(..., 280)        CHỜ 280ms mà không chờ gì cả
//       -> q.includes('lỗi') || ...    dò chuỗi con
//       -> bốn hàm sinh HTML           0 request ra ngoài
//
// Nó KHÔNG bịa: `phanTichLoiThe()` đọc `state.diagnostics` thật, đếm lỗi thật.
// Đây là một trợ lý THEO LUẬT, nói đúng về chương trình đang mở. Nhưng cái tên
// "Trợ Lý AURA" cộng với 280ms giả vờ nghĩ khiến người dùng đọc thành một
// model — đúng họ "nhãn nói sai việc" ở CLAUDE.md mục 4.
//
// ĐO BỘ ĐỊNH TUYẾN, hai bộ câu, trước và sau:
//
//     12 câu thường          11/12  ->  12/12
//     10 câu khó              4/10  ->   9/10
//
// Bốn kiểu hỏng, chỉ MỘT là bệnh dò chuỗi con:
//     `fix` nằm trong `prefix`/`suffix`      -> chữa bằng ranh giới từ
//     từ đơn quá chung (`đỏ`, `thêm`)        -> chữa bằng cụm
//     câu chạm hai chủ đề, nhánh đầu thắng   -> chữa bằng HỎI LẠI
//     ngữ nghĩa thật (`đỏ` màu hay lỗi)      -> KHÔNG chữa được, không giả vờ
//
// Cửa CHẠY THẬT `docYDinhCauHoi` trích ra khỏi app.js, theo lối `test_o_tim.js`.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { bocMoiChuThich, bocChuThich } = require('../tools/boc_chu_thich.js');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const doc = (ten) => fs.readFileSync(path.join(THU_MUC, ten), 'utf8');
const APP_JS_THO = doc('app.js');
const APP_JS = bocMoiChuThich(APP_JS_THO);
const HTML = bocChuThich(doc('index.html'));

function trichKhoi(neo, nguon = APP_JS_THO) {
  const i = nguon.indexOf(neo);
  assert.notStrictEqual(i, -1, 'không tìm thấy: ' + neo);
  let j = nguon.indexOf('{', i) + 1;
  let sau = 1;
  while (sau > 0) {
    assert.ok(j < nguon.length, 'ngoặc không đóng sau: ' + neo);
    const ch = nguon[j];
    if (ch === '{') sau += 1;
    else if (ch === '}') sau -= 1;
    j += 1;
  }
  return nguon.slice(i, j);
}

// `KY_TU_TRONG_TU` KHÔNG trích bằng `trichKhoi` được: giá trị của nó là
// '\\p{L}\\p{N}\\p{M}_' và bộ đếm ngoặc bám ngay vào dấu `{` NẰM TRONG CHUỖI
// rồi đếm lệch. Lấy nguyên dòng bằng khớp chuỗi nháy đơn thay vì đếm ngoặc.
const dongKyTu = APP_JS_THO.match(/const KY_TU_TRONG_TU = '[^']*';/);
assert.ok(dongKyTu, 'không tìm thấy khai báo KY_TU_TRONG_TU');

const nguon = [
  dongKyTu[0],
  trichKhoi('const BANG_TU_KHOA_SOI = {'),
  trichKhoi('function khopTronVen(cau, cum) {'),
  trichKhoi('function docYDinhCauHoi(cau) {'),
  'return { docYDinhCauHoi, khopTronVen, BANG_TU_KHOA_SOI };',
].join(';\n');
const app = new Function(nguon)();

/** Rút gọn kết quả về một nhãn để so cho gọn. */
function nhan(cau) {
  const y = app.docYDinhCauHoi(cau);
  if (y.viec) return y.viec.toUpperCase();
  return y.ly_do === 'mo_ho' ? 'HOI_LAI' : 'KHONG_HIEU';
}

test('bàn thử tự nó phải chạy', () => {
  // Ca đối chứng cho chính máy đo: bảng phải có đủ bốn việc, và một câu rỗng
  // phải rơi vào "không khớp" chứ không nổ.
  assert.deepStrictEqual(Object.keys(app.BANG_TU_KHOA_SOI).sort(),
    ['goi_y', 'kich_ban', 'loi', 'trace']);
  assert.strictEqual(nhan(''), 'KHONG_HIEU');
});

test('12 câu người học hỏi bình thường', () => {
  const BO = [
    ['Chương trình này làm gì?', 'KICH_BAN'],
    ['Giải thích luồng chạy giúp em', 'KICH_BAN'],
    ['Thẻ nào đang bị đỏ?', 'LOI'],
    ['Em nên thêm thẻ gì tiếp theo?', 'GOI_Y'],
    ['Mạch nước ngầm là gì?', 'TRACE'],
    ['Cái thẻ này để làm gì vậy?', 'KICH_BAN'],
    ['Làm sao lưu tệp?', 'KHONG_HIEU'],
    ['Python có bao nhiêu kiểu dữ liệu?', 'KHONG_HIEU'],
    ['Vì sao thẻ của em không chạy?', 'LOI'],
    ['Hôm nay trời đẹp nhỉ', 'KHONG_HIEU'],
    ['Kể chuyện cười đi', 'KHONG_HIEU'],
    ['Xin chào', 'KHONG_HIEU'],
  ];
  const truot = BO.filter(([c, m]) => nhan(c) !== m).map(([c, m]) => `${c} -> ${nhan(c)} (mong ${m})`);
  assert.deepStrictEqual(truot, [], `bản dò chuỗi con được 11/12; nay phải 12/12`);
});

test('từ khoá nằm LỌT GIỮA từ khác thì không được khớp', () => {
  // Đúng bệnh CLAUDE.md mục 4. Bản trước: `fix` trong `prefix` -> báo hỏi LỖI.
  for (const cau of ['Biến prefix dùng thế nào?', 'Hàm suffix_ten em viết đúng chưa?']) {
    assert.strictEqual(nhan(cau), 'KHONG_HIEU', `"${cau}" khớp nhầm`);
  }
  assert.ok(!app.khopTronVen('biến prefix', 'fix'), 'fix khớp lọt trong prefix');
  assert.ok(app.khopTronVen('cái trace này', 'trace'), 'trace đứng riêng phải khớp');
});

test('từ đơn quá chung phải đổi thành CỤM', () => {
  // Ranh giới từ KHÔNG chữa được nhóm này — `đỏ` đứng riêng thật. Chữa bằng
  // cách bảng chỉ chứa `bị đỏ` · `thẻ đỏ` · `báo đỏ`, không chứa `đỏ` trơ.
  assert.ok(!app.BANG_TU_KHOA_SOI.loi.includes('đỏ'),
    '`đỏ` trơ trong bảng thì "đổi màu nền thành đỏ" bị báo là hỏi lỗi');
  assert.ok(!app.BANG_TU_KHOA_SOI.goi_y.includes('thêm'),
    '`thêm` trơ thì "tệp này có thêm gì mới không" bị báo là xin gợi ý thẻ');
  for (const cau of ['In ra chữ "Đỏ" thì viết sao?', 'Em muốn đổi màu nền thành đỏ',
                     'Tệp này có thêm gì mới không?', 'Cho em xin số đo chiều dài']) {
    assert.strictEqual(nhan(cau), 'KHONG_HIEU', `"${cau}" khớp nhầm`);
  }
});

test('câu chạm HAI chủ đề thì HỎI LẠI, không tự chọn', () => {
  const y = app.docYDinhCauHoi('Gợi ý thẻ nào để sửa lỗi này?');
  assert.strictEqual(y.viec, null,
    'bản trước để nhánh `if` đầu thắng: trả về một bản kê lỗi, phần "gợi ý" ' +
    'bốc hơi mà người dùng không biết');
  assert.strictEqual(y.ly_do, 'mo_ho');
  assert.deepStrictEqual(y.ung_vien.sort(), ['goi_y', 'loi']);
});

test('KHÔNG khớp gì thì nói KHÔNG HIỂU, không đoán bừa', () => {
  const y = app.docYDinhCauHoi('Hôm nay trời đẹp nhỉ');
  assert.strictEqual(y.viec, null);
  assert.strictEqual(y.ly_do, 'khong_khop');
});

test('ba trạng thái tách rời, không gộp thành hai', () => {
  // CLAUDE.md: đạt · đo được mà không đạt · KHÔNG ĐO ĐƯỢC. Ở đây là:
  // chắc chắn một việc · mơ hồ giữa nhiều việc · không hiểu. Gộp "mơ hồ" vào
  // "không hiểu" thì mất lời mời chọn; gộp vào "chắc" thì quay lại đoán bừa.
  const ba = new Set([
    app.docYDinhCauHoi('Thẻ nào đang bị đỏ?').viec ? 'chac' : 'khac',
    app.docYDinhCauHoi('Gợi ý thẻ nào để sửa lỗi này?').ly_do,
    app.docYDinhCauHoi('Xin chào').ly_do,
  ]);
  assert.deepStrictEqual([...ba].sort(), ['chac', 'khong_khop', 'mo_ho']);
});

test('KHÔNG còn giả vờ suy nghĩ ở bất kỳ đâu', () => {
  assert.ok(!/hienThiDangSuyNghi|xoaDangSuyNghi/.test(APP_JS),
    'hai hàm ba-chấm-nhấp-nháy vẫn còn — chúng chỉ để trông như đang nghĩ');
  const than = trichKhoi('function xuLyTinNhanNguoiDung(noiDung) {', APP_JS);
  assert.ok(!/setTimeout/.test(than),
    'còn `setTimeout` trong đường trả lời: bảng này không chờ gì cả, nó đọc ' +
    'state.tree rồi trả lời trong vài mili-giây');
  const nutNhanh = APP_JS.slice(APP_JS.indexOf('analyze-errors'),
                                APP_JS.indexOf('analyze-errors') + 1400);
  assert.ok(!/setTimeout/.test(nutNhanh),
    'bốn nút gợi ý nhanh vẫn còn `setTimeout(..., 200)` giả vờ nghĩ');
});

test('nhãn trên màn hình nói ĐÚNG việc bảng này làm', () => {
  assert.ok(!/Trợ Lý AURA|Trợ lý AURA/i.test(HTML),
    'tên "Trợ Lý AURA" đọc như một model biết trò chuyện, trong khi nó là bộ ' +
    'dò từ khoá đọc cây thẻ');
  assert.ok(/Soi Chương Trình/.test(HTML), 'thiếu tên mới');
  assert.ok(/không dùng model/i.test(HTML),
    'phải nói THẲNG trên màn hình là không có model — người dùng đọc nhãn, ' +
    'không đọc mã nguồn');
});
