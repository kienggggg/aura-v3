/**
 * test_hop_dong_api.js — cửa cứng cho đường dẫn và tên trường giữa JS/Python.
 *
 * VÌ SAO CÓ CỬA NÀY, 26/08/2026:
 *
 * Hai lỗi giao diện đã cùng im lặng: JS từng đọc `data.tep_tin` trong khi
 * Python trả `danh_sach`, rồi ô chọn test gọi một thư mục `tests/` không tồn
 * tại ở mọi dự án. Trước cửa này, 12 lời gọi authFetch (9 đường phân biệt)
 * không có phép đối chiếu tự động với 10 đường `/api/` Python đăng ký.
 *
 * Cửa chỉ đỏ ở chiều chắc chắn hỏng lúc chạy: JS gọi đường Python không có.
 * Chiều Python chưa được giao diện gọi chỉ được in cảnh báo vì `/api/nhip`
 * hiện dành cho khách khác. Không biến API hợp lệ nhưng không thuộc app.js
 * thành hồi quy giả.
 *
 * VÌ SAO THÊM TÊN TRƯỜNG, 27/08/2026:
 *
 * Hai lệch schema đã im lặng tới lúc bấm app: `tep_tin`/`danh_sach`, rồi
 * `.filter()` trên diagnostics dạng object. Grep `data.x` thử ngày 26/08 ra
 * 13 tên nhưng lẫn `e`, `d`, `nguon` của biến khác. Cửa này vì thế nối binding
 * thật; trên cây hiện tại là 11 response, 16 lần nhận JSON, 29 cặp đường-trường.
 *
 * Ba biến AURA_HOP_DONG_APP_JS / AURA_HOP_DONG_THE_APP_PY /
 * AURA_HOP_DONG_THE_API_PY cho phép trỏ cửa vào bản mutant tạm. Nhờ vậy có
 * thể chứng minh lỗi gieo đỏ mà không sửa mã thật trong lúc một phép đo khác
 * đang dùng kho.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const GOC = path.resolve(__dirname, '..');
const TEP_JS = path.resolve(
  process.env.AURA_HOP_DONG_APP_JS || path.join(GOC, 'interface', 'web', 'the_v1', 'app.js')
);
const TEP_PY = path.resolve(
  process.env.AURA_HOP_DONG_THE_APP_PY || path.join(GOC, 'interface', 'the_app.py')
);
const TEP_API_PY = path.resolve(
  process.env.AURA_HOP_DONG_THE_API_PY || path.join(GOC, 'interface', 'the_api.py')
);
const PYTHON = path.join(GOC, 'venv', 'Scripts', 'python.exe');

function boQuaKhoangTrangVaChuThich(ma, viTri) {
  let i = viTri;
  while (i < ma.length) {
    if (/\s/.test(ma[i])) {
      i += 1;
      continue;
    }
    if (ma.startsWith('//', i)) {
      const hetDong = ma.indexOf('\n', i + 2);
      i = hetDong === -1 ? ma.length : hetDong + 1;
      continue;
    }
    if (ma.startsWith('/*', i)) {
      const dong = ma.indexOf('*/', i + 2);
      assert.notStrictEqual(dong, -1, `Chú thích JS mở ở offset ${i} nhưng không đóng`);
      i = dong + 2;
      continue;
    }
    break;
  }
  return i;
}

function docChuoiLiteral(ma, viTri) {
  const dau = ma[viTri];
  assert.ok(dau === "'" || dau === '"' || dau === '`');
  if (dau === '`') return docTemplateLiteral(ma, viTri);
  let noiDung = '';
  let i = viTri + 1;
  while (i < ma.length) {
    const c = ma[i];
    if (c === '\\') {
      assert.ok(i + 1 < ma.length, `Escape JS cụt ở offset ${i}`);
      noiDung += c + ma[i + 1];
      i += 2;
      continue;
    }
    if (c === dau) {
      return { noiDung, ketThuc: i + 1 };
    }
    noiDung += c;
    i += 1;
  }
  assert.fail(`Chuỗi JS mở ở offset ${viTri} nhưng không đóng`);
}

function docTemplateLiteral(ma, viTri) {
  let i = viTri + 1;
  while (i < ma.length) {
    if (ma[i] === '\\') {
      i += 2;
      continue;
    }
    if (ma[i] === '`') {
      return { noiDung: ma.slice(viTri + 1, i), ketThuc: i + 1 };
    }
    if (ma.startsWith('${', i)) {
      i = boQuaBieuThucTemplate(ma, i + 2);
      continue;
    }
    i += 1;
  }
  assert.fail(`Template JS mở ở offset ${viTri} nhưng không đóng`);
}

function soDong(ma, viTri) {
  return ma.slice(0, viTri).split('\n').length;
}

