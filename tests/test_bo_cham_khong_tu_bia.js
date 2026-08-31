// tests/test_bo_cham_khong_tu_bia.js
//
// 30/08/2026. Auto-Grader tung tu viet loi giai bang JS theo `c.id` roi so voi
// `expected` do chinh app.js khai — hai ban sao cua cung mot dap an, luon khop.
// The cua nguoi hoc khong bao gio duoc doc. Do tay: canvas 0 the, 0 request,
// van ra 4/4 · 100% · "XUAT SAC", va con ghi vao localStorage
// aura_solved_challenges — huy hieu vinh vien cho viec chua lam.
//
// BAN DAU cua nay giu luat: "co chu phan quyet thi phai co lenh goi cong chay ma
// that". Luat do dung khi bo cham CHUA duoc noi. Ngay bo cham duoc noi that vao
// /api/chay thi no thanh VO HIEU — dieu kien "co nguon that" luon dung nen moi
// khang dinh deu tro ve som. Do duoc: gieo lai dung loi goc (loi giai cung theo
// c.id + danhDauBaiDaGiai vo dieu kien) -> ma thoat 0, cua nuot sach.
//
// Nen luat nay viet lai theo hai the gioi:
//   CHUA noi cong  -> cam moi chu phan quyet (luat cu, van con gia tri)
//   DA noi cong    -> phan quyet phai DEN TU phan hoi cua lan chay, va viec cong
//                     XP phai co rao chan bang bien tinh tu ket qua do duoc
//
// GIOI HAN, noi luon: day la kiem tra tren MA NGUON, khong phai chay thu bo cham.
// No khong biet ket qua co dung khong; no chi biet ma co CHO cho ket qua that di
// vao khong. Ba trang thai that (dat · sai · khong do duoc) van phai bam tay.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

// 30/08/2026 — bọc qua bocChuThich(). Gieo thử chứng minh cửa này TỪNG bị
// lừa: xoá dòng mã thật và để lại một chú thích mang đúng chữ cửa tìm thì nó
// VẪN XANH. 5/6 cửa dò chuỗi dính bệnh này; cái duy nhất thoát là cái CHẠY mã.
// Xem tools/boc_chu_thich.js.
const { bocChuThich } = require('../tools/boc_chu_thich.js');

