// tests/test_loi_may_chu_khong_do_cho_nguoi_dung.js
//
// 30/08/2026. Quét trục ĐƯỜNG LỖI: app nói gì khi mọi thứ hỏng.
//
// `runProgram` đọc phản hồi của /api/chay rồi rẽ:
//     if  (res.status === 'PASS')     -> đạt
//     elif(res.status === 'TIMEOUT')  -> quá giờ
//     else                            -> "LỖI RUNTIME"
// Không chỗ nào kiểm `resp.ok`. Nên MỌI phản hồi khác — kể cả thân lỗi 500
// `{"error": "..."}` không có trường `status` — rơi vào nhánh cuối. Đo:
//
//     máy chủ trả 500  ->  trạng thái "LỖI RUNTIME"
//                          "Lỗi không xác định … [Thất bại · Exit code: undefined]"
//
// Máy chủ hỏng, nhưng người mới học đọc thành "mã của tôi có lỗi khi chạy" rồi
// đi tìm một con bọ KHÔNG TỒN TẠI trong mã mình. Cùng họ với nhãn nói sai việc,
// và cùng họ với "không có test nào bị đỏ" đã sửa cùng ngày: ba trạng thái phải
// tách rời — chạy xong và ĐẠT · chạy xong và SAI · KHÔNG CHẠY ĐƯỢC.
//
// Đường /api/trace đã kiểm `resp.ok` từ đầu; đường /api/chay bị sót.
//
// Đo lại sau khi vá, cả hai chiều:
//     máy chủ 500        -> "KHÔNG CHẠY ĐƯỢC — lỗi của máy chủ, không phải mã bạn"
//     403 tắt chạy mã    -> như trên, kèm "Chay ma dang tat"
//     mã 1/0 nổ thật     -> VẪN "LỖI RUNTIME", có ZeroDivisionError, KHÔNG đổ cho máy chủ
//     chạy bình thường   -> PASS, 50 ms
//
// GIỚI HẠN: kiểm trên mã nguồn. Bốn phép đo hành vi ở trên đã bấm tay; cửa này
// chỉ chặn việc rào chắn bị gỡ đi.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');

// Bóc chú thích CẢ DÒNG trước khi so chuỗi. Gieo thử bắt được: thay
// `metaStatus.textContent = 'LỖI RUNTIME'` bằng chuỗi khác thì cửa VẪN XANH, vì
// chữ "LỖI RUNTIME" còn nằm trong CHÚ THÍCH ở đầu tệp app.js do chính tôi viết.
// Đúng họ bệnh dò chuỗi con ở CLAUDE.md mục 4 — đã dính ba lần trong ngày.
function bocChuThich(s) {
  let r = s.replace(/\/\*[\s\S]*?\*\//g, ' ');
  return r.split('\n').map((d) => (/^\s*\/\//.test(d) ? '' : d)).join('\n');
}

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
  return bocChuThich(APP_JS.slice(i, j));
}

test('runProgram phải kiểm resp.ok TRƯỚC khi diễn giải res.status', () => {
  const than = thanHam('runProgram');
  const iKiem = than.indexOf('!resp.ok');
  const iDoc = than.indexOf("res.status === 'PASS'");
  assert.notStrictEqual(iKiem, -1,
    'không còn kiểm resp.ok — lỗi 500 sẽ rơi vào nhánh cuối và bị gọi là "LỖI RUNTIME"');
  assert.ok(iKiem < iDoc,
    'kiểm resp.ok phải nằm TRƯỚC chỗ đọc res.status, nếu không thì đã muộn');
});

test('lỗi máy chủ phải nói rõ đó KHÔNG phải lỗi mã của người dùng', () => {
  const than = thanHam('runProgram');
  assert.match(than, /KHÔNG CHẠY ĐƯỢC/,
    'mất trạng thái thứ ba — máy chủ hỏng lại bị gộp vào "chạy xong và sai"');
  assert.match(than, /không phải của mã bạn viết/,
    'câu này là thứ giữ người mới học khỏi đi tìm một con bọ không tồn tại');
});

test('nhánh LỖI RUNTIME vẫn còn — đừng "sửa" bằng cách đổ hết cho máy chủ', () => {
  const than = thanHam('runProgram');
  assert.match(than, /LỖI RUNTIME/,
    'mã người dùng nổ lỗi thật thì vẫn phải được gọi đúng tên');
  assert.match(than, /res\.stderr/, 'không còn hiện stderr thật của lần chạy');
});

test('ba trạng thái phải tách rời, không gộp thành hai', () => {
  const than = thanHam('runProgram');
  for (const [chu, y] of [["'PASS'", 'chạy xong và đạt'],
                          ["'TIMEOUT'", 'quá giờ'],
                          ['KHÔNG CHẠY ĐƯỢC', 'không đo được'],
                          ['LỖI RUNTIME', 'chạy xong và sai']]) {
    assert.ok(than.includes(chu), `mất nhánh "${y}" (${chu})`);
  }
});

test('đường /api/trace cũng phải giữ nguyên chốt resp.ok của nó', () => {
  // Đường này làm đúng từ đầu — ghi lại để nếu ai đó "dọn cho gọn" thì cửa đỏ.
  const i = APP_JS.indexOf("authFetch('/api/trace'");
  assert.notStrictEqual(i, -1, 'không còn lời gọi /api/trace');
  const quanh = bocChuThich(APP_JS.slice(i, i + 900));
  assert.match(quanh, /!resp\.ok|resp\.ok\s*===\s*false/,
    '/api/trace mất chốt resp.ok — sẽ đi vào đúng cái bẫy /api/chay vừa thoát');
});