function coTheBatDauRegex(tokenTruoc) {
  if (!tokenTruoc) return true;
  if (tokenTruoc.loai === 'dau') {
    return /[({[=,:;!?&|+*%~<>]/.test(tokenTruoc.giaTri);
  }
  return tokenTruoc.loai === 'identifier' &&
    /^(?:return|case|throw|typeof|delete|void|new|in|of|yield|await)$/.test(tokenTruoc.giaTri);
}

function boQuaRegexLiteral(ma, viTri) {
  let i = viTri + 1;
  let trongLopKyTu = false;
  while (i < ma.length) {
    if (ma[i] === '\\') {
      i += 2;
      continue;
    }
    if (ma[i] === '[') trongLopKyTu = true;
    else if (ma[i] === ']') trongLopKyTu = false;
    else if (ma[i] === '/' && !trongLopKyTu) {
      i += 1;
      while (i < ma.length && /[A-Za-z]/.test(ma[i])) i += 1;
      return i;
    } else if (ma[i] === '\n' || ma[i] === '\r') {
      assert.fail(`Regex JS mở ở dòng ${soDong(ma, viTri)} nhưng không đóng`);
    }
    i += 1;
  }
  assert.fail(`Regex JS mở ở dòng ${soDong(ma, viTri)} nhưng không đóng`);
}

function boQuaBieuThucTemplate(ma, viTri) {
  let sau = 1;
  let tokenTruoc = null;
  let i = viTri;
  while (i < ma.length) {
    const moi = boQuaKhoangTrangVaChuThich(ma, i);
    if (moi !== i) {
      i = moi;
      continue;
    }
    if (ma[i] === "'" || ma[i] === '"' || ma[i] === '`') {
      i = docChuoiLiteral(ma, i).ketThuc;
      tokenTruoc = { loai: 'literal' };
      continue;
    }
    if (ma[i] === '/' && coTheBatDauRegex(tokenTruoc)) {
      i = boQuaRegexLiteral(ma, i);
      tokenTruoc = { loai: 'literal' };
      continue;
    }
    if (/[A-Za-z_$]/.test(ma[i])) {
      const batDau = i;
      i += 1;
      while (i < ma.length && /[A-Za-z0-9_$]/.test(ma[i])) i += 1;
      tokenTruoc = { loai: 'identifier', giaTri: ma.slice(batDau, i) };
      continue;
    }
    if (ma[i] === '{') sau += 1;
    if (ma[i] === '}') {
      sau -= 1;
      if (sau === 0) return i + 1;
    }
    tokenTruoc = { loai: 'dau', giaTri: ma[i] };
    i += 1;
  }
  assert.fail(`Biểu thức \${...} mở ở offset ${viTri - 2} nhưng không đóng`);
}

/**
 * Quét token vừa đủ cho hợp đồng này, thay vì grep chữ `authFetch` thô.
 * Chỉ một identifier ở ngoài chú thích/chuỗi, theo sau bởi `(` và một literal
 * mới được tính là lời gọi. Khai báo `function authFetch(url, ...)` bị loại.
 */
function rutLoiGoiAuthFetch(ma) {
  const loiGoi = [];
  const khongPhaiLiteral = [];
  let tokenTruoc = null;
  let i = 0;

  while (i < ma.length) {
    const moi = boQuaKhoangTrangVaChuThich(ma, i);
    if (moi !== i) {
      i = moi;
      continue;
    }

    if (ma[i] === "'" || ma[i] === '"' || ma[i] === '`') {
      i = docChuoiLiteral(ma, i).ketThuc;
      tokenTruoc = { loai: 'literal' };
      continue;
    }

    if (ma[i] === '/' && coTheBatDauRegex(tokenTruoc)) {
      i = boQuaRegexLiteral(ma, i);
      tokenTruoc = { loai: 'literal' };
      continue;
    }

    if (/[A-Za-z_$]/.test(ma[i])) {
      const batDau = i;
      i += 1;
      while (i < ma.length && /[A-Za-z0-9_$]/.test(ma[i])) i += 1;
      const ten = ma.slice(batDau, i);

      if (ten === 'authFetch' && !(tokenTruoc && tokenTruoc.giaTri === 'function')) {
        const moNgoac = boQuaKhoangTrangVaChuThich(ma, i);
        if (ma[moNgoac] === '(') {
          const doiSo = boQuaKhoangTrangVaChuThich(ma, moNgoac + 1);
          if (ma[doiSo] === "'" || ma[doiSo] === '"' || ma[doiSo] === '`') {
            const literal = docChuoiLiteral(ma, doiSo);
            const moc = [literal.noiDung.indexOf('?'), literal.noiDung.indexOf('#')]
              .filter((x) => x >= 0);
            const ketThucDuong = moc.length ? Math.min(...moc) : literal.noiDung.length;
            const duong = literal.noiDung.slice(0, ketThucDuong);
            const noiSuy = duong.indexOf('${');
            if (noiSuy >= 0 || duong.includes('\\')) {
              khongPhaiLiteral.push({ dong: soDong(ma, batDau), doiSo: literal.noiDung });
            } else {
              loiGoi.push({
                duong,
                dong: soDong(ma, batDau),
                batDauLoiGoi: batDau,
                batDauDuong: doiSo + 1,
              });
            }
          } else {
            khongPhaiLiteral.push({ dong: soDong(ma, batDau), doiSo: '<biểu thức động>' });
          }
        }
      }

      tokenTruoc = { loai: 'identifier', giaTri: ten };
      continue;
    }

    tokenTruoc = { loai: 'dau', giaTri: ma[i] };
    i += 1;
  }

  return { loiGoi, khongPhaiLiteral };
}

function taoHamSoDong(ma) {
  const dauDong = [0];
  for (let i = 0; i < ma.length; i += 1) {
    if (ma[i] === '\n') dauDong.push(i + 1);
  }
  return (viTri) => {
    let trai = 0;
    let phai = dauDong.length;
    while (trai + 1 < phai) {
      const giua = Math.floor((trai + phai) / 2);
      if (dauDong[giua] <= viTri) trai = giua;
      else phai = giua;
    }
    return trai + 1;
  };
}

/**
 * Tokenizer nhỏ, chỉ phục vụ phép nối binding -> trường JSON. Nó không dò
 * `data.x` bằng regex: chú thích, chuỗi và regex đều bị bỏ khỏi mã thực thi.
 * Riêng `${...}` được token hóa đệ quy vì trường API thật có thể nằm trong
 * nội suy (hiện `/api/trace` và `/api/chay` đều có).
 */
function tokenHoaJs(ma) {
  const tokens = [];
  const dongTai = taoHamSoDong(ma);
  const toanTu = [
    '>>>=', '===', '!==', '>>>', '**=', '&&=', '||=', '??=', '...', '=>',
    '?.', '==', '!=', '<=', '>=', '++', '--', '+=', '-=', '*=', '/=', '%=',
    '&&', '||', '??', '**', '<<', '>>', '&=', '|=', '^=', '?.',
  ];

  function them(loai, giaTri, batDau, ketThuc, themThuocTinh = {}) {
    tokens.push({ loai, giaTri, batDau, ketThuc, dong: dongTai(batDau), ...themThuocTinh });
  }

  function quetNoiSuyTemplate(batDau, ketThuc) {
    let i = batDau + 1;
    while (i < ketThuc - 1) {
      if (ma[i] === '\\') {
        i += 2;
        continue;
      }
      if (ma.startsWith('${', i)) {
        const sauDong = boQuaBieuThucTemplate(ma, i + 2);
        assert.ok(sauDong <= ketThuc, `Nội suy template vượt chuỗi ở dòng ${dongTai(i)}`);
        // Cặp ngoặc ảo giữ dấu phẩy trong `${a, b}` ở đúng scope khi quét
        // khai báo; chúng không đại diện cho một block JS thật.
        them('dau', '{', i + 1, i + 2, { aoTemplate: true });
        quet(i + 2, sauDong - 1);
        them('dau', '}', sauDong - 1, sauDong, { aoTemplate: true });
        i = sauDong;
        continue;
      }
      i += 1;
    }
  }

  function quet(batDau, ketThuc) {
    let i = batDau;
    let tokenTruoc = null;
    while (i < ketThuc) {
      const moi = boQuaKhoangTrangVaChuThich(ma, i);
      if (moi !== i) {
        i = Math.min(moi, ketThuc);
        continue;
      }

      if (ma[i] === "'" || ma[i] === '"' || ma[i] === '`') {
        const literal = docChuoiLiteral(ma, i);
        assert.ok(literal.ketThuc <= ketThuc, `Chuỗi JS vượt phạm vi ở dòng ${dongTai(i)}`);
        them('literal', literal.noiDung, i, literal.ketThuc, { dauChuoi: ma[i] });
        if (ma[i] === '`') quetNoiSuyTemplate(i, literal.ketThuc);
        i = literal.ketThuc;
        tokenTruoc = { loai: 'literal' };
        continue;
      }

      if (ma[i] === '/' && coTheBatDauRegex(tokenTruoc)) {
        const sauRegex = boQuaRegexLiteral(ma, i);
        assert.ok(sauRegex <= ketThuc, `Regex JS vượt phạm vi ở dòng ${dongTai(i)}`);
        them('literal', '<regex>', i, sauRegex, { regex: true });
        i = sauRegex;
        tokenTruoc = { loai: 'literal' };
        continue;
      }

      if (/[A-Za-z_$]/.test(ma[i])) {
        const dau = i;
        i += 1;
        while (i < ketThuc && /[A-Za-z0-9_$]/.test(ma[i])) i += 1;
        const ten = ma.slice(dau, i);
        them('identifier', ten, dau, i);
        tokenTruoc = { loai: 'identifier', giaTri: ten };
        continue;
      }

      if (/[0-9]/.test(ma[i])) {
        const dau = i;
        i += 1;
        while (i < ketThuc && /[A-Za-z0-9_.]/.test(ma[i])) i += 1;
        them('number', ma.slice(dau, i), dau, i);
        tokenTruoc = { loai: 'literal' };
        continue;
      }

      const op = toanTu.find((x) => ma.startsWith(x, i));
      if (op) {
        them('dau', op, i, i + op.length);
        i += op.length;
        tokenTruoc = { loai: 'dau', giaTri: op };
        continue;
      }

      them('dau', ma[i], i, i + 1);
      tokenTruoc = { loai: 'dau', giaTri: ma[i] };
      i += 1;
    }
  }

  quet(0, ma.length);
  return tokens;
}

function lapCauTrucScope(tokens) {
  const moSangDong = new Map();
  const dongSangMo = new Map();
  const nganXepNgoac = [];
  const dongCua = { '(': ')', '[': ']', '{': '}' };
  const moCua = { ')': '(', ']': '[', '}': '{' };

  for (let i = 0; i < tokens.length; i += 1) {
    const dau = tokens[i].giaTri;
    if (tokens[i].loai !== 'dau') continue;
    if (Object.hasOwn(dongCua, dau)) {
      nganXepNgoac.push({ dau, i });
    } else if (Object.hasOwn(moCua, dau)) {
      const mo = nganXepNgoac.pop();
      assert.ok(
        mo && mo.dau === moCua[dau],
        `Ngoặc JS lệch ở dòng ${tokens[i].dong}: gặp ${dau}, ` +
          `đỉnh là ${mo ? `${mo.dau} dòng ${tokens[mo.i].dong}` : '<rỗng>'}; ` +
          `tokens=${tokens.slice(Math.max(0, i - 12), i + 1).map((x) => `${x.giaTri}@${x.dong}`).join(' ')}`
      );
      moSangDong.set(mo.i, i);
      dongSangMo.set(i, mo.i);
    }
  }
  assert.deepStrictEqual(
    nganXepNgoac,
    [],
    'Mã JS còn ngoặc chưa đóng: ' + nganXepNgoac.map((x) => tokens[x.i].dong).join(', ')
  );

  const blocks = [{ id: 0, batDau: -1, ketThuc: tokens.length, cha: null, doSau: 0 }];
  const blockTheoToken = new Array(tokens.length).fill(0);
  const blockTheoNgoacMo = new Map();
  const nganXepBlock = [0];
  for (let i = 0; i < tokens.length; i += 1) {
    const dau = tokens[i].giaTri;
    if (tokens[i].loai === 'dau' && dau === '{') {
      blockTheoToken[i] = nganXepBlock[nganXepBlock.length - 1];
      const cha = nganXepBlock[nganXepBlock.length - 1];
      const block = {
        id: blocks.length,
        batDau: i,
        ketThuc: moSangDong.get(i),
        cha,
        doSau: blocks[cha].doSau + 1,
      };
      assert.notStrictEqual(block.ketThuc, undefined, `Block mở dòng ${tokens[i].dong} không đóng`);
      blocks.push(block);
      blockTheoNgoacMo.set(i, block.id);
      nganXepBlock.push(block.id);
    } else if (tokens[i].loai === 'dau' && dau === '}') {
      blockTheoToken[i] = nganXepBlock[nganXepBlock.length - 1];
      const blockId = nganXepBlock.pop();
      assert.strictEqual(blocks[blockId].ketThuc, i, `Cây block lệch ở dòng ${tokens[i].dong}`);
    } else {
      blockTheoToken[i] = nganXepBlock[nganXepBlock.length - 1];
    }
  }
  assert.deepStrictEqual(nganXepBlock, [0], 'Cây block JS không trở về gốc');

  return { moSangDong, dongSangMo, blocks, blockTheoToken, blockTheoNgoacMo };
}

function rutPhamViHam(tokens, cauTruc) {
  const ham = [];
  const { moSangDong, dongSangMo } = cauTruc;

  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai === 'identifier' && tokens[i].giaTri === 'function') {
      let j = i + 1;
      if (tokens[j] && tokens[j].giaTri === '*') j += 1;
      let ten = '<hàm ẩn danh>';
      if (tokens[j] && tokens[j].loai === 'identifier') {
        ten = tokens[j].giaTri;
        j += 1;
      }
      if (!tokens[j] || tokens[j].giaTri !== '(') continue;
      const dongThamSo = moSangDong.get(j);
      const moThan = dongThamSo + 1;
      if (!tokens[moThan] || tokens[moThan].giaTri !== '{') continue;
      ham.push({
        ten,
        batDau: moThan,
        ketThuc: moSangDong.get(moThan),
        moThamSo: j,
        dongThamSo,
      });
    }

    if (tokens[i].loai === 'dau' && tokens[i].giaTri === '=>') {
      let moThamSo = null;
      let dongThamSo = null;
      if (tokens[i - 1] && tokens[i - 1].giaTri === ')') {
        dongThamSo = i - 1;
        moThamSo = dongSangMo.get(dongThamSo);
      }
      const than = i + 1;
      if (!tokens[than]) continue;
      if (tokens[than].giaTri === '{') {
        ham.push({
          ten: '<hàm mũi tên>',
          batDau: than,
          ketThuc: moSangDong.get(than),
          moThamSo,
          dongThamSo,
          thamSoDon: moThamSo === null && tokens[i - 1]?.loai === 'identifier' ? i - 1 : null,
        });
      } else {
        let ketThuc = than;
        while (ketThuc < tokens.length) {
          const dau = tokens[ketThuc].giaTri;
          if (tokens[ketThuc].loai === 'dau' && (dau === '(' || dau === '[' || dau === '{')) {
            ketThuc = moSangDong.get(ketThuc) + 1;
            continue;
          }
          if (tokens[ketThuc].loai === 'dau' &&
              (dau === ',' || dau === ';' || dau === ')' || dau === ']' || dau === '}')) break;
          ketThuc += 1;
        }
        ham.push({
          ten: '<hàm mũi tên>',
          batDau: than - 1,
          ketThuc,
          moThamSo,
          dongThamSo,
          thamSoDon: moThamSo === null && tokens[i - 1]?.loai === 'identifier' ? i - 1 : null,
        });
      }
    }
  }

  return ham.filter((x) => Number.isInteger(x.ketThuc));
}

function taoBangBinding(tokens, cauTruc, cacHam) {
  const bindings = [];
  const { blocks, blockTheoToken, blockTheoNgoacMo, moSangDong } = cauTruc;

  function hamTai(chiSo) {
    return cacHam
      .filter((x) => x.batDau < chiSo && chiSo < x.ketThuc)
      .sort((a, b) => (a.ketThuc - a.batDau) - (b.ketThuc - b.batDau))[0] || null;
  }

  function them(ten, chiSoKhaiBao, phamVi, loai, thayCaPhamVi = false, baoThu = false) {
    if (!ten) return;
    bindings.push({
      ten,
      chiSoKhaiBao,
      batDauPhamVi: phamVi.batDau,
      ketThucPhamVi: phamVi.ketThuc,
      loai,
      thayCaPhamVi,
      baoThu,
    });
  }

  function themPattern(batDau, ketThuc, phamVi, loai, thayCaPhamVi) {
    if (batDau === null || batDau === undefined || batDau >= ketThuc) return;
    if (tokens[batDau].loai === 'identifier') {
      them(tokens[batDau].giaTri, batDau, phamVi, loai, thayCaPhamVi);
      return;
    }
    // Destructuring không xuất hiện ở binding API hiện tại. Ghi bảo thủ mọi
    // identifier làm binding; nếu nó che một biến JSON, cửa sẽ báo không thể
    // chứng minh thay vì gán nhầm trường của biến ngoài.
    for (let i = batDau; i < ketThuc; i += 1) {
      if (tokens[i].loai === 'identifier') {
        them(tokens[i].giaTri, i, phamVi, loai, thayCaPhamVi, true);
      }
    }
  }

  // const/let/var: lấy mọi declarator đơn; phần initializer được nhảy qua bằng
  // cặp ngoặc nên dấu phẩy trong object/call không bị coi là declarator mới.
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai !== 'identifier' || !['const', 'let', 'var'].includes(tokens[i].giaTri)) continue;
    const loai = tokens[i].giaTri;
    let j = i + 1;
    while (j < tokens.length) {
      const block = blocks[blockTheoToken[j]];
      const hamHienTai = hamTai(j);
      const phamVi = loai === 'var' && hamHienTai ? hamHienTai : block;
      if (tokens[j].loai === 'identifier') {
        them(tokens[j].giaTri, j, phamVi, loai, loai === 'var');
        j += 1;
      } else if (tokens[j].loai === 'dau' && (tokens[j].giaTri === '{' || tokens[j].giaTri === '[')) {
        const dong = moSangDong.get(j);
        themPattern(j + 1, dong, phamVi, loai, loai === 'var');
        j = dong + 1;
      } else {
        break;
      }

      let coDeclaratorSau = false;
      while (j < tokens.length) {
        const dau = tokens[j].giaTri;
        if (tokens[j].loai === 'dau' && (dau === '(' || dau === '[' || dau === '{')) {
          j = moSangDong.get(j) + 1;
          continue;
        }
        if (tokens[j].loai === 'dau' && dau === ',') {
          j += 1;
          coDeclaratorSau = true;
          break;
        }
        if ((tokens[j].loai === 'dau' && (dau === ';' || dau === ')' || dau === '}')) ||
            (tokens[j].loai === 'identifier' && (dau === 'of' || dau === 'in'))) break;
        j += 1;
      }
      if (!coDeclaratorSau) break;
    }
  }

  // Tham số function/arrow là binding của thân hàm, kể cả trước vị trí chữ.
  for (const h of cacHam) {
    if (h.thamSoDon !== null && h.thamSoDon !== undefined) {
      themPattern(h.thamSoDon, h.thamSoDon + 1, h, 'tham_số', true);
    } else if (h.moThamSo !== null && h.moThamSo !== undefined) {
      let dauDoan = h.moThamSo + 1;
      for (let i = dauDoan; i <= h.dongThamSo; i += 1) {
        const laCuoi = i === h.dongThamSo;
        if (!laCuoi && tokens[i].loai === 'dau' &&
            (tokens[i].giaTri === '(' || tokens[i].giaTri === '[' || tokens[i].giaTri === '{')) {
          i = moSangDong.get(i);
          continue;
        }
        if (laCuoi || (tokens[i].loai === 'dau' && tokens[i].giaTri === ',')) {
          let ket = i;
          for (let k = dauDoan; k < i; k += 1) {
            if (tokens[k].giaTri === '=') {
              ket = k;
              break;
            }
          }
          themPattern(dauDoan, ket, h, 'tham_số', true);
          dauDoan = i + 1;
        }
      }
    }
  }

  // catch (err) có scope riêng và phải che `const err = await ...` ở nhánh
  // trước đó; nếu không `err.message` sẽ bị chấm nhầm thành trường API.
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai !== 'identifier' || tokens[i].giaTri !== 'catch' || tokens[i + 1]?.giaTri !== '(') continue;
    const dongThamSo = moSangDong.get(i + 1);
    const moThan = dongThamSo + 1;
    if (tokens[moThan]?.giaTri !== '{') continue;
    const block = blocks[blockTheoNgoacMo.get(moThan)];
    themPattern(i + 2, dongThamSo, block, 'catch', true);
  }

  function giaiBinding(ten, chiSoDung) {
    const ungVien = bindings
      .filter((x) => x.ten === ten && x.batDauPhamVi < chiSoDung && chiSoDung < x.ketThucPhamVi)
      .sort((a, b) => {
        const rongA = a.ketThucPhamVi - a.batDauPhamVi;
        const rongB = b.ketThucPhamVi - b.batDauPhamVi;
        if (rongA !== rongB) return rongA - rongB;
        return b.chiSoKhaiBao - a.chiSoKhaiBao;
      });
    if (!ungVien.length) return null;
    // let/const che cả block từ đầu (TDZ); đừng rơi xuyên xuống binding ngoài.
    return ungVien[0];
  }

  return { bindings, giaiBinding, hamTai };
}

