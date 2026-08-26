/**
 * test_chan_mat_du_lieu.js — cửa cứng: app không được để mất thẻ chưa lưu.
 *
 * VÌ SAO CÓ TỆP NÀY, 26/08/2026:
 *
 * Sếp nói giao diện "cứ kiểu gì ấy" mà không diễn tả được. Đo thử thì ra hai
 * chỗ, và một trong hai là mất dữ liệu thật:
 *
 *   grep -rn beforeunload interface/web/the_v1/   ->  KHÔNG MỘT DÒNG NÀO
 *
 * Nghĩa là đóng tab trình duyệt — bấm ✕, hay Ctrl+W — thì mọi thẻ chưa lưu
 * bay sạch, im lặng, không một câu hỏi. Và Ctrl+W đặc biệt nguy: trong VS Code
 * nó đóng MỘT TỆP, còn ở đây app không bắt nên trình duyệt đóng cả cửa sổ.
 *
 * Đo bàn phím bằng cách gửi phím thật vào trang, đọc `defaultPrevented`:
 *
 *   app bắt            Ctrl+F · Ctrl+H · Ctrl+B · Ctrl+Z/Y · Ctrl+C/X/V · Ctrl+Enter
 *   RƠI XUỐNG TRÌNH DUYỆT  Ctrl+S · Ctrl+P · Ctrl+O · Ctrl+N · Ctrl+W
 *
 * Ctrl+S không phải "không làm gì" mà là LÀM SAI: trình duyệt mở hộp "Lưu
 * trang web". Đó là phản xạ số một của người dùng IDE.
 *
 * 707 test xanh suốt trong khi hai chỗ này trống. Cùng họ với tám lỗi
 * 24-25/08 (xem `test_moi_nut_co_handler.js`): test kiểm *hàm trả về đúng
 * chưa*, không test nào hỏi *bấm phím này thì có gì xảy ra không*.
 *
 * CỬA NÀY CHẠY THẬT LOGIC, không dò chuỗi. Nó bóc hàm `coThayDoiChuaLuu` ra
 * khỏi `app.js` rồi gọi với từng trạng thái. Dò chuỗi thì chỉ biết "có chữ
 * beforeunload", không biết nó có xét đúng các tab khác không — mà đó chính
 * là ca dễ sai nhất.
 */
const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf-8');

