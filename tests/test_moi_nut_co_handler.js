/**
 * test_moi_nut_co_handler.js — cửa cứng: MỌI nút trên giao diện phải có
 * người nghe sự kiện thật.
 *
 * VÌ SAO CÓ TỆP NÀY, 24-25/08/2026:
 *
 * Tám lỗi trong hai ngày, tất cả cùng MỘT HỌ — giao diện hứa một việc, mã
 * làm việc khác (hoặc không làm gì):
 *
 *   btnUndo / btnRedo          có nút, có state.history, KHÔNG handler nào
 *   btnZoomIn/Out/Reset        có nút, có hàm setCodeFontSize, có cả phím
 *                              tắt — nhưng ba nút chưa từng nối
 *   btnToggleSidebarRight      nhãn ghi "Bảng Phụ & Terminal", đo thật thì
 *                              terminal KHÔNG đổi (flex -> flex)
 *   panel Agent                trả lời bằng chuỗi cứng + setTimeout 350ms
 *                              giả vờ suy nghĩ, 0 request
 *   hộp "Mở tệp"               đọc data.tep_tin, backend trả danh_sach
 *   nút "Dò dòng dữ liệu"      .replace('core/', ...) trên đường dẫn dùng
 *                              dấu `\` — không khớp, chưa từng chạy được
 *
 * KHÔNG lỗi nào trong tám lỗi ấy bị 624 test bắt. Chúng xanh suốt trong khi
 * cả tám đang tồn tại. Cả tám chỉ lộ ra khi TỰ BẤM THỬ như người dùng.
 *
 * Cửa này chặn được đúng MỘT loại trong họ đó — loại rẻ nhất và máy kiểm
 * được: "có nút mà không ai nghe". Ba loại còn lại (nhãn nói sai việc, dữ
 * liệu đọc sai tên trường, trả lời giả) thì máy không tự biết được; chúng
 * vẫn phải bắt bằng tay. Nói rõ ra để không ai tưởng cửa này che hết.
 */
const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

// 30/08/2026 — bọc qua bocChuThich(). Gieo thử chứng minh cửa này TỪNG bị
// lừa: xoá dòng mã thật và để lại một chú thích mang đúng chữ cửa tìm thì nó
// VẪN XANH. 5/6 cửa dò chuỗi dính bệnh này; cái duy nhất thoát là cái CHẠY mã.
// Xem tools/boc_chu_thich.js.
const { bocChuThich } = require('../tools/boc_chu_thich.js');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const HTML = bocChuThich(fs.readFileSync(path.join(THU_MUC, 'index.html'), 'utf-8'));
const APP_JS = bocChuThich(fs.readFileSync(path.join(THU_MUC, 'app.js'), 'utf-8'));

/** Mọi thẻ <button> trong HTML, kèm id và danh sách class. */
function docCacNut(html) {
  const ra = [];
  const re = /<button\b([^>]*)>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const thuoc_tinh = m[1];
    const idM = /\bid="([^"]+)"/.exec(thuoc_tinh);
    const clsM = /\bclass="([^"]+)"/.exec(thuoc_tinh);
    ra.push({
      id: idM ? idM[1] : null,
      cls: clsM ? clsM[1].trim().split(/\s+/) : [],
      the: m[0],
    });
  }
  return ra;
}

/**
 * Nút có id NÀY có được nối sự kiện thật không?
 *
 * Không chỉ kiểm "id có xuất hiện trong app.js" — như thế thì một nút chỉ
 * được đọc để đổi `.disabled` cũng lọt qua. Phải có bằng chứng
 * addEventListener, theo đúng hai lối viết đang dùng trong app.js:
 *
 *   document.getElementById('x').addEventListener(...)      // trực tiếp
 *   document.getElementById('x')?.addEventListener(...)     // optional chaining
 *   const b = document.getElementById('x'); b.addEventListener(...)  // qua biến
 *
 * PHẢI CHẤP NHẬN `?.` — sửa 30/08/2026.
 *
 * Bản đầu chỉ khớp `)` rồi `.addEventListener`. Ngày 28/08 mã mới nối năm nút
 * trình chiếu bằng optional chaining:
 *
 *     document.getElementById('btnPresPen')?.addEventListener('click', ...)
 *
 * Cửa báo ĐỎ "Nút CÓ trên giao diện nhưng KHÔNG ai nghe: btnPresMouse,
 * btnPresPen, btnPresHighlighter, btnPresLaser, btnPresEraser" — trong khi cả
 * năm nút ĐỀU có người nghe. Đọc mã ra ngay: `?.` chứ không phải `.`.
 *
 * Đây là CỬA SAI, không phải mã sai — và là lần thứ tư trong bốn ngày tôi để
 * một cửa khớp hụt. Ba lần trước: dò trúng chú thích chứa `returnValue`, dò
 * trúng dòng khai biến `btnModeFiles`, neo `indexOf` vào khối `keydown` đầu
 * tiên khi có nhiều khối.
 *
 * Một cửa báo đỏ oan cũng nguy như một cửa báo xanh oan: lần sau người ta sẽ
 * bỏ qua nó.
 */