function chuanHoaDuongLiteral(literal) {
  const moc = [literal.indexOf('?'), literal.indexOf('#')].filter((x) => x >= 0);
  const het = moc.length ? Math.min(...moc) : literal.length;
  const duong = literal.slice(0, het);
  if (duong.includes('${') || duong.includes('\\')) return null;
  return duong;
}

/**
 * Nối đúng binding: authFetch -> biến response -> biến nhận JSON -> trường.
 * Không lần theo alias (`state.x = data`) vì lúc đó không còn bằng chứng tĩnh
 * rằng thuộc tính về sau vẫn là trường cấp ngoài của đúng response này.
 */
function rutTruongJsonTheoRoute(ma) {
  const tokens = tokenHoaJs(ma);
  const cauTruc = lapCauTrucScope(tokens);
  const cacHam = rutPhamViHam(tokens, cauTruc);
  const bang = taoBangBinding(tokens, cauTruc, cacHam);
  const { loiGoi, khongPhaiLiteral } = rutLoiGoiAuthFetch(ma);
  const loiTheoOffset = new Map(loiGoi.map((x) => [x.batDauLoiGoi, x]));
  const bindingTheoKhaiBao = new Map(bang.bindings.map((x) => [x.chiSoKhaiBao, x]));
  const phanHoi = [];
  const json = [];
  const truong = [];
  const khongChungMinhDuoc = khongPhaiLiteral.map((x) => ({
    dong: x.dong,
    lyDo: `authFetch không dùng đường literal: ${x.doiSo}`,
  }));

  function tenHamTai(chiSo) {
    return bang.hamTai(chiSo)?.ten || '<scope gốc>';
  }

  const tokenAuthFetch = [];
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai !== 'identifier' || tokens[i].giaTri !== 'authFetch' || tokens[i + 1]?.giaTri !== '(') continue;
    if (tokens[i - 1]?.giaTri === 'function') continue;
    tokenAuthFetch.push(i);
    const loi = loiTheoOffset.get(tokens[i].batDau);
    if (!loi) {
      khongChungMinhDuoc.push({ dong: tokens[i].dong, lyDo: 'Lời gọi authFetch tokenizer thấy nhưng cửa route chưa rút được' });
      continue;
    }
    if (!['const', 'let', 'var'].includes(tokens[i - 4]?.giaTri) ||
        tokens[i - 3]?.loai !== 'identifier' || tokens[i - 2]?.giaTri !== '=' ||
        tokens[i - 1]?.giaTri !== 'await') {
      khongChungMinhDuoc.push({
        dong: tokens[i].dong,
        lyDo: `authFetch ${loi.duong} không được gán trực tiếp dạng "const resp = await ..."`,
      });
      continue;
    }
    const binding = bindingTheoKhaiBao.get(i - 3);
    if (!binding) {
      khongChungMinhDuoc.push({ dong: tokens[i].dong, lyDo: `Không dựng được binding ${tokens[i - 3].giaTri}` });
      continue;
    }
    binding.phanHoiApi = { duong: loi.duong, dong: tokens[i].dong };
    phanHoi.push({
      duong: loi.duong,
      bien: binding.ten,
      dong: tokens[i].dong,
      ham: tenHamTai(i),
      binding,
    });
  }

  if (tokenAuthFetch.length !== loiGoi.length + khongPhaiLiteral.length) {
    khongChungMinhDuoc.push({
      dong: 0,
      lyDo: `Hai tokenizer không đồng ý về số authFetch: ${tokenAuthFetch.length} và ${loiGoi.length + khongPhaiLiteral.length}`,
    });
  }

  const parseDaChungMinh = new Set();
  function ganJson(awaitIndex, bindingResp, baseIndex) {
    if (!['const', 'let', 'var'].includes(tokens[awaitIndex - 3]?.giaTri) ||
        tokens[awaitIndex - 2]?.loai !== 'identifier' || tokens[awaitIndex - 1]?.giaTri !== '=') {
      khongChungMinhDuoc.push({
        dong: tokens[awaitIndex].dong,
        lyDo: `JSON của ${bindingResp.phanHoiApi.duong} không được gán trực tiếp vào một biến đơn`,
      });
      return;
    }
    const bindingJson = bindingTheoKhaiBao.get(awaitIndex - 2);
    if (!bindingJson) {
      khongChungMinhDuoc.push({ dong: tokens[awaitIndex].dong, lyDo: 'Không dựng được binding nhận JSON' });
      return;
    }
    bindingJson.jsonApi = bindingResp.phanHoiApi;
    json.push({
      duong: bindingResp.phanHoiApi.duong,
      bien: bindingJson.ten,
      dong: tokens[awaitIndex].dong,
      ham: tenHamTai(awaitIndex),
      binding: bindingJson,
    });
    parseDaChungMinh.add(baseIndex);
  }

  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai !== 'identifier' || tokens[i].giaTri !== 'await') continue;

    // await resp.json(), kể cả khi sau đó nối `.catch(...)`.
    if (tokens[i + 1]?.loai === 'identifier' && tokens[i + 2]?.giaTri === '.' &&
        tokens[i + 3]?.giaTri === 'json' && tokens[i + 4]?.giaTri === '(') {
      const bindingResp = bang.giaiBinding(tokens[i + 1].giaTri, i + 1);
      if (bindingResp?.phanHoiApi) ganJson(i, bindingResp, i + 1);
      continue;
    }

    // await readJsonSafely(resp)
    if (tokens[i + 1]?.giaTri === 'readJsonSafely' && tokens[i + 2]?.giaTri === '(' &&
        tokens[i + 3]?.loai === 'identifier') {
      const bindingResp = bang.giaiBinding(tokens[i + 3].giaTri, i + 3);
      if (bindingResp?.phanHoiApi) ganJson(i, bindingResp, i + 1);
    }
  }

  // Nếu response đã biết còn được parse theo hình dạng khác, không bỏ qua.
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai === 'identifier' && tokens[i + 1]?.giaTri === '.' &&
        tokens[i + 2]?.giaTri === 'json' && tokens[i + 3]?.giaTri === '(') {
      const binding = bang.giaiBinding(tokens[i].giaTri, i);
      if (binding?.phanHoiApi && !parseDaChungMinh.has(i)) {
        khongChungMinhDuoc.push({
          dong: tokens[i].dong,
          lyDo: `Không chứng minh được phép parse ${binding.phanHoiApi.duong} qua ${binding.ten}.json()`,
        });
      }
    }
    if (tokens[i].loai === 'identifier' && tokens[i].giaTri === 'readJsonSafely' && tokens[i + 1]?.giaTri === '(' &&
        tokens[i + 2]?.loai === 'identifier') {
      const binding = bang.giaiBinding(tokens[i + 2].giaTri, i + 2);
      if (binding?.phanHoiApi && !parseDaChungMinh.has(i)) {
        khongChungMinhDuoc.push({
          dong: tokens[i].dong,
          lyDo: `Không chứng minh được phép parse ${binding.phanHoiApi.duong} qua readJsonSafely`,
        });
      }
    }
  }

  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].loai !== 'identifier') continue;
    // `obj.data.x`: token `data` ở đây là tên thuộc tính, không phải binding.
    if (tokens[i - 1]?.giaTri === '.' || tokens[i - 1]?.giaTri === '?.') continue;
    const binding = bang.giaiBinding(tokens[i].giaTri, i);
    if (!binding?.jsonApi) continue;

    let j = i + 1;
    let tenTruong = null;
    if (tokens[j]?.giaTri === '.' || tokens[j]?.giaTri === '?.') {
      j += 1;
      if (tokens[j]?.loai === 'identifier') {
        tenTruong = tokens[j].giaTri;
      } else if (tokens[j]?.giaTri === '[') {
        // xử lý chung ở nhánh dưới
      } else {
        khongChungMinhDuoc.push({ dong: tokens[i].dong, lyDo: `Thuộc tính sau ${binding.ten} không phải identifier` });
      }
    }
    if (!tenTruong && tokens[j]?.giaTri === '[') {
      const dongNgoac = cauTruc.moSangDong.get(j);
      if (dongNgoac === j + 2 && tokens[j + 1]?.loai === 'literal' &&
          !tokens[j + 1].regex && !tokens[j + 1].giaTri.includes('${') &&
          !tokens[j + 1].giaTri.includes('\\')) {
        tenTruong = tokens[j + 1].giaTri;
      } else {
        khongChungMinhDuoc.push({
          dong: tokens[i].dong,
          lyDo: `Truy cập ${binding.ten}[...] động của ${binding.jsonApi.duong}`,
        });
      }
    }
    if (!tenTruong) continue;
    if (binding.baoThu) {
      khongChungMinhDuoc.push({
        dong: tokens[i].dong,
        lyDo: `Binding destructuring ${binding.ten} che biến JSON; không thể phân giải chắc chắn`,
      });
      continue;
    }
    truong.push({
      duong: binding.jsonApi.duong,
      truong: tenTruong,
      bien: binding.ten,
      dong: tokens[i].dong,
      ham: tenHamTai(i),
    });
  }

  return { phanHoi, json, truong, khongChungMinhDuoc };
}

