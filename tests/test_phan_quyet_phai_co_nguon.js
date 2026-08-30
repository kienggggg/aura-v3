// tests/test_phan_quyet_phai_co_nguon.js
//
// 30/08/2026. Trong MOT commit viet moi (18711f5, +6.698 dong), 5 tinh nang that
// va 3 gia. Chia doi khong theo "viet moi hay sua lai" — ca 8 deu viet moi. No
// chia theo viec ma phai LAM RA MOT VAT hay phai NOI RA MOT PHAN QUYET:
//
//   lam ra vat (Logo, Flowchart, Packager, Workflow Hub, Bang ve)  -> that ca 5
//   noi ra phan quyet (AI Doctor, sao/luot tai Extension, Grader)  -> gia ca 3
//
// Vat tu no chung minh: zip mo duoc hoac khong, SVG hien hoac khong. Phan quyet
// thi khong co gi buoc no phai dung — viet actualVal = 6 chay tron tru y het viet
// ma cham that, va nhin con gon hon.
//
// Cua nay giu mot bat bien theo loi DANH SACH DONG (giong tests/test_v3_ranh_gioi.py):
// moi cho trong app.js in ra chu phan quyet PHAI co ten trong bang duoi, kem NGUON
// DO sinh ra phan quyet do. Them mot phan quyet moi ma khong khai nguon -> DO.
// Khai roi ma nguon bien mat khoi ham -> DO. Khai roi ma chu bien mat -> DO (bang
// phai luon dung, khong duoc de lai muc chet).
//
// GIOI HAN, noi luon:
//  - Cua boc chu thich CA DONG va khoi block truoc khi quet. Chu thich cuoi dong
//    (sau ma) thi KHONG boc — huong sai an toan: no gay DO gia chu khong gay XANH
//    gia. Da tung dinh bay nay: khop mot chu thich chua chu returnValue.
//  - Cua boc noi dung style="..." vi width: 100% khong phai phan quyet.
//  - Ham bao quanh lay tu khai bao function gan nhat bao trum vi tri do. Phan quyet
//    nam trong arrow function long ben trong se quy ve ham co ten do — the la du.
//
// CHO MU, DA DO chu khong phai doan. Gieo 5 loi khen gia dung chu NGOAI danh sach
// CUM_PHAN_QUYET vao mot ham khong khai bao, cua XANH ca 5:
//     "🎉 Tuyệt vời, bạn đã làm đúng rồi!"          khong bat
//     "Bài của bạn CHÍNH XÁC 4 trên 4 trường hợp."  khong bat
//     "Mã nguồn của bạn sạch, không có vấn đề gì."   khong bat
//     "Điểm: 10/10"                                  khong bat
//     "✓ ĐÚNG"                                       khong bat
// Noi ro de khoi ai tuong co cua nay la het lo: day la CAI CHOT chong tai pham ba
// loi da bat duoc (sao/luot tai, PASS gia, HEALTHY gia), KHONG phai hang rao kin.
// Khong noi rong danh sach ra "dung/sach/chinh xac/diem" vi nhung chu ay xuat hien
// khap noi trong app -> se DO gia lien tuc roi bi tat, ma cua bi tat thi bang khong.
// Cach bat cai lot: van la nguoi tu bam thu, nhu CLAUDE.md muc 4 da ghi.
//  - Cua nay KHONG biet mot con so co dung hay khong. No chi hoi: co nguon nao de
//    ma sinh ra con so ay khong. Do la cau hoi may tra loi duoc; cau kia thi khong.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const DUONG = path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'app.js');
const GOC = fs.readFileSync(DUONG, 'utf8');

// --- cac cum tu la LOI KHANG DINH ve bai lam / suc khoe ma / chat luong goi -----
const CUM_PHAN_QUYET = [
  'PASS', 'FAIL', 'HEALTHY', 'XUẤT SẮC', 'VƯỢT QUA',
  'HOÀN THÀNH 100', '★', 'AN TOÀN', 'Hợp lệ',
];

// --- BANG KHAI BAO: cho nao duoc in phan quyet, va lay so tu dau --------------
// Them dong vao day phai la viec CO Y, co nguoi thay, va giai thich duoc.
const DUOC_PHEP = [
  {
    ham: 'runProgram',
    cum: 'PASS',
    nguon: '/api/chay',
    vi_sao: 'PASS lay tu res.status cua authFetch(/api/chay) — tien trinh Python that o backend',
  },
  {
    ham: 'chayKhamBenhVaHienThi',
    cum: 'HEALTHY',
    nguon: 'state.diagnostics',
    vi_sao: 'doc so_loi_do va so_canh_bao_vang cua bo kiem tra tinh; 26/08 tung in "100% HEALTHY" khi bo do bao 2 loi',
  },
  {
    ham: 'updateStatusBar',
    cum: 'Hợp lệ',
    nguon: 'state.diagnostics',
    vi_sao: 'thanh trang thai dem thang tu danh sach chan doan, khong tu ket luan lay',
  },
];

