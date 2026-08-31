// tests/test_nut_tai_svg.js
//
// 30/08/2026. NÚT "TẢI FILE SVG" CHƯA TỪNG HOẠT ĐỘNG.
//
// Đo tay: mở Sơ Đồ Khối với 2 thẻ trên canvas, `#flowchartModal svg` có thật —
// người dùng đang NHÌN THẤY sơ đồ. Bấm btnDownloadSVG:
//     0 blob được tạo · 0 thẻ <a> được bấm
//     #nhanNhanh hiện: "Không có sơ đồ khối hợp lệ để tải!"
//
// Nguyên nhân: `sinhSVGSoDoKhoi` dựng chuỗi bằng template literal mở đầu bằng
// xuống dòng + 6 dấu cách (`let svg = \`` rồi mới tới `<svg class="flow-svg"`),
// nên giá trị trả về bắt đầu bằng KHOẢNG TRẮNG. Chốt chặn
// `currentGeneratedSVG.startsWith('<svg')` vì thế LUÔN sai với mọi cây không rỗng.
//
// Bằng chứng độc lập từ cùng ngày: gói zip do 1-Click Packager sinh ra chứa
// `flowchart.svg` mở đầu bằng đúng 6 dấu cách — giải base64 ra thấy tận mắt.
//
// Sửa ở NGUỒN chứ không nới chốt chặn: chốt ấy đúng, chuỗi mới là thứ bẩn.
//
// GIỚI HẠN: đây là kiểm trên mã. Nó chặn việc gỡ mất trim; nó KHÔNG chứng minh
// nút chạy. Phần ấy đã bấm tay sau khi vá: 1 blob · 1 thẻ <a> · thông báo
// "Đã tải tệp vector SVG thành công!".

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');

function thanHam(ten) {
  const i = APP_JS.indexOf('function ' + ten + '(');
  assert.notStrictEqual(i, -1, 'không tìm thấy hàm ' + ten);
  let j = APP_JS.indexOf('{', i), sau = 1;
  j += 1;
  while (sau > 0) {
    assert.ok(j < APP_JS.length, 'ngoặc không đóng trong ' + ten);
    const c = APP_JS[j];
    if (c === '{') sau += 1;
    else if (c === '}') sau -= 1;
    j += 1;
  }
  return APP_JS.slice(i, j);
}

test('cái bẫy vẫn còn đó: chuỗi SVG mở đầu bằng khoảng trắng', () => {
  const than = thanHam('sinhSVGSoDoKhoi');
  const m = /let svg = `([\s\S]{0,30})/.exec(than);
  assert.ok(m, 'không còn `let svg = ` — cấu trúc đổi, đọc lại cửa này');
  assert.match(m[1], /^\s+</,
    'template literal không còn mở đầu bằng khoảng trắng nữa — nếu đã sửa ở đó ' +
    'thì cập nhật cửa này, đừng để nó canh một cái bẫy không còn tồn tại');
});

test('giá trị đem đi kiểm phải sạch khoảng trắng — nguồn trim HOẶC chốt trim', () => {
  const nguon = thanHam('sinhSVGSoDoKhoi');
  const chot = thanHam('taiSVGSoDoKhoi');

  const nguonTrim = /return\s+svg\s*\.trim\(\)/.test(nguon);
  const chotTrim = /currentGeneratedSVG\s*\.trim\(\)\s*\.startsWith/.test(chot);

  assert.ok(nguonTrim || chotTrim,
    'sinhSVGSoDoKhoi trả chuỗi mở đầu bằng khoảng trắng, mà taiSVGSoDoKhoi lại ' +
    'kiểm startsWith("<svg") trên chuỗi chưa trim — nút tải sẽ luôn từ chối, ' +
    'kèm câu "Không có sơ đồ khối hợp lệ" trong khi sơ đồ đang hiện trên màn hình');
});

test('chốt chặn vẫn còn — đừng "sửa" bằng cách bỏ nó đi', () => {
  const chot = thanHam('taiSVGSoDoKhoi');
  assert.match(chot, /startsWith\('<svg'\)/,
    'bỏ chốt chặn thì cây rỗng sẽ tải về một tệp .svg chứa thẻ <div> báo lỗi');
  assert.match(chot, /URL\.createObjectURL/, 'không còn tạo blob để tải');
});

test('cây rỗng thì vẫn phải TỪ CHỐI, không được tải bừa', () => {
  const nguon = thanHam('sinhSVGSoDoKhoi');
  // nhánh cây rỗng phải trả về thứ KHÔNG mở đầu bằng <svg, để chốt chặn bắt được
  const m = /if\s*\(!treeNodes\s*\|\|\s*treeNodes\.length === 0\)\s*\{\s*return\s*`([\s\S]{0,40})/.exec(nguon);
  assert.ok(m, 'mất nhánh cây rỗng — cây rỗng sẽ rơi xuống nhánh sinh SVG thật');
  assert.ok(!m[1].trim().startsWith('<svg'),
    'nhánh cây rỗng nay trả về chuỗi mở đầu bằng <svg — chốt chặn sẽ cho qua và ' +
    'người dùng tải về một sơ đồ trống');
});