const MA_RUT_HOP_DONG_PYTHON = String.raw`
import ast
import json
import sys

app_path, api_path = sys.argv[1:3]
with open(app_path, "r", encoding="utf-8") as f:
    app_tree = ast.parse(f.read(), filename=app_path)
with open(api_path, "r", encoding="utf-8") as f:
    api_tree = ast.parse(f.read(), filename=api_path)

def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return (prefix + "." if prefix else "") + node.attr
    return None

routes = []
non_literals = []
for node in ast.walk(app_tree):
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        continue
    if node.func.attr not in {"add_get", "add_post"}:
        continue
    owner = node.func.value
    if not isinstance(owner, ast.Attribute) or owner.attr != "router":
        continue
    if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
        non_literals.append({"kind": "route", "line": node.lineno})
        continue
    if len(node.args) < 2 or not dotted_name(node.args[1]):
        non_literals.append({"kind": "handler", "line": node.lineno})
        continue
    routes.append({
        "method": node.func.attr[4:].upper(),
        "path": node.args[0].value,
        "line": node.lineno,
        "handler": dotted_name(node.args[1]).split(".")[-1],
    })

functions = {
    node.name: node
    for node in api_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

class ResponseVisitor(ast.NodeVisitor):
    """Chỉ thăm thân hàm hiện tại; response trong hàm lồng không thuộc handler."""

    def __init__(self):
        self.static_responses = []
        self.dynamic_responses = []
        self.nonliteral_keys = []
        self.returned_helpers = []

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_ClassDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_Return(self, node):
        value = node.value
        if isinstance(value, ast.Await):
            value = value.value
        if isinstance(value, ast.Call):
            name = dotted_name(value.func)
            if name and name in functions:
                self.returned_helpers.append({"line": node.lineno, "name": name})
        self.generic_visit(node)

    def visit_Call(self, node):
        if dotted_name(node.func) == "web.json_response":
            data = node.args[0] if node.args else None
            if data is None:
                for keyword in node.keywords:
                    if keyword.arg == "data":
                        data = keyword.value
                        break
            if isinstance(data, ast.Dict):
                keys = []
                for key in data.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        keys.append(key.value)
                    else:
                        self.nonliteral_keys.append(getattr(key, "lineno", node.lineno))
                self.static_responses.append({"line": node.lineno, "keys": sorted(set(keys))})
            else:
                self.dynamic_responses.append({
                    "line": node.lineno,
                    "expression_type": type(data).__name__ if data is not None else "missing",
                })
        self.generic_visit(node)

raw = {}
for name, fn in functions.items():
    visitor = ResponseVisitor()
    for statement in fn.body:
        visitor.visit(statement)
    raw[name] = {
        "static_responses": visitor.static_responses,
        "dynamic_responses": visitor.dynamic_responses,
        "nonliteral_keys": visitor.nonliteral_keys,
        "returned_helpers": visitor.returned_helpers,
    }

memo = {}
def resolve(name, stack=()):
    if name in memo:
        return memo[name]
    if name not in raw or name in stack:
        return {
            "keys": [], "static_lines": [], "dynamic_responses": [],
            "nonliteral_keys": [], "helper_chain": [],
        }
    own = raw[name]
    keys = {key for response in own["static_responses"] for key in response["keys"]}
    static_lines = [response["line"] for response in own["static_responses"]]
    dynamic = list(own["dynamic_responses"])
    nonliteral = list(own["nonliteral_keys"])
    helper_chain = []
    for helper in own["returned_helpers"]:
        child = resolve(helper["name"], stack + (name,))
        keys.update(child["keys"])
        static_lines.extend(child["static_lines"])
        dynamic.extend(child["dynamic_responses"])
        nonliteral.extend(child["nonliteral_keys"])
        helper_chain.append(helper)
        helper_chain.extend(child["helper_chain"])
    result = {
        "keys": sorted(keys),
        "static_lines": sorted(set(static_lines)),
        "dynamic_responses": dynamic,
        "nonliteral_keys": sorted(set(nonliteral)),
        "helper_chain": helper_chain,
    }
    memo[name] = result
    return result

handlers = {name: resolve(name) for name in functions}
seen_paths = set()
duplicate_paths = []
for route in routes:
    if route["path"] in seen_paths:
        duplicate_paths.append(route["path"])
    seen_paths.add(route["path"])
missing_handlers = sorted({route["handler"] for route in routes if route["handler"] not in handlers})

print(json.dumps({
    "routes": routes,
    "non_literals": non_literals,
    "handlers": handlers,
    "duplicate_paths": sorted(set(duplicate_paths)),
    "missing_handlers": missing_handlers,
}, ensure_ascii=False))
`;