// ---------------------------------------------------------------------------
function bocChuThichVaStyle(s) {
  let r = s.replace(/\/\*[\s\S]*?\*\//g, ' ');
  r = r.split('\n').map(d => (/^\s*\/\//.test(d) ? '' : d)).join('\n');
  r = r.replace(/style="[^"]*"/g, 'style=""');
  return r;
}

function hamBaoQuanh(s, viTri) {
  let ten = '<ngoai moi ham>';
  const re = /\bfunction\s+([A-Za-z_$][\w$]*)\s*\(/g;
  let m;
  while ((m = re.exec(s)) !== null) {
    if (m.index > viTri) break;
    const mo = s.indexOf('{', m.index);
    if (mo === -1) continue;
    let sau = 1, k = mo + 1;
    while (sau > 0 && k < s.length) {
      const c = s[k];
      if (c === '{') sau += 1;
      else if (c === '}') sau -= 1;
      k += 1;
    }
    if (viTri >= mo && viTri < k) ten = m[1];
  }
  return ten;
}

function timTatCa() {
  const s = bocChuThichVaStyle(GOC);
  const ra = [];
  for (const cum of CUM_PHAN_QUYET) {
    let i = s.indexOf(cum);
    while (i !== -1) {
      ra.push({ cum, ham: hamBaoQuanh(s, i), viTri: i });
      i = s.indexOf(cum, i + cum.length);
    }
  }
  return ra;
}

function thanCuaHam(ten) {
  const i = GOC.indexOf('function ' + ten + '(');
  if (i === -1) return null;
  const mo = GOC.indexOf('{', i);
  let sau = 1, k = mo + 1;
  while (sau > 0 && k < GOC.length) {
    const c = GOC[k];
    if (c === '{') sau += 1;
    else if (c === '}') sau -= 1;
    k += 1;
  }
  return GOC.slice(i, k);
}

// ---------------------------------------------------------------------------
test('moi chu phan quyet trong app.js deu phai co ten trong bang khai bao', () => {
  const la = [];
  for (const t of timTatCa()) {
    if (!DUOC_PHEP.some(d => d.ham === t.ham && d.cum === t.cum)) {
      la.push(t.ham + ' in "' + t.cum + '"');
    }
  }
  assert.deepStrictEqual([...new Set(la)], [],
    'co cho in phan quyet ma khong khai nguon do trong DUOC_PHEP — ' +
    'them vao bang PHAI kem nguon that, dung them cho het do');
});

test('nguon do da khai phai con nam trong chinh ham do', () => {
  for (const d of DUOC_PHEP) {
    const than = thanCuaHam(d.ham);
    assert.ok(than !== null, 'khong con ham ' + d.ham + ' — bang khai bao da cu');
    assert.ok(than.includes(d.nguon),
      d.ham + ' van in "' + d.cum + '" nhung nguon do "' + d.nguon + '" da bien mat khoi ham');
  }
});

test('bang khai bao khong duoc de lai muc chet', () => {
  const thay = timTatCa();
  for (const d of DUOC_PHEP) {
    assert.ok(thay.some(t => t.ham === d.ham && t.cum === d.cum),
      'muc chet trong DUOC_PHEP: ' + d.ham + ' khong con in "' + d.cum + '" nua — xoa dong do di');
  }
});

test('moi muc khai bao phai ghi VI SAO, khong duoc de trong', () => {
  for (const d of DUOC_PHEP) {
    assert.ok(typeof d.vi_sao === 'string' && d.vi_sao.trim().length >= 20,
      'muc ' + d.ham + ' thieu loi giai thich — bang nay de nguoi sau doc, khong phai de qua cua');
  }
});

test('bo boc chu thich khong duoc an mat ma that', () => {
  const thu = ['  // PASS gia trong chu thich', "  x.textContent = 'PASS';"].join('\n');
  const sau = bocChuThichVaStyle(thu);
  assert.ok(!sau.includes('// PASS'), 'chu thich ca dong phai bi boc');
  assert.ok(sau.includes("'PASS'"), 'dong MA that khong duoc boc mat');
});
