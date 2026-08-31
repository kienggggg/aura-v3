// tests/test_khong_goi_ham_khong_ton_tai.js
//
// 30/08/2026. Nút "⏭ Bước" trong chế độ Trình Chiếu gọi `buocTiepTheo()` — một
// cái tên KHÔNG TỒN TẠI ở đâu trong app.js. Hàm thật tên `buocTiep`, và nút
// btnDebugStepNext ở thanh gỡ lỗi thường vẫn gọi đúng tên ấy.
//
// Đo tay: vào Trình Chiếu, bấm "⏭ Bước" lần đầu -> mở gỡ lỗi (đúng). Bấm lần
// hai -> `Uncaught ReferenceError: buocTiepTheo is not defined`, bộ đếm đứng yên
// ở "Bước 1 / 3". Nút chưa từng hoạt động ở nhánh đó.
//
// Vì sao không cửa nào bắt được: nút CÓ handler (test_moi_nut_co_handler.js
// xanh), cú pháp hợp lệ (`node --check` xanh), và lỗi chỉ nổ ở NHÁNH `else` —
// nhánh chỉ chạy sau khi gỡ lỗi đã bật. Một nhánh hiếm là chỗ trú tốt nhất cho
// lỗi loại này.
//
// Cửa này quét MỌI lời gọi `ten(...)` và đòi `ten` phải được định nghĩa trong
// chính tệp, hoặc nằm trong danh sách sẵn có của trình duyệt.
//
// ĐỘ NHIỄU, đo trước khi viết: sau khi sửa lỗi trên, chỉ còn 3 tên chưa khai —
// Uint8Array, DataView, URLSearchParams — đều là hằng của trình duyệt. Tức nhiễu
// gần bằng 0. Nếu con số ấy phình lên, ĐỪNG nới danh sách bừa: xem lại xem có
// phải một lời gọi thật sự hỏng không.
//
// GIỚI HẠN: đây là phân tích văn bản, không phải trình biên dịch. Nó bóc chú
// thích và chuỗi trước khi quét, nhưng không hiểu phạm vi (scope) — một hàm khai
// bên trong hàm khác vẫn được tính là "đã định nghĩa" dù chỗ gọi không thấy nó.
// Nó bắt được cái ĐÃ bắt: tên gọi mà KHÔNG khai ở đâu cả.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const DUONG = path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js');

// Hằng có sẵn của trình duyệt / Node. Thêm vào đây phải là việc CÓ Ý.
const SAN_CO = new Set(`
window document console JSON Math Object Array String Number Boolean Date RegExp
Promise Set Map WeakMap WeakSet Error TypeError RangeError Symbol Proxy Reflect BigInt
parseInt parseFloat isNaN isFinite encodeURIComponent decodeURIComponent encodeURI decodeURI
setTimeout setInterval clearTimeout clearInterval requestAnimationFrame cancelAnimationFrame
fetch alert confirm prompt localStorage sessionStorage navigator location history URL Blob
FileReader File FormData Headers Request Response AbortController Intl TextEncoder TextDecoder
Event CustomEvent KeyboardEvent MouseEvent PointerEvent MutationObserver ResizeObserver
IntersectionObserver getComputedStyle structuredClone queueMicrotask atob btoa
Uint8Array Uint16Array Uint32Array Int8Array Int16Array Int32Array Float32Array Float64Array
DataView ArrayBuffer URLSearchParams
if for while switch return typeof instanceof new delete void in of do else try catch finally
function class const let var this super throw yield await async break continue case default
require module exports process Buffer globalThis undefined null true false
HTMLElement Node Element SVGElement Image Audio Option DOMParser XMLSerializer
TheValidator
`.trim().split(/\s+/));