let cacheHopDongPython = null;

function rutHopDongPython() {
  if (cacheHopDongPython) return cacheHopDongPython;
  assert.ok(fs.existsSync(PYTHON), `Không có Python của kho: ${PYTHON}`);
  assert.ok(fs.existsSync(TEP_API_PY), `Không có tệp handler Python: ${TEP_API_PY}`);
  const ketQua = spawnSync(
    PYTHON,
    ['-X', 'utf8', '-c', MA_RUT_HOP_DONG_PYTHON, TEP_PY, TEP_API_PY],
    {
    cwd: GOC,
    encoding: 'utf8',
    }
  );
  assert.strictEqual(
    ketQua.status,
    0,
    `Không phân tích được hợp đồng Python (exit=${ketQua.status}):\n${ketQua.stderr || ketQua.error || ''}`
  );
  let data;
  try {
    data = JSON.parse(ketQua.stdout);
  } catch (err) {
    assert.fail(`Python không trả JSON hợp đồng hợp lệ: ${err.message}\nstdout=${ketQua.stdout}`);
  }
  assert.deepStrictEqual(
    data.non_literals,
    [],
    `add_get/add_post không dùng route/handler tĩnh: ${JSON.stringify(data.non_literals)}`
  );
  assert.deepStrictEqual(data.duplicate_paths, [], `Python đăng ký trùng route: ${data.duplicate_paths.join(', ')}`);
  assert.deepStrictEqual(data.missing_handlers, [], `Không tìm thấy handler: ${data.missing_handlers.join(', ')}`);
  cacheHopDongPython = data;
  return data;
}