const APP_JS = bocChuThich(fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js'), 'utf8'));

// Than ham lay bang DEM NGOAC tu ten ham, khong neo bang indexOf mot doan —
// hai lan truoc neo kieu do deu truot khi ma doi (xem test_chan_mat_du_lieu.js).
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

const HAM = 'chamDiemBaiTap';
// Nhan dien loi GOI ra ngoai, khong nhan dien ten ham cu the: app.js goi qua
// authFetch() (co them X-Auth-Token). Cua ban dau kiem includes('fetch') nen
// KHONG nhan ra authFetch — do gia, ma do gia thi nguoi ta tat cua.
const RE_GOI = /\b(?:auth)?[Ff]etch\(/;
const CONG_CHAY_MA = '/api/chay';

function daNoiCong(than) {
  return than.includes(CONG_CHAY_MA) && RE_GOI.test(than);
}

const CHU_PHAN_QUYET = ['✓ PASS', 'HOÀN THÀNH 100%', 'XUẤT SẮC', 'VƯỢT QUA THỬ THÁCH'];

// --- the gioi 1: CHUA noi cong -> cam tuyen bo -------------------------------
test('chua noi cong chay ma thi khong duoc tuyen bo gi', () => {
  const than = thanHam(HAM);
  if (daNoiCong(than)) return;          // the gioi 2, do o cac khang dinh duoi
  for (const chu of CHU_PHAN_QUYET) {
    assert.ok(!than.includes(chu),
      HAM + ' in phan quyet "' + chu + '" nhung khong goi cong chay ma that');
  }
  assert.ok(!than.includes('danhDauBaiDaGiai('),
    HAM + ' cong XP trong khi khong do duoc gi');
  assert.ok(than.includes('CHƯA CHẤM ĐƯỢC'),
    HAM + ' khong do duoc nhung cung khong noi ra trang thai do');
});

// --- the gioi 2: DA noi cong ------------------------------------------------
test('bo cham khong duoc TU GIAI bai bang cach nhin c.id', () => {
  const than = thanHam(HAM);
  assert.ok(!/\bc\.id\s*===/.test(than),
    HAM + ' lai re nhanh theo c.id — day dung la cach no tung tu viet loi giai ' +
    'bang JS roi cham chinh minh');
});

test('ket qua phai den tu phan hoi cua lan chay, khong tu tinh trong JS', () => {
  const than = thanHam(HAM);
  if (!daNoiCong(than)) return;
  assert.ok(than.includes('res.stdout'),
    HAM + ' khong doc res.stdout — vay cot "Thuc Te" lay tu dau ra?');
  assert.ok(/__AURA_DO__/.test(than),
    HAM + ' khong con dau doc ket qua tung truong hop tu dau ra cua lan chay');
});

test('cong XP phai co rao chan bang bien tinh tu ket qua do duoc', () => {
  const than = thanHam(HAM);
  const soLan = (than.match(/danhDauBaiDaGiai\(/g) || []).length;
  assert.strictEqual(soLan, 1,
    'phai co dung 1 cho cong XP trong ' + HAM + ', dang co ' + soLan);

  // Rao chan phai duoc TINH tu so truong hop do duoc va so truong hop dat,
  // va phai nam TRUOC cho cong XP.
  const viTriRao = than.indexOf('const datHet =');
  const viTriCong = than.indexOf('danhDauBaiDaGiai(');
  assert.ok(viTriRao !== -1, HAM + ' khong con bien datHet — rao chan da bien mat');
  assert.ok(viTriRao < viTriCong, 'rao chan datHet phai duoc tinh TRUOC khi cong XP');

  const dongRao = than.slice(viTriRao, than.indexOf(';', viTriRao));
  assert.ok(/doHet/.test(dongRao) && /soDat/.test(dongRao),
    'datHet phai tinh tu ca doHet (do duoc het chua) lan soDat (dat may cai) — ' +
    'dang la: ' + dongRao.trim());
  assert.ok(/if \(datHet\)/.test(than),
    'cho cong XP phai nam trong nhanh if (datHet)');
});

test('qua gio KHONG duoc bien thanh phan quyet "sai"', () => {
  const than = thanHam(HAM);
  if (!daNoiCong(than)) return;
  // 12/08 da tra gia mot lan: nhan timeout doc y het mot ket luan ve hanh vi.
  assert.ok(than.includes('res.timed_out'),
    HAM + ' khong xet res.timed_out — qua gio se bi doc nham thanh bai lam sai');
  // Neo theo LOI GOI ke tiep, khong dem ky tu: ba chuoi tieng Viet o giua dai
  // hon moi cua so em dat tay, va mot con so dat tay thi lan sau lai sai.
  const k = than.indexOf('res.timed_out');
  const g = than.indexOf('veTheTestCase(', k);
  assert.ok(g !== -1, 'sau nhanh qua gio khong con lenh ve the ket qua nao');
  const loiGoi = than.slice(g, than.indexOf(');', g) + 2);
  assert.ok(loiGoi.includes("'chua_do'"),
    'nhanh qua gio phai ve trang thai chua_do (KHONG DO DUOC), khong phai truot — ' +
    'dang goi: ' + loiGoi.replace(/\s+/g, ' ').slice(0, 140));
});

test('ba trang thai phai con du, khong duoc gop lai thanh hai', () => {
  const than = thanHam(HAM) + thanHam('veTheTestCase');
  for (const tt of ['dat', 'truot', 'chua_do']) {
    assert.ok(than.includes(tt),
      'mat trang thai "' + tt + '" — ba trang thai dat/truot/khong-do-duoc phai tach roi');
  }
});
