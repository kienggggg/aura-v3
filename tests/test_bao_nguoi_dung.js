/**
 * test_bao_nguoi_dung.js — cửa cứng: app báo cho người dùng bằng cách không
 * chặn màn hình, và mở lên thì thấy việc của chính họ.
 *
 * VÌ SAO CÓ TỆP NÀY, 26/08/2026:
 *
 * Sếp bảo "sửa xong frontend tạo cảm giác thân thiện với người dùng". Đo thật
 * trên app đang chạy thì ra ba chỗ, tất cả đều là chuyện người dùng gặp trong
 * mười giây đầu:
 *
 *   1. `alert()` ở 6 chỗ, trong đó có `alert('Lưu tệp thành công!')` — hộp
 *      CHẶN CẢ TRANG bật lên MỖI LẦN LƯU. Bấm Ctrl+S theo phản xạ rồi phải
 *      bấm tiếp OK mới làm việc tiếp được. Lưu mười lần là mười lần bị chặn.
 *
 *   2. Mở app lên LUÔN thấy bài mẫu "1. Hàm cộng hai số" — mã của người
 *      khác, không nằm trong dự án của người dùng. Chua hơn: app ĐÃ CÓ SẴN
 *      màn hình chào cho canvas trống (`#emptyCanvasGuide`) nhưng mã khởi
 *      động nhét bài mẫu vào nên nó chưa từng hiện.
 *
 *   3. Lưu THÀNH CÔNG mà thanh trạng thái vẫn ghi "chưa lưu". Đường lưu
 *      không đi qua `onTreeChanged`, nơi tôi cắm `veThanhTrangThai()`. Cờ sai
 *      ấy còn kéo theo `beforeunload`: đóng tab bị hỏi vô cớ.
 *
 * Điều 3 đáng nhớ nhất: chú thích của CHÍNH TÔI ở `veThanhTrangThai` viết
 * "rải lời gọi khắp nơi thì sẽ có nhánh quên gọi" — rồi vấp đúng chuyện đó
 * trong cùng một buổi. Viết ra luật không bằng có cửa chặn.
 *
 * Cả ba chỉ lộ ra khi TỰ BẤM THỬ. Không cửa nào cũ bắt được.
 */
const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');

// CHUẨN HOÁ KẾT THÚC DÒNG trước khi so bất cứ thứ gì.
//
// Kho này nằm trên Windows và git đổi LF thành CRLF khi lấy tệp ra, nên
// `app.js` trên đĩa kết thúc dòng bằng CR + LF. Hai phép so của cửa này gãy
// vì đúng chuyện ấy, 26/08:
//
//   - Bộ bỏ chú thích dùng regex kết thúc bằng `$`. Trong JS, dấu chấm KHÔNG
//     khớp ký tự CR, nên phần `.*` dừng trước CR và không bao giờ chạm `$`.
//     Chú thích còn nguyên, và cửa báo "còn 1 lời gọi alert()" trong khi chỗ
//     đó chỉ là một dòng chú thích.
//   - Neo `indexOf` viết bằng LF không khớp chuỗi CRLF trên đĩa.
//
// Cả hai đều là CỬA SAI, không phải mã sai. Đúng họ bệnh "chấm điểm bằng dò
// chuỗi con" (CLAUDE.md §4), lần này do bảng mã xuống dòng.
const APP_JS = fs
  .readFileSync(path.join(THU_MUC, 'app.js'), 'utf-8')
  .split('\r\n')
  .join('\n');

/** app.js sau khi bỏ hết chú thích — để phép so không khớp nhầm lời bình.
 *
 * 26/08: bài học phải trả giá hai lần trong một buổi. Lần đầu, cửa kiểm
 * `returnValue` xanh dù đã gỡ dòng gán, vì chú thích ngay trên có chữ ấy.
 */
function maKhongChuThich() {
  return APP_JS
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .split('\n')
    .map(d => d.replace(/(^|[^:])\/\/.*$/, '$1'))
    .join('\n');
}