function rutRoutePython() {
  return rutHopDongPython().routes;
}

test('mọi đường literal authFetch đều tồn tại trong router Python', () => {
  const maJs = fs.readFileSync(TEP_JS, 'utf8');
  const { loiGoi, khongPhaiLiteral } = rutLoiGoiAuthFetch(maJs);
  const routes = rutRoutePython();
  const apiPython = routes.filter((x) => x.path.startsWith('/api/'));

  assert.deepStrictEqual(
    khongPhaiLiteral,
    [],
    'Có authFetch không mang đường literal tĩnh; cửa không thể chứng minh route ấy tồn tại:\n' +
      khongPhaiLiteral.map((x) => `  dòng ${x.dong}: ${x.doiSo}`).join('\n')
  );
  assert.ok(loiGoi.length > 0, 'Không rút được lời gọi authFetch nào — không được xanh rỗng');
  assert.ok(apiPython.length > 0, 'Không rút được route /api/ Python nào — không được xanh rỗng');

  const duongJs = [...new Set(loiGoi.map((x) => x.duong))].sort();
  const duongPython = [...new Set(apiPython.map((x) => x.path))].sort();
  const pythonSet = new Set(duongPython);
  const jsSet = new Set(duongJs);
  const jsKhongCoPython = duongJs.filter((x) => !pythonSet.has(x));
  const pythonChuaDuocJsGoi = duongPython.filter((x) => !jsSet.has(x));

  console.log(
    `[HỢP ĐỒNG API] JS: ${loiGoi.length} lời gọi / ${duongJs.length} đường; ` +
      `Python: ${duongPython.length} đường /api/`
  );
  if (pythonChuaDuocJsGoi.length) {
    console.warn(
      '[CẢNH BÁO, KHÔNG ĐỎ] Python có route app.js chưa gọi: ' +
        pythonChuaDuocJsGoi.join(', ')
    );
  }

  assert.deepStrictEqual(
    jsKhongCoPython,
    [],
    'JS gọi đường Python không đăng ký (chắc chắn 404 khi chạy): ' + jsKhongCoPython.join(', ')
  );
});

