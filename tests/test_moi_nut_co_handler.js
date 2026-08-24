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

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const HTML = fs.readFileSync(path.join(THU_MUC, 'index.html'), 'utf-8');
const APP_JS = fs.readFileSync(path.join(THU_MUC, 'app.js'), 'utf-8');

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
 *   document.getElementById('x').addEventListener(...)     // trực tiếp
 *   const b = document.getElementById('x'); b.addEventListener(...)  // qua biến
 */
function coNguoiNghe(id, js) {
  const idEsc = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Lối 1: nối thẳng, cho phép xuống dòng giữa chuỗi
  const thang = new RegExp(
    `getElementById\\(\\s*['"\`]${idEsc}['"\`]\\s*\\)\\s*\\.addEventListener`
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
    if (new RegExp(`\\b${bien}\\s*\\.addEventListener`).test(js)) return true;
  }
  return false;
}

/** Nút không có id thì phải được nối qua querySelectorAll trên một class của nó. */
function coNguoiNgheQuaClass(cls, js) {
  return cls.some((c) => {
    const cEsc = c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`querySelectorAll\\([^)]*\\.${cEsc}\\b`).test(js);
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