function coNguoiNghe(id, js) {
  const idEsc = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Lối 1: nối thẳng, cho phép xuống dòng và cả `?.`
  const thang = new RegExp(
    `getElementById\\(\\s*['"\`]${idEsc}['"\`]\\s*\\)\\s*\\??\\.\\s*addEventListener`
  );
  if (thang.test(js)) return true;

  // Lối 2: gán vào biến rồi nối. Tìm tên biến, rồi tìm <bien>.addEventListener
  const ganBien = new RegExp(
    `(?:const|let|var)\\s+([A-Za-z_$][\\w$]*)\\s*=\\s*document\\.getElementById\\(\\s*['"\`]${idEsc}['"\`]\\s*\\)`,
    'g'
  );
  let g;
  while ((g = ganBien.exec(js)) !== null) {
    const bien = g[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (new RegExp(`\\b${bien}\\s*\\??\\.\\s*addEventListener`).test(js)) return true;
  }
  return false;
}

/** Nút không có id thì phải được nối qua MỘT trong ba lối, trên class của nó.
 *
 * Ba lối đang dùng thật trong `app.js`:
 *
 *     container.querySelectorAll('.x').forEach(b => b.addEventListener(...))
 *     e.target.closest('.x')      // uỷ quyền sự kiện
 *     e.target.matches('.x')      // uỷ quyền sự kiện, lối khác
 *
 * PHẢI CHẤP NHẬN `closest` / `matches` — sửa 30/08/2026.
 *
 * Bản đầu chỉ nhận `querySelectorAll`. Ngày 28/08 bốn nút
 * `<button class="quick-chip" data-action="...">` được nối bằng UỶ QUYỀN:
 *
 *     const chip = e.target.closest('.quick-chip');
 *
 * Cửa báo bốn nút ấy "không ai nghe" — sai. Uỷ quyền sự kiện là lối nối hợp lệ
 * và còn bền hơn: nút sinh động sau khi trang tải vẫn chạy, trong khi
 * `querySelectorAll` chạy một lần thì không.
 *
 * Đây là lỗ thứ hai trong cùng một cửa, phát hiện cùng ngày với lỗ `?.` ở
 * `coNguoiNghe`. Cả hai đều là CỬA HẸP chứ không phải mã hỏng.
 */
function coNguoiNgheQuaClass(cls, js) {
  return cls.some((c) => {
    const cEsc = c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(
      `(?:querySelectorAll|querySelector|closest|matches)\\([^)]*\\.${cEsc}\\b`
    ).test(js);
  });
}

describe('Cửa cứng: mọi nút phải có người nghe', () => {
  test('mọi <button id="..."> đều được nối addEventListener', () => {
    const nut = docCacNut(HTML).filter((b) => b.id);
    assert.ok(nut.length >= 25, `Phải tìm thấy nhiều nút có id, chỉ thấy ${nut.length}`);

    const treo = nut.filter((b) => !coNguoiNghe(b.id, APP_JS)).map((b) => b.id);
    assert.deepStrictEqual(
      treo,
      [],
      `Nút CÓ trên giao diện nhưng KHÔNG ai nghe: ${treo.join(', ')}\n` +
        'Bấm vào sẽ không có gì xảy ra. Nối addEventListener, hoặc bỏ nút đi.'
    );
  });

  test('mọi <button> không có id đều được nối qua class', () => {
    const nut = docCacNut(HTML).filter((b) => !b.id);
    const treo = nut
      .filter((b) => !coNguoiNgheQuaClass(b.cls, APP_JS))
      .map((b) => b.the.slice(0, 80));
    assert.deepStrictEqual(
      treo,
      [],
      `Nút không id và không class nào được querySelectorAll:\n${treo.join('\n')}`
    );
  });
});