function bocChuThichVaChuoi(s) {
  let r = s.replace(/\/\*[\s\S]*?\*\//g, ' ');
  r = r.split('\n').map((d) => (/^\s*\/\//.test(d) ? '' : d)).join('\n');
  r = r.replace(/'(?:[^'\\\n]|\\.)*'/g, "''");
  r = r.replace(/"(?:[^"\\\n]|\\.)*"/g, '""');
  r = r.replace(/`(?:[^`\\]|\\.)*`/g, '``');
  return r;
}

function tenDaKhai(s) {
  const ra = new Set();
  const them = (re, nhom = 1) => {
    let m;
    const r = new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g');
    while ((m = r.exec(s)) !== null) if (m[nhom]) ra.add(m[nhom]);
  };
  them(/\bfunction\s+([A-Za-z_$][\w$]*)/g);
  them(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=/g);
  them(/\bclass\s+([A-Za-z_$][\w$]*)/g);
  them(/\bcatch\s*\(\s*([A-Za-z_$][\w$]*)/g);
  them(/\bfor\s*\(\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)/g);
  // tham số: của arrow function và của function declaration
  for (const re of [/\(([^()]{0,160})\)\s*=>/g, /\bfunction[^(]{0,40}\(([^)]{0,200})\)/g]) {
    let m;
    while ((m = re.exec(s)) !== null) {
      for (const t of (m[1] || '').match(/[A-Za-z_$][\w$]*/g) || []) ra.add(t);
    }
  }
  return ra;
}

function loiGoiKhongKhai() {
  const goc = fs.readFileSync(DUONG, 'utf8');
  const s = bocChuThichVaChuoi(goc);
  const khai = tenDaKhai(s);
  const ra = new Map();
  const re = /(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(/g;
  let m;
  while ((m = re.exec(s)) !== null) {
    const ten = m[1];
    if (SAN_CO.has(ten) || khai.has(ten)) continue;
    const dong = s.slice(0, m.index).split('\n').length;
    if (!ra.has(ten)) ra.set(ten, []);
    ra.get(ten).push(dong);
  }
  return ra;
}

test('không gọi hàm nào chưa được định nghĩa trong app.js', () => {
  const thieu = loiGoiKhongKhai();
  const bao = [...thieu.entries()].map(([t, d]) => `${t}() ở dòng ${d.join(', ')}`);
  assert.deepStrictEqual(bao, [],
    'gọi một cái tên không tồn tại — nút sẽ nổ ReferenceError và không làm gì. ' +
    'Nếu đây là hằng của trình duyệt thì thêm vào SAN_CO một cách CÓ Ý, ' +
    'đừng nới danh sách để cho qua một lời gọi thật sự hỏng');
});

test('phép quét thật sự tìm được thứ gì đó — không phải xanh rỗng', () => {
  const goc = fs.readFileSync(DUONG, 'utf8');
  const s = bocChuThichVaChuoi(goc);
  assert.ok(tenDaKhai(s).size > 300,
    'chỉ thấy ' + tenDaKhai(s).size + ' tên được khai — bộ tách đã hỏng, ' +
    'và một bộ tách hỏng thì khẳng định ở trên xanh vì không quét được gì');
  const soLoiGoi = (s.match(/(?<![.\w$])[A-Za-z_$][\w$]*\s*\(/g) || []).length;
  assert.ok(soLoiGoi > 1000, 'chỉ thấy ' + soLoiGoi + ' lời gọi — bộ tách đã hỏng');
});

test('bóc chú thích và chuỗi, để không khớp nhầm', () => {
  const thu = [
    '// hamKhongCoThat();',
    "const a = 'hamTrongChuoi()';",
    '/* hamTrongKhoi(); */',
    'thatSuGoi();',
  ].join('\n');
  const sau = bocChuThichVaChuoi(thu);
  assert.ok(!sau.includes('hamKhongCoThat'), 'chú thích cả dòng phải bị bóc');
  assert.ok(!sau.includes('hamTrongChuoi'), 'nội dung chuỗi phải bị bóc');
  assert.ok(!sau.includes('hamTrongKhoi'), 'chú thích khối phải bị bóc');
  assert.ok(sau.includes('thatSuGoi('), 'lời gọi thật không được bóc mất');
});
