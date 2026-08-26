/**
 * test_hop_dong_api.js — cửa cứng cho đường dẫn giữa giao diện JS và Python.
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
 * Hai biến AURA_HOP_DONG_APP_JS / AURA_HOP_DONG_THE_APP_PY cho phép trỏ cửa
 * vào bản mutant tạm. Nhờ vậy có thể chứng minh ba lỗi gieo đều đỏ mà không
 * sửa app.js thật trong lúc một phép đo khác đang dùng kho.
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

const MA_RUT_ROUTE_PYTHON = String.raw`
import ast
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename=path)

routes = []
non_literals = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        continue
    if node.func.attr not in {"add_get", "add_post"}:
        continue
    owner = node.func.value
    if not isinstance(owner, ast.Attribute) or owner.attr != "router":
        continue
    if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
        non_literals.append(node.lineno)
        continue
    routes.append({"method": node.func.attr[4:].upper(), "path": node.args[0].value, "line": node.lineno})

print(json.dumps({"routes": routes, "non_literals": non_literals}, ensure_ascii=False))
`;

function rutRoutePython() {
  assert.ok(fs.existsSync(PYTHON), `Không có Python của kho: ${PYTHON}`);
  const ketQua = spawnSync(PYTHON, ['-X', 'utf8', '-c', MA_RUT_ROUTE_PYTHON, TEP_PY], {
    cwd: GOC,
    encoding: 'utf8',
  });
  assert.strictEqual(
    ketQua.status,
    0,
    `Không phân tích được route Python (exit=${ketQua.status}):\n${ketQua.stderr || ketQua.error || ''}`
  );
  let data;
  try {
    data = JSON.parse(ketQua.stdout);
  } catch (err) {
    assert.fail(`Python không trả JSON route hợp lệ: ${err.message}\nstdout=${ketQua.stdout}`);
  }
  assert.deepStrictEqual(
    data.non_literals,
    [],
    `add_get/add_post không dùng đường literal tại dòng: ${data.non_literals.join(', ')}`
  );
  return data.routes;
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