describe('không chặn màn hình để báo tin', () => {
  test('không còn lời gọi alert() nào trong mã', () => {
    const ma = maKhongChuThich();
    const con = [...ma.matchAll(/(^|[^.\w])alert\s*\(/g)];
    assert.equal(con.length, 0,
      `còn ${con.length} lời gọi alert(). Hộp alert chặn cả trang, trông ` +
      'giống cảnh báo của trình duyệt hơn của app, và mất sạch khi bấm OK — ' +
      'người dùng không đọc kịp thì không xem lại được. Dùng `baoNhanh()`.');
  });

  test('baoNhanh phân biệt được việc và hỏng việc', () => {
    const ma = maKhongChuThich();
    assert.ok(/function baoNhanh\(chu, loai = ''\)/.test(ma),
      'thiếu hàm baoNhanh(chu, loai)');
    assert.ok(/loai === 'hong'/.test(ma),
      'baoNhanh không phân biệt loại — báo lỗi sẽ trôi qua như báo thành công');
    // Báo lỗi phải ở lại LÂU HƠN báo thường: người ta cần đọc kỹ hơn.
    const m = ma.match(/loai === 'hong' \? (\d+) : (\d+)/);
    assert.ok(m, 'không tìm thấy hai mốc thời gian trong baoNhanh');
    assert.ok(Number(m[1]) > Number(m[2]),
      `báo hỏng (${m[1]}ms) phải ở lại lâu hơn báo thường (${m[2]}ms)`);
  });
});

describe('lưu xong thì mọi chỗ đều biết', () => {
  test('nhánh lưu thành công vẽ lại thanh trạng thái', () => {
    // Đường lưu KHÔNG đi qua `onTreeChanged`. Thiếu lời gọi này thì lưu
    // thành công mà thanh vẫn ghi "chưa lưu", và `beforeunload` hỏi vô cớ.
    const i = APP_JS.indexOf(
      'state.hasModifications = false;\n        dongBoTabHienTai();');
    assert.ok(i !== -1, 'không tìm thấy nhánh lưu thành công');
    const nhanh = APP_JS.slice(i, i + 2200);
    assert.ok(nhanh.includes('veThanhTrangThai()'),
      'nhánh lưu thành công không gọi veThanhTrangThai() — thanh trạng thái ' +
      'sẽ giữ nguyên "chưa lưu" sau khi đã lưu xong');
  });

  test('câu báo chỉ hiện TÊN tệp, không hiện đường dẫn đầy đủ', () => {
    // Đường dẫn tuyệt đối dài hơn 100 ký tự, tràn hết ô báo và không nói
    // thêm được gì — người dùng đã biết mình ở dự án nào (thanh trạng thái
    // ghi bên trái).
    const ma = maKhongChuThich();
    const m = ma.match(/baoNhanh\(`✓ Đã lưu \$\{([^}]*)\}`\)/);
    assert.ok(m, 'không tìm thấy câu báo lưu thành công');
    assert.ok(/\.pop\(\)/.test(m[1]),
      `câu báo lưu dùng "${m[1]}" — vẫn là cả đường dẫn, phải cắt lấy tên tệp`);
  });
});

describe('mở lên thấy việc của mình', () => {
  test('có nhớ tệp đang mở, khoá theo từng dự án', () => {
    const ma = maKhongChuThich();
    assert.ok(/function khoaNhoTep\(\)/.test(ma), 'thiếu hàm khoaNhoTep');
    assert.ok(/'aura_tep_dang_mo:' \+ \(state\.tenDuAn/.test(ma),
      'khoá nhớ tệp không gắn với tên dự án — mở dự án B sẽ đòi tệp của dự ' +
      'án A và nhận lỗi');
    assert.ok(/async function moLaiTepLanTruoc\(\)/.test(ma),
      'thiếu hàm moLaiTepLanTruoc');
  });

  test('nhớ lại cả khi mở tệp lẫn khi lưu tệp', () => {
    const ma = maKhongChuThich();
    assert.ok(/nhoTepDangMo\(data\.duong_dan\)/.test(ma),
      'mở tệp xong không nhớ lại');
    assert.ok(/nhoTepDangMo\(target\)/.test(ma),
      'lưu tệp xong không nhớ lại — "lưu thành tệp mới" xong mở lại vẫn ra ' +
      'tệp cũ');
  });

  test('khởi động CHỜ /api/status trước khi đọc khoá nhớ', () => {
    // `state.tenDuAn` về từ `/api/status`, và nó là KHOÁ. Không chờ thì
    // `moLaiTepLanTruoc()` đọc khoá '(khong ro)' — sai dự án, và lỗi chỉ hiện
    // ra ở lần chạy THỨ HAI. Đây là lần thứ hai trong buổi vấp đúng kiểu đua
    // thứ tự này (lần trước: cây tệp vẽ xong trước khi tên dự án về).
    assert.ok(/await configureRuntimeCapabilities\(\)/.test(APP_JS),
      'khởi động không chờ configureRuntimeCapabilities() — khoá nhớ tệp sẽ sai');
  });

  test('mở lại tệp cũ SAU khi tab đầu đã dựng', () => {
    // `moTrongTab` gọi `dongBoTabHienTai()` để chụp tab hiện tại trước khi mở
    // tab mới. Chưa có tab nào thì không có chỗ chụp, và bài mẫu bị nuốt mất.
    const iTab = APP_JS.indexOf('state.tabs = [{');
    assert.ok(iTab !== -1, 'không tìm thấy chỗ dựng tab đầu');
    const iGoi = APP_JS.indexOf('moLaiTepLanTruoc();', iTab);
    assert.ok(iGoi !== -1 && iGoi > iTab,
      'moLaiTepLanTruoc() phải được gọi SAU khi state.tabs đã có tab đầu');
  });
});
