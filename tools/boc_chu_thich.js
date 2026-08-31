// tools/boc_chu_thich.js
//
// Bóc chú thích khỏi mã nguồn TRƯỚC khi dò chuỗi trên nó.
//
// VÌ SAO CÓ TỆP NÀY. Ngày 30/08/2026, cùng một bệnh cắn ba lần trong một ngày:
// một cửa khẳng định `than.includes('LỖI RUNTIME')` và nó XANH — không phải vì
// mã còn dòng ấy, mà vì CHÚ THÍCH của chính tôi ở đầu `app.js` có chữ đó.
//
// Đo có hệ thống sau đó, gieo cùng một phép vào sáu cửa (xoá dòng mã thật, để
// lại một chú thích mang đúng chữ mà cửa tìm):
//
//     test_bo_cham_khong_tu_bia.js       VẪN XANH   <- bị lừa
//     test_nut_tai_svg.js                VẪN XANH   <- bị lừa
//     test_phim_tat_phai_duoc_nghe.js    VẪN XANH   <- bị lừa
//     test_nhan_noi_dung_viec.js         VẪN XANH   <- bị lừa
//     test_moi_nut_co_handler.js         VẪN XANH   <- bị lừa
//     test_o_tim.js                      ĐỎ         <- KHÔNG bị lừa
//
// Năm trên sáu. Và cái duy nhất thoát là cái duy nhất CHẠY mã trích ra thay vì
// dò chuỗi trên nó. Đó là bài học thật: cửa chạy thật thì miễn nhiễm; cửa dò
// chuỗi thì phải bóc chú thích, không có lựa chọn thứ ba.
//
// Đường tấn công không cần ai cố ý: chỉ cần một người comment tạm một dòng để
// thử gì đó rồi quên bỏ comment. Năm cửa vẫn xanh.
//
// HƯỚNG SAI AN TOÀN: chỉ bóc chú thích CẢ DÒNG (`//` là thứ đầu tiên sau khoảng
// trắng đầu dòng) và khối `/* */`. Chú thích cuối dòng KHÔNG bóc — bóc nó cần
// hiểu chuỗi và regex literal, mà bóc nhầm một đoạn mã thật thì gây XANH GIẢ,
// đúng thứ tệp này sinh ra để chống. Bỏ sót một chú thích cuối dòng thì cùng lắm
// gây ĐỎ GIẢ, và đỏ giả thì có người đọc.

'use strict';

/** Bóc chú thích cả dòng và khối. Xem chú thích ở đầu tệp về hướng sai an toàn. */
function bocChuThich(s) {
  const khong_khoi = String(s == null ? '' : s).replace(/\/\*[\s\S]*?\*\//g, ' ');
  return khong_khoi
    .split('\n')
    .map((d) => (/^\s*\/\//.test(d) ? '' : d))
    .join('\n');
}

/** Bóc thêm nội dung chuỗi — cho cửa nào cần chắc rằng chuỗi cũng không lừa được. */
function bocChuThichVaChuoi(s) {
  let r = bocChuThich(s);
  r = r.replace(/'(?:[^'\\\n]|\\.)*'/g, "''");
  r = r.replace(/"(?:[^"\\\n]|\\.)*"/g, '""');
  r = r.replace(/`(?:[^`\\]|\\.)*`/g, '``');
  return r;
}

/**
 * Bóc CẢ chú thích cuối dòng, bằng cách quét từng ký tự và nhớ mình đang ở
 * trong chuỗi nào.
 *
 * VÌ SAO CẦN THÊM HÀM NÀY. `bocChuThich` cố ý chỉ bóc chú thích cả dòng, vì
 * hướng sai của nó an toàn. Nhưng gieo thử 30/08/2026 cho thấy có chỗ hướng ấy
 * không đủ: gỡ `|| e.key === 'F11'` khỏi mã và để lại chú thích CUỐI DÒNG
 * `// trước đây: e.key === 'F11'` thì `test_phim_tat_phai_duoc_nghe.js` VẪN
 * XANH. Hai cửa kia hết mù sau khi bọc, cửa này thì không.
 *
 * Hàm này quét trạng thái chuỗi ('...', "...", `...`) nên không cắt nhầm một
 * `//` nằm trong chuỗi — ví dụ `'http://x'` giữ nguyên.
 *
 * GIỚI HẠN ĐÃ BIẾT: nó KHÔNG hiểu regex literal. Một `//` bên trong regex kiểu
 * `/\/\//` sẽ bị coi là mở chú thích và phần còn lại của dòng bị cắt. Hiếm,
 * và hướng sai của nó là ĐỎ GIẢ (cắt mất mã thật -> khẳng định dương trượt),
 * chứ không phải xanh giả. Đỏ giả thì có người đọc.
 */
function bocMoiChuThich(s) {
  const chu = String(s == null ? '' : s);
  let ra = '';
  let i = 0;
  let trongChuoi = null;      // ký tự mở chuỗi đang dở, hoặc null
  let trongKhoi = false;      // đang trong /* */

  while (i < chu.length) {
    const c = chu[i];
    const ke = chu[i + 1];

    if (trongKhoi) {
      if (c === '*' && ke === '/') { trongKhoi = false; i += 2; ra += ' '; continue; }
      ra += (c === '\n' ? '\n' : ' ');
      i += 1;
      continue;
    }

    if (trongChuoi) {
      ra += c;
      if (c === '\\') { ra += (ke === undefined ? '' : ke); i += 2; continue; }
      if (c === trongChuoi) trongChuoi = null;
      i += 1;
      continue;
    }

    if (c === "'" || c === '"' || c === '`') { trongChuoi = c; ra += c; i += 1; continue; }
    if (c === '/' && ke === '/') {
      while (i < chu.length && chu[i] !== '\n') i += 1;   // bỏ tới hết dòng
      continue;
    }
    if (c === '/' && ke === '*') { trongKhoi = true; i += 2; ra += ' '; continue; }

    ra += c;
    i += 1;
  }
  return ra;
}

module.exports = { bocChuThich, bocChuThichVaChuoi, bocMoiChuThich };