describe('chặn mất thẻ chưa lưu', () => {
  test('app có đăng ký beforeunload', () => {
    assert.ok(
      /addEventListener\(\s*['"]beforeunload['"]/.test(APP_JS),
      'Không thấy listener `beforeunload`. Đóng tab sẽ mất thẻ chưa lưu, ' +
      'im lặng — đúng lỗi đã sửa ngày 26/08/2026.');
  });

  test('beforeunload gọi CẢ preventDefault LẪN returnValue', () => {
    // Chrome theo `returnValue`, chuẩn HTML theo `preventDefault()`. Thiếu
    // một trong hai thì hộp cảnh báo không hiện trên một nhánh trình duyệt,
    // và không có gì nổ để ai biết.
    //
    // PHẢI BỎ CHÚ THÍCH TRƯỚC KHI SO. Bản đầu của cửa này dò thẳng chuỗi
    // `returnValue` trên cả khối, và khi thử gieo lỗi (xoá dòng
    // `e.returnValue = ''`) thì cửa VẪN XANH — vì chú thích ngay phía trên
    // có nhắc `returnValue` và `preventDefault()`. Cửa đang đọc lời bình
    // chứ không đọc mã.
    //
    // Đúng bệnh CLAUDE.md §4 "đừng tự chấm điểm bằng dò chuỗi con", xảy ra
    // trong chính cái cửa dựng ra để chống nó. Bắt được vì đã gieo lỗi thử,
    // không bắt được bằng đọc lại.
    const m = APP_JS.match(
      /addEventListener\(\s*['"]beforeunload['"][\s\S]{0,900}?\n\s*\}\);/);
    assert.ok(m, 'không tách được thân hàm beforeunload');
    const chiMa = m[0].replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');
    assert.ok(/preventDefault\s*\(\s*\)/.test(chiMa),
      'thiếu preventDefault() trong THÂN HÀM (không tính chú thích)');
    assert.ok(/\breturnValue\s*=/.test(chiMa),
      'thiếu phép gán returnValue trong THÂN HÀM (không tính chú thích)');
  });

  test('coThayDoiChuaLuu xét cả tab đang xem lẫn các tab KHÁC', () => {
    // Bóc đúng hàm ra và chạy nó. `state.hasModifications` là cờ của tab
    // ĐANG XEM; các tab kia giữ cờ riêng trong ảnh chụp của chúng (xem
    // `anhTabHienTai`). Chỉ xét tab đang xem thì: mở ba tệp, sửa hai tệp
    // đầu, đứng ở tệp thứ ba mà đóng — vẫn mất hai tệp kia, vẫn im lặng.
    const m = APP_JS.match(/function coThayDoiChuaLuu\(\)\s*\{[\s\S]*?\n    \}/);
    assert.ok(m, 'không tìm thấy hàm `coThayDoiChuaLuu` trong app.js');

    const dung = new Function('state', `${m[0]}; return coThayDoiChuaLuu();`);

    assert.equal(
      dung({ hasModifications: false, tabActive: 0, tabs: [{ hasModifications: false }] }),
      false, 'chưa sửa gì mà vẫn chặn — sẽ phiền người dùng mỗi lần đóng');

    assert.equal(
      dung({ hasModifications: true, tabActive: 0, tabs: [{ hasModifications: true }] }),
      true, 'tab đang xem có sửa mà không chặn');

    assert.equal(
      dung({
        hasModifications: false, tabActive: 0,
        tabs: [{ hasModifications: false }, { hasModifications: true }]
      }),
      true, 'tab KHÁC có sửa mà không chặn — đây là ca dễ sót nhất');

    assert.equal(
      dung({ hasModifications: false, tabActive: 0, tabs: [] }),
      false, 'chưa có tab nào mà vẫn chặn');
  });
});

describe('phím tắt theo thói quen IDE', () => {
  /** Thân khối `window.addEventListener('keydown', ...)` chính. */
  function khoiPhimTat() {
    const i = APP_JS.indexOf("window.addEventListener('keydown'");
    assert.ok(i !== -1, 'không tìm thấy khối phím tắt');
    return APP_JS.slice(i, i + 6000);
  }

  test('Ctrl+S được app bắt, không rơi xuống trình duyệt', () => {
    const k = khoiPhimTat();
    assert.ok(
      /e\.ctrlKey[^\n]*e\.key === 's'/.test(k),
      "Ctrl+S không được bắt. Ở trình duyệt nó mở hộp 'Lưu trang web' — " +
      'không phải không làm gì, mà là làm SAI.');
  });

  test('Ctrl+S lưu THẲNG khi tệp đã có đường dẫn', () => {
    // Trong IDE, Ctrl+S ghi đè tệp đang mở; hỏi đường dẫn là việc của
    // "Lưu thành tệp mới". Nút "Lưu Tệp" trên thanh trên vẫn mở hộp như cũ.
    const k = khoiPhimTat();
    const nhanh = k.match(/e\.key === 's'[\s\S]{0,1800}?\n      \} else if/);
    assert.ok(nhanh, 'không tách được nhánh Ctrl+S');
    assert.ok(
      /saveFile\(\s*state\.activeFilePath/.test(nhanh[0]),
      'Ctrl+S không gọi saveFile với đường dẫn đang mở');
    assert.ok(
      /state\.activeFilePath\s*\)/.test(nhanh[0]) && /else/.test(nhanh[0]),
      'thiếu nhánh cho tệp CHƯA có tên (phải mở hộp hỏi đường dẫn)');
  });
});
