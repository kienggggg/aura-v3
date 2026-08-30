// tests/test_bo_cham_khong_tu_bia.js
//
// 30/08/2026. Auto-Grader tung tu viet loi giai bang JS theo `c.id` roi so voi
// `expected` do chinh app.js khai — hai ban sao cua cung mot dap an, luon khop.
// The cua nguoi hoc khong bao gio duoc doc. Do tay: canvas 0 the, 0 request,
// van ra 4/4 · 100% · "XUAT SAC", va con ghi vao localStorage
// aura_solved_challenges — huy hieu vinh vien cho viec chua lam.
//
// Cua nay giu MOT bat bien, khong dò chuỗi bua bai:
//   trong than ham cham diem, neu co chu phan quyet (PASS / HOAN THANH / XUAT SAC)
//   HOAC co lenh ghi "da giai", thi PHAI co lenh goi cong chay ma that.
// Tuc la: muon tuyen bo thi phai do. Khong do duoc thi cam tuyen bo.
//
// Than ham lay bang DEM NGOAC tu ten ham, khong bang indexOf mot moc doan —
// hai lan truoc neo bang indexOf deu truot khi mã đổi (xem test_chan_mat_du_lieu.js).

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8');

function thanHam(tenHam) {
  const neo = 'function ' + tenHam + '(';
  const i = APP_JS.indexOf(neo);
  assert.notStrictEqual(i, -1, 'khong tim thay ham ' + tenHam);
  let j = APP_JS.indexOf('{', i);
  assert.notStrictEqual(j, -1, 'ham ' + tenHam + ' khong co than');
  let sau = 1;
  j += 1;
  while (sau > 0) {
    assert.ok(j < APP_JS.length, 'ngoac khong dong trong ' + tenHam);
    const ch = APP_JS[j];
    if (ch === '{') sau += 1;
    else if (ch === '}') sau -= 1;
    j += 1;
  }
  return APP_JS.slice(i, j);
}

const CHU_PHAN_QUYET = [
  '✓ PASS', 'HOÀN THÀNH 100%', 'XUẤT SẮC',
  'VƯỢT QUA THỬ THÁCH',
];
const LENH_GHI_DA_GIAI = ['danhDauBaiDaGiai('];
const LENH_DO_THAT = ['/api/chay', 'goiApiChayMa', 'chayMaThat'];

test('ham cham diem khong tuyen bo PASS neu khong goi cong chay ma that', () => {
  const than = thanHam('chamDiemBaiTap');
  const coDo = LENH_DO_THAT.some(t => than.includes(t) && than.includes('fetch'));
  if (coDo) return;                       // co do that -> duoc phep phan quyet
  for (const chu of CHU_PHAN_QUYET) {
    assert.ok(!than.includes(chu),
      'chamDiemBaiTap in phan quyet "' + chu + '" nhung khong goi cong chay ma that');
  }
});

test('ham cham diem khong ghi "da giai" neu khong goi cong chay ma that', () => {
  const than = thanHam('chamDiemBaiTap');
  const coDo = LENH_DO_THAT.some(t => than.includes(t) && than.includes('fetch'));
  if (coDo) return;
  for (const lenh of LENH_GHI_DA_GIAI) {
    assert.ok(!than.includes(lenh),
      'chamDiemBaiTap goi ' + lenh + ' — cong XP cho bai chua ai do');
  }
});

test('khong do duoc thi phai NOI LA khong do duoc', () => {
  const than = thanHam('chamDiemBaiTap');
  const coDo = LENH_DO_THAT.some(t => than.includes(t) && than.includes('fetch'));
  if (coDo) return;
  assert.ok(than.includes('CHƯA CHẤM ĐƯỢC'),
    'chamDiemBaiTap khong do duoc nhung cung khong noi ra trang thai do');
});

test('cot "Thuc Te" khong duoc dien so khi chua chay gi', () => {
  const than = thanHam('chamDiemBaiTap');
  if (!than.includes('Thực Tế')) return;
  const coDo = LENH_DO_THAT.some(t => than.includes(t) && than.includes('fetch'));
  if (coDo) return;
  // KHONG dung /actual/i: chu "Actual" nam ngay trong NHAN hien thi
  // "Thuc Te (Actual):" nen se khop nham — dung ho benh do chuoi con
  // o CLAUDE.md §4. Chi bat DINH DANH trong ma: actualVal hoac .actual
  assert.ok(!/\bactualVal\b|\.actual\b/.test(than),
    'con cot "Thuc Te" lay tu bien actual trong khi khong chay gi');
});
