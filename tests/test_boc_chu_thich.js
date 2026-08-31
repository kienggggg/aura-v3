// tests/test_boc_chu_thich.js
//
// `tools/boc_chu_thich.js` là bộ lọc mà 6 cửa khác dựa vào. Nó bóc sai thì cửa
// nào cũng sai theo — bóc thiếu gây ĐỎ GIẢ (khó chịu), bóc thừa gây XANH GIẢ
// (nguy hiểm, vì nó cắt mất chính đoạn mã mà cửa đang tìm).
//
// 30/08/2026: 5/6 cửa dò chuỗi trên app.js bị chú thích lừa. Đo bằng gieo, không
// đoán: xoá dòng mã thật, để lại một chú thích mang đúng chữ cửa tìm.
//     bị lừa   test_bo_cham · test_nut_tai_svg · test_phim_tat · test_nhan_noi_dung · test_moi_nut
//     thoát    test_o_tim   — cái duy nhất CHẠY mã trích ra thay vì dò chuỗi

const assert = require('node:assert');
const { test } = require('node:test');
const {
  bocChuThich, bocChuThichVaChuoi, bocMoiChuThich,
} = require('../tools/boc_chu_thich.js');

const NL = '\n';

test('bocChuThich bỏ chú thích cả dòng và khối, giữ nguyên mã', () => {
  const vao = [
    '  // hamGia();',
    '  hamThat();',
    '  /* khoiGia(); */',
    '  const x = 1;',
  ].join(NL);
  const ra = bocChuThich(vao);
  assert.ok(!ra.includes('hamGia'), 'chú thích cả dòng phải bị bỏ');
  assert.ok(!ra.includes('khoiGia'), 'chú thích khối phải bị bỏ');
  assert.ok(ra.includes('hamThat()'), 'mã thật không được bỏ mất');
  assert.ok(ra.includes('const x = 1'), 'mã thật không được bỏ mất');
});

test('bocChuThich CỐ Ý giữ chú thích cuối dòng — hướng sai an toàn', () => {
  const ra = bocChuThich('  hamThat();   // ghiChuCuoiDong');
  assert.ok(ra.includes('hamThat()'));
  assert.ok(ra.includes('ghiChuCuoiDong'),
    'nếu nó bắt đầu bóc cuối dòng thì rủi ro cắt nhầm mã tăng — dùng ' +
    'bocMoiChuThich cho chỗ cần, đừng đổi hàm này');
});

test('bocMoiChuThich bóc CẢ chú thích cuối dòng', () => {
  const ra = bocMoiChuThich("  if (a) { }   // e.key === 'F11'");
  assert.ok(ra.includes('if (a)'), 'mã thật phải còn');
  assert.ok(!ra.includes('F11'), 'chú thích cuối dòng phải bị bóc — đúng chỗ đã hỏng');
});

test('bocMoiChuThich KHÔNG cắt nhầm dấu // nằm trong chuỗi', () => {
  for (const vao of [
    `const u = 'http://vi-du.com/a';`,
    `const u = "https://vi-du.com/b";`,
    'const u = `ws://vi-du.com/c`;',
  ]) {
    const ra = bocMoiChuThich(vao);
    assert.ok(ra.includes('vi-du.com'),
      `cắt nhầm // trong chuỗi: ${vao} -> ${ra}`);
  }
});

test('bocMoiChuThich xử lý được dấu nháy đã thoát trong chuỗi', () => {
  const vao = `const s = 'anh \\'ta\\' nói';   // ghiChuCuoiDong`;
  const ra = bocMoiChuThich(vao);
  assert.ok(ra.includes('anh'), 'nội dung chuỗi phải còn');
  assert.ok(!ra.includes('ghiChuCuoiDong'), 'chú thích cuối dòng phải bị bóc');
});

test('bocMoiChuThich giữ nguyên số dòng — để báo lỗi còn trỏ đúng chỗ', () => {
  const vao = ['a();', '/* nhieu', 'dong', 'chu thich */', 'b();'].join(NL);
  const ra = bocMoiChuThich(vao);
  assert.strictEqual(ra.split(NL).length, vao.split(NL).length,
    'bóc khối nhiều dòng không được làm mất dòng, nếu không thì số dòng ' +
    'trong thông báo lỗi của các cửa sẽ trỏ sai');
});

test('bocChuThichVaChuoi bóc cả nội dung chuỗi', () => {
  const ra = bocChuThichVaChuoi(`goiThat('chuoiGia');`);
  assert.ok(ra.includes('goiThat('), 'lời gọi thật phải còn');
  assert.ok(!ra.includes('chuoiGia'), 'nội dung chuỗi phải bị bóc');
});

test('cả ba hàm chịu được đầu vào rỗng và null', () => {
  for (const f of [bocChuThich, bocChuThichVaChuoi, bocMoiChuThich]) {
    assert.strictEqual(f(''), '');
    assert.strictEqual(f(null), '');
    assert.strictEqual(f(undefined), '');
  }
});

test('không bóc thừa: mã thật trong app.js phải sống sót', () => {
  // Ca đối chứng trên tệp THẬT, không phải chuỗi tự bịa: nếu bộ bóc ăn mất mã
  // thì mọi cửa dùng nó sẽ xanh giả, và không khẳng định nào ở trên bắt được.
  const fs = require('node:fs');
  const path = require('node:path');
  const goc = fs.readFileSync(
    path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');
  for (const [f, ten] of [[bocChuThich, 'bocChuThich'], [bocMoiChuThich, 'bocMoiChuThich']]) {
    const ra = f(goc);
    for (const moc of ['function runProgram(', 'function chamDiemBaiTap(',
                       "authFetch('/api/chay'", 'function sinhSVGSoDoKhoi(']) {
      assert.ok(ra.includes(moc), `${ten} ăn mất "${moc}" khỏi app.js`);
    }
    assert.ok(ra.length > goc.length * 0.5,
      `${ten} cắt mất hơn nửa app.js (${ra.length}/${goc.length}) — bóc thừa`);
  }
});