test('mọi trường đọc trực tiếp từ JSON authFetch đều có trong handler Python', () => {
  const maJs = fs.readFileSync(TEP_JS, 'utf8');
  const ketQuaJs = rutTruongJsonTheoRoute(maJs);
  const hopDongPython = rutHopDongPython();
  const routeTheoDuong = new Map(hopDongPython.routes.map((x) => [x.path, x]));

  assert.deepStrictEqual(
    ketQuaJs.khongChungMinhDuoc,
    [],
    'Có hình dạng JS mà cửa không thể nối chắc chắn theo binding:\n' +
      ketQuaJs.khongChungMinhDuoc.map((x) => `  dòng ${x.dong}: ${x.lyDo}`).join('\n')
  );
  assert.ok(ketQuaJs.phanHoi.length > 0, 'Không nối được response authFetch nào — không được xanh rỗng');
  assert.ok(ketQuaJs.json.length > 0, 'Không nối được biến nhận JSON nào — không được xanh rỗng');
  assert.ok(ketQuaJs.truong.length > 0, 'Không rút được trường JSON nào — không được xanh rỗng');

  const capTheoKhoa = new Map();
  for (const doc of ketQuaJs.truong) {
    const khoa = `${doc.duong}\u0000${doc.truong}`;
    if (!capTheoKhoa.has(khoa)) capTheoKhoa.set(khoa, doc);
  }

  const routeKhongCoHandler = [];
  const handlerCoKhoaDong = [];
  const truongKhongCoPython = [];
  const handlerDaDoiChieu = new Set();
  for (const doc of capTheoKhoa.values()) {
    const route = routeTheoDuong.get(doc.duong);
    const handler = route ? hopDongPython.handlers[route.handler] : null;
    if (!route || !handler) {
      routeKhongCoHandler.push(doc);
      continue;
    }
    handlerDaDoiChieu.add(route.handler);
    if (handler.nonliteral_keys.length) {
      handlerCoKhoaDong.push({ handler: route.handler, lines: handler.nonliteral_keys });
    }
    if (!handler.keys.includes(doc.truong)) {
      truongKhongCoPython.push({ ...doc, handler: route.handler });
    }
  }

  assert.deepStrictEqual(
    routeKhongCoHandler,
    [],
    'Trường JS không nối được tới handler Python:\n' +
      routeKhongCoHandler.map((x) => `  ${x.duong}.${x.truong} (JS dòng ${x.dong})`).join('\n')
  );
  assert.deepStrictEqual(
    handlerCoKhoaDong,
    [],
    'Handler dùng khóa dict không tĩnh; cửa không thể chứng minh tên trường:\n' +
      handlerCoKhoaDong.map((x) => `  ${x.handler}: dòng ${x.lines.join(', ')}`).join('\n')
  );
  assert.deepStrictEqual(
    truongKhongCoPython,
    [],
    'JS đọc trường không có trong bất kỳ web.json_response({...}) tĩnh nào của handler:\n' +
      truongKhongCoPython.map(
        (x) => `  ${x.duong}: ${x.bien}.${x.truong} — ${x.ham}, JS dòng ${x.dong}; handler ${x.handler}`
      ).join('\n')
  );

  const soPhanHoiDong = [...handlerDaDoiChieu]
    .flatMap((ten) => hopDongPython.handlers[ten].dynamic_responses)
    .length;
  console.log(
    `[HỢP ĐỒNG TRƯỜNG] ${ketQuaJs.phanHoi.length} response / ` +
      `${ketQuaJs.json.length} lần nhận JSON / ${capTheoKhoa.size} cặp đường-trường; ` +
      `${handlerDaDoiChieu.size} handler Python`
  );
  if (soPhanHoiDong) {
    console.warn(
      `[GIỚI HẠN ĐÃ GHI NHẬN] ${soPhanHoiDong} json_response dùng object động; ` +
        'cửa chỉ chấp nhận các trường đồng thời có bằng chứng ở nhánh dict literal.'
    );
  }
});
