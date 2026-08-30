// tests/test_o_tim.js
//
// 30/08/2026. Ô Tìm (Ctrl+F) nói "Tìm trong chương trình…" nhưng chỉ tìm trong
// GIÁ TRỊ người dùng gõ vào thẻ. Đo tay, chương trình đang hiện trên màn hình ở
// chế độ Mã Thuần là `def chào(tên): … print(chào(người))`:
//
//     chào 1/3 · người 1/2 · danh_sách 1/2 · Sếp 1/1     tìm được
//     def 0/0 · print 0/0 · return 0/0                    KHÔNG, dù đang nhìn thấy
//
// `0/0` dưới cái nhãn đó đọc như "chương trình không có chữ def". Cùng họ với
// nhãn nói sai việc ở CLAUDE.md mục 4.
//
// Cửa này CHẠY THẬT hàm tìm của app: trích `TU_KHOA_PYTHON_CUA_THE`,
// `chuTrenThe` và `gomThePhuHop` ra khỏi app.js bằng đếm ngoặc rồi thi hành
// chúng. Không dò chuỗi trong mã — đổi bảng từ khoá đi thì cửa đỏ vì HÀNH VI.
//
// GIỚI HẠN: cửa chạy ba khối đó tách khỏi trình duyệt, nên nó không chứng minh
// ô Tìm nối đúng vào nút và vào ô nhập. Phần ấy vẫn phải bấm tay.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');

function trichKhoi(neo) {
  const i = APP_JS.indexOf(neo);
  assert.notStrictEqual(i, -1, 'khong tim thay: ' + neo);
  let j = APP_JS.indexOf('{', i);
  let sau = 1;
  j += 1;
  while (sau > 0) {
    assert.ok(j < APP_JS.length, 'ngoac khong dong sau: ' + neo);
    const ch = APP_JS[j];
    if (ch === '{') sau += 1;
    else if (ch === '}') sau -= 1;
    j += 1;
  }
  return APP_JS.slice(i, j);
}

const nguon = [
  trichKhoi('const TU_KHOA_PYTHON_CUA_THE = {'),
  trichKhoi('function chuTrenThe(node) {'),
  trichKhoi('function gomThePhuHop(danhSach, tuKhoa, ra) {'),
  'return { chuTrenThe, gomThePhuHop, TU_KHOA_PYTHON_CUA_THE };',
].join('\n');
const app = new Function(nguon)();

// Đúng chương trình đã dùng để đo tay.
const CAY = [
  { id: 'v1', ma: 'ham', o: { ten_ham: 'chào', tham_so: 'tên' }, than: [
    { id: 'v2', ma: 'gan', o: { ten_bien: 'lời', gia_tri: 'f"Xin chào {tên}"' }, than: [] },
    { id: 'v3', ma: 'tra_ve', o: { gia_tri: 'lời' }, than: [] },
  ] },
  { id: 'v4', ma: 'gan', o: { ten_bien: 'danh_sách', gia_tri: '["Sếp", "Kiên"]' }, than: [] },
  { id: 'v5', ma: 'lap_moi', o: { bien: 'người', day: 'danh_sách' }, than: [
    { id: 'v6', ma: 'in_ra', o: { noi_dung: 'chào(người)' }, than: [] },
  ] },
];

function tim(tuKhoa) {
  return app.gomThePhuHop(CAY, tuKhoa.toLowerCase().trim(), []);
}

test('tìm được từ khoá Python đang hiện trên màn hình', () => {
  assert.deepStrictEqual(tim('def'), ['v1'], 'thẻ hàm phải khớp "def"');
  assert.deepStrictEqual(tim('print'), ['v6'], 'thẻ in ra phải khớp "print"');
  assert.deepStrictEqual(tim('return'), ['v3'], 'thẻ trả về phải khớp "return"');
  assert.deepStrictEqual(tim('for'), ['v5'], 'thẻ vòng lặp phải khớp "for"');
});

test('vẫn tìm được nội dung tiếng Việt người dùng gõ', () => {
  assert.deepStrictEqual(tim('chào'), ['v1', 'v2', 'v6']);
  assert.deepStrictEqual(tim('người'), ['v5', 'v6']);
  assert.deepStrictEqual(tim('danh_sách'), ['v4', 'v5']);
  assert.deepStrictEqual(tim('sếp'), ['v4']);
});

test('chữ không có trong chương trình thì phải ra rỗng', () => {
  assert.deepStrictEqual(tim('ZZZKHONGCOCHUNAY'), []);
  assert.deepStrictEqual(tim('while'), [], 'không có thẻ lặp_khi nào trong cây này');
  assert.deepStrictEqual(tim('import'), []);
});

// Chiều ngược lại: bảng từ khoá KHÔNG được kéo theo chỗ giữ chỗ. Nếu ai đó dùng
// lại NHAN_CU_PHAP (`x = 10`, `for i in day:`) thì tìm "10" sẽ khớp mọi thẻ gán
// và tìm "day" khớp mọi vòng lặp — nhiễu đến mức ô Tìm hết dùng được.
test('bảng từ khoá không được kéo theo chỗ giữ chỗ của nhãn thẻ', () => {
  assert.deepStrictEqual(tim('10'), [], 'thẻ gán không được khớp "10"');
  assert.deepStrictEqual(tim('day'), [], 'thẻ vòng lặp không được khớp "day"');
  assert.deepStrictEqual(tim('args'), [], 'thẻ hàm không được khớp "args"');
  assert.deepStrictEqual(tim('cond'), [], 'thẻ điều kiện không được khớp "cond"');
  assert.deepStrictEqual(tim('val'), [], 'thẻ trả về không được khớp "val"');
});

test('mỗi mã thẻ trong bảng chỉ được chứa từ khoá Python thật', () => {
  const HOP_LE = new Set(['print', 'if', 'else', 'for', 'in', 'while', 'return',
    'def', '#', 'import', 'break', 'continue', 'try', 'except', 'as']);
  for (const [ma, chu] of Object.entries(app.TU_KHOA_PYTHON_CUA_THE)) {
    for (const t of String(chu).split(/\s+/).filter(Boolean)) {
      assert.ok(HOP_LE.has(t),
        `thẻ "${ma}" khai từ khoá "${t}" — không phải từ khoá Python, ` +
        'nhiều khả năng là chỗ giữ chỗ lọt vào');
    }
  }
});
