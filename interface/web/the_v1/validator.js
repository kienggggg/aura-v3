// validator.js — Bộ kiểm tra tĩnh phía Client (Javascript thuần, chạy trên cả Browser và Node.js)
// Thiết kế theo đúng đặc tả kiểm tra của AURA v3 và đối chiếu 1:1 với core/the_v1.py.

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.TheValidator = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  const BUILTIN_SYMBOLS = new Set([
    "True", "False", "None", "range", "len", "int", "str", "float", "list",
    "dict", "set", "tuple", "sum", "min", "max", "abs", "round", "bool",
    "print", "input", "enumerate", "zip", "sorted", "reversed", "map", "filter",
    "open", "type", "isinstance", "issubclass", "iter", "next", "all", "any",
    "chr", "ord", "hex", "bin", "oct", "pow", "divmod", "format", "repr",
    "getattr", "hasattr", "setattr", "delattr", "frozenset", "callable", "id",
    "hash", "staticmethod", "classmethod", "property", "super", "vars", "dir",
    "bytes", "bytearray", "slice", "complex", "memoryview", "ascii", "help",
    "globals", "locals", "Exception", "ValueError", "TypeError", "KeyError",
    "IndexError", "AttributeError", "RuntimeError", "StopIteration",
    "FileNotFoundError", "AssertionError", "ImportError", "IOError", "OSError",
    // Từ khóa Python
    "if", "else", "elif", "for", "while", "in", "is", "not", "and", "or",
    "as", "with", "try", "except", "finally", "def", "class", "return", "yield",
    "pass", "break", "continue", "import", "from", "lambda", "global", "nonlocal",
    "assert", "del", "raise", "async", "await"
  ]);

  const NHOM_THE = {
    dieu_khien: { ten: "Điều khiển", mau: "#3B82F6" },
    du_lieu: { ten: "Dữ liệu", mau: "#10B981" },
    vao_ra: { ten: "Vào / Ra", mau: "#8B5CF6" },
    ham: { ten: "Hàm", mau: "#F59E0B" },
    chu_thich: { ten: "Chú thích", mau: "#14B8A6" },
    ma_tho: { ten: "Mã thô", mau: "#6B7280" }
  };

  const BO_THE_V1 = {
    gan: {
      ma: "gan",
      ten: "Gán",
      nhom: "du_lieu",
      o: [
        { ten: "ten_bien", kieu: "chu", bat_buoc: true, goi_y: "x" },
        { ten: "gia_tri", kieu: "bieu_thuc", bat_buoc: true, goi_y: "10" }
      ],
      co_than: false,
      mau: "#10B981"
    },
    in_ra: {
      ma: "in_ra",
      ten: "In ra",
      nhom: "vao_ra",
      o: [
        { ten: "noi_dung", kieu: "bieu_thuc", bat_buoc: true, goi_y: '"Xin chào"' }
      ],
      co_than: false,
      mau: "#8B5CF6"
    },
    neu: {
      ma: "neu",
      ten: "Nếu",
      nhom: "dieu_khien",
      o: [
        { ten: "dieu_kien", kieu: "bieu_thuc", bat_buoc: true, goi_y: "x > 0" }
      ],
      co_than: true,
      mau: "#3B82F6"
    },
    nguoc_lai: {
      ma: "nguoc_lai",
      ten: "Ngược lại",
      nhom: "dieu_khien",
      o: [],
      co_than: true,
      mau: "#3B82F6"
    },
    lap_moi: {
      ma: "lap_moi",
      ten: "Lặp mỗi",
      nhom: "dieu_khien",
      o: [
        { ten: "bien", kieu: "chu", bat_buoc: true, goi_y: "i" },
        { ten: "day", kieu: "bieu_thuc", bat_buoc: true, goi_y: "range(10)" }
      ],
      co_than: true,
      mau: "#3B82F6"
    },
    lap_khi: {
      ma: "lap_khi",
      ten: "Lặp khi",
      nhom: "dieu_khien",
      o: [
        { ten: "dieu_kien", kieu: "bieu_thuc", bat_buoc: true, goi_y: "x > 0" }
      ],
      co_than: true,
      mau: "#3B82F6"
    },
    tra_ve: {
      ma: "tra_ve",
      ten: "Trả về",
      nhom: "ham",
      o: [
        { ten: "gia_tri", kieu: "bieu_thuc", bat_buoc: true, goi_y: "x + 1" }
      ],
      co_than: false,
      mau: "#F59E0B"
    },
    ham: {
      ma: "ham",
      ten: "Định nghĩa hàm",
      nhom: "ham",
      o: [
        { ten: "ten_ham", kieu: "chu", bat_buoc: true, goi_y: "tinh_tong" },
        { ten: "tham_so", kieu: "chu", bat_buoc: false, goi_y: "a, b" }
      ],
      co_than: true,
      mau: "#F59E0B"
    },
    goi_ham: {
      ma: "goi_ham",
      ten: "Gọi hàm",
      nhom: "ham",
      o: [
        { ten: "ten_ham", kieu: "chu", bat_buoc: true, goi_y: "tinh_tong" },
        { ten: "doi_so", kieu: "chu", bat_buoc: false, goi_y: "1, 2" }
      ],
      co_than: false,
      mau: "#F59E0B"
    },
    pheptinh: {
      ma: "pheptinh",
      ten: "Phép tính",
      nhom: "du_lieu",
      o: [
        { ten: "trai", kieu: "bieu_thuc", bat_buoc: true, goi_y: "a" },
        { ten: "phep", kieu: "chu", bat_buoc: true, goi_y: "+" },
        { ten: "phai", kieu: "bieu_thuc", bat_buoc: true, goi_y: "b" }
      ],
      co_than: false,
      mau: "#10B981"
    },
    chu_thich: {
      ma: "chu_thich",
      ten: "Chú thích",
      nhom: "chu_thich",
      o: [
        { ten: "noi_dung", kieu: "chu", bat_buoc: true, goi_y: "# Chú thích" }
      ],
      co_than: false,
      mau: "#14B8A6"
    },
    ma_tho: {
      ma: "ma_tho",
      ten: "Mã thô",
      nhom: "ma_tho",
      o: [
        { ten: "nguyen_van", kieu: "chu_nhieu_dong", bat_buoc: true, goi_y: "" }
      ],
      co_than: false,
      mau: "#6B7280"
    }
  };

  function trichXuatBien(bieuThuc) {
    if (!bieuThuc || typeof bieuThuc !== "string") return new Set();
    let str = bieuThuc.trim();
    if (!str) return new Set();

    // Xóa chuỗi ký tự và bytes literal (kèm tiền tố b, r, f, u, rb, fr...)
    str = str.replace(/\b[rRuUbBfF]+(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, " ");

    // Thu thập biến cục bộ sinh từ comprehension: for <var> in ...
    const compVars = new Set();
    const compMatches = str.matchAll(/\bfor\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\s+in\b/g);
    for (const m of compMatches) {
      const vars = m[1].split(",");
      for (const v of vars) {
        const vClean = v.trim();
        if (vClean) compVars.add(vClean);
      }
    }

    // Xóa các thuộc tính / phương thức .attr để không bắt nhầm attr là biến
    str = str.replace(/\.[a-zA-Z_][a-zA-Z0-9_]*/g, " ");

    const tokens = str.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || [];
    const res = new Set();
    for (const t of tokens) {
      if (!BUILTIN_SYMBOLS.has(t) && !compVars.has(t)) {
        res.add(t);
      }
    }
    return res;
  }

  function trichXuatImport(code) {
    const symbols = new Set();
    if (!code || typeof code !== "string") return symbols;
    const lines = code.split("\n");
    for (let line of lines) {
      line = line.trim();
      if (line.startsWith("import ")) {
        const parts = line.slice(7).split(",");
        for (let p of parts) {
          let name = p.trim();
          if (name.includes(" as ")) {
            name = name.split(" as ")[1].trim();
          } else {
            name = name.split(".")[0].trim();
          }
          if (name) symbols.add(name);
        }
      } else if (line.startsWith("from ") && line.includes(" import ")) {
        const impPart = line.split(" import ")[1];
        if (impPart) {
          const parts = impPart.split(",");
          for (let p of parts) {
            let name = p.trim();
            if (name.includes(" as ")) {
              name = name.split(" as ")[1].trim();
            }
            name = name.replace(/[()]/g, "").trim();
            if (name && name !== "*") symbols.add(name);
          }
        }
      }
    }
    return symbols;
  }

  function trichXuatBienGanTrongMaTho(code) {
    const names = new Set();
    if (!code || typeof code !== "string") return names;
    const lines = code.split("\n");
    for (let line of lines) {
      const m = line.match(/^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=/);
      if (m) names.add(m[1]);
      const defM = line.match(/^\s*(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)/);
      if (defM) names.add(defM[1]);
    }
    return names;
  }

  function trichXuatTenThamSo(thamSoStr) {
    if (!thamSoStr || typeof thamSoStr !== "string") return [];
    let str = thamSoStr.trim();
    if (!str) return [];

    let clean = str.replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/'(?:[^'\\]|\\.)*'/g, "''");
    let depth = 0;
    let cur = "";
    const chunks = [];
    for (let i = 0; i < clean.length; i++) {
      const ch = clean[i];
      if (ch === '(' || ch === '[' || ch === '{') depth++;
      else if (ch === ')' || ch === ']' || ch === '}') depth--;
      else if (ch === ',' && depth === 0) {
        if (cur.trim()) chunks.push(cur.trim());
        cur = "";
        continue;
      }
      cur += ch;
    }
    if (cur.trim()) chunks.push(cur.trim());

    const result = [];
    for (let p of chunks) {
      p = p.trim();
      if (p === "*") continue;
      let namePart = p.split(/[:=]/)[0].trim();
      namePart = namePart.replace(/^\*+/, "").trim();
      if (namePart && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(namePart)) {
        result.push(namePart);
      }
    }
    return result;
  }

  function demSoLanDungThe(nodes, counter) {
    if (!nodes) return;
    for (const n of nodes) {
      counter[n.ma] = (counter[n.ma] || 0) + 1;
      if (n.than && n.than.length > 0) {
        demSoLanDungThe(n.than, counter);
      }
    }
  }

  function thuThapBieuTuongToanCuc(nodes, globalSymbols) {
    if (!nodes) return;
    for (const node of nodes) {
      if (node.ma === "ham") {
        const tenH = (node.o && node.o.ten_ham) ? String(node.o.ten_ham).trim() : "";
        if (tenH) globalSymbols.add(tenH);
      } else if (node.ma === "ma_tho") {
        const code = (node.o && node.o.nguyen_van) ? String(node.o.nguyen_van) : (node.raw_text || "");
        trichXuatImport(code).forEach(s => globalSymbols.add(s));
        trichXuatBienGanTrongMaTho(code).forEach(s => globalSymbols.add(s));
      }
      if (node.than && node.than.length > 0) {
        thuThapBieuTuongToanCuc(node.than, globalSymbols);
      }
    }
  }

  function kiemTraCayThe(nodes) {
    const diagnostics = [];
    const soLanDung = {};
    for (const k in BO_THE_V1) {
      soLanDung[k] = 0;
    }
    demSoLanDungThe(nodes, soLanDung);

    // PHA 1: Thu thập biểu tượng toàn cục
    const globalSymbols = new Set(BUILTIN_SYMBOLS);
    thuThapBieuTuongToanCuc(nodes, globalSymbols);

    const cacBienDaGan = new Set();
    const cacBienDaDoc = new Set();

    // PHA 2: Duyệt kiểm tra phạm vi và cú pháp
    function kiemTraDanhSach(nodeList, depth, insideFunction, scopeVars, parentMa = null) {
      if (!nodeList) return;
      let prevNode = null;
      let daGapTraVe = false;

      for (let i = 0; i < nodeList.length; i++) {
        const node = nodeList[i];
        const ma = node.ma;
        const defn = BO_THE_V1[ma];

        // CẢNH BÁO VÀNG 4: Lồng sâu quá 4 tầng
        if (depth > 4) {
          diagnostics.push({
            muc_do: "vang",
            ma_loi: "excessive_nesting",
            thong_diep: `Khối lệnh lồng quá sâu (${depth} tầng, tối đa 4)`,
            node_id: node.id,
            line: node.line_start || null
          });
        }

        // CẢNH BÁO VÀNG 3: Thẻ nằm sau tra_ve trong cùng một thân
        if (daGapTraVe) {
          diagnostics.push({
            muc_do: "vang",
            ma_loi: "unreachable_code",
            thong_diep: "Thẻ nằm sau lệnh 'Trả về', sẽ không bao giờ được chạy tới",
            node_id: node.id,
            line: node.line_start || null
          });
        }
        if (ma === "tra_ve") {
          daGapTraVe = true;
        }

        // LỖI ĐỎ 1: Ô bắt buộc còn trống
        if (defn && defn.o) {
          for (const oDef of defn.o) {
            if (oDef.bat_buoc) {
              const val = (node.o && node.o[oDef.ten]) ? String(node.o[oDef.ten]).trim() : "";
              if (!val) {
                diagnostics.push({
                  muc_do: "do",
                  ma_loi: "empty_required_field",
                  thong_diep: `Ô bắt buộc '${oDef.ten}' của thẻ '${defn.ten}' còn trống`,
                  node_id: node.id,
                  line: node.line_start || null
                });
              }
            }
          }
        }

        // LỖI ĐỎ 2: nguoc_lai không đứng ngay sau neu (hoặc thuộc neu)
        if (ma === "nguoc_lai") {
          const hopLeElse = (parentMa === "neu") || (prevNode && prevNode.ma === "neu");
          if (!hopLeElse) {
            diagnostics.push({
              muc_do: "do",
              ma_loi: "orphan_else",
              thong_diep: "Thẻ 'Ngược lại' phải đứng ngay sau một thẻ 'Nếu'",
              node_id: node.id,
              line: node.line_start || null
            });
          }
        }

        // LỖI ĐỎ 3: tra_ve nằm ngoài mọi ham
        if (ma === "tra_ve" && !insideFunction) {
          diagnostics.push({
            muc_do: "do",
            ma_loi: "return_outside_function",
            thong_diep: "Lệnh 'Trả về' chỉ được dùng bên trong một thẻ 'Hàm'",
            node_id: node.id,
            line: node.line_start || null
          });
        }

        // LỖI ĐỎ 5: Chuỗi thẻ rỗng bên trong thẻ có thân
        if (defn && defn.co_than && (!node.than || node.than.length === 0)) {
          diagnostics.push({
            muc_do: "do",
            ma_loi: "empty_body",
            thong_diep: `Thẻ '${defn.ten}' có thân nhưng chưa chứa lệnh nào bên trong`,
            node_id: node.id,
            line: node.line_start || null
          });
        }

        const currentScope = new Set(scopeVars);

        if (ma === "gan") {
          const tenBien = (node.o && node.o.ten_bien) ? String(node.o.ten_bien).trim() : "";
          const giaTri = (node.o && node.o.gia_tri) ? String(node.o.gia_tri) : "";
          const readVars = trichXuatBien(giaTri);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' được sử dụng nhưng chưa từng được gán giá trị`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
          if (tenBien && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(tenBien)) {
            cacBienDaGan.add(tenBien);
            scopeVars.add(tenBien);
          }
        } else if (ma === "in_ra") {
          const noiDung = (node.o && node.o.noi_dung) ? String(node.o.noi_dung) : "";
          const readVars = trichXuatBien(noiDung);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' được sử dụng nhưng chưa từng được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
        } else if (ma === "neu") {
          const dk = (node.o && node.o.dieu_kien) ? String(node.o.dieu_kien) : "";
          const readVars = trichXuatBien(dk);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' trong điều kiện 'Nếu' chưa được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
        } else if (ma === "lap_khi") {
          const dk = (node.o && node.o.dieu_kien) ? String(node.o.dieu_kien) : "";
          const readVars = trichXuatBien(dk);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' trong điều kiện 'Lặp khi' chưa được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
          // CẢNH BÁO VÀNG 2: lap_khi điều kiện không đổi trong thân
          if (readVars.size > 0 && node.than && node.than.length > 0) {
            const assignedInBody = new Set();
            node.than.forEach(c => {
              if (c.ma === "gan" && c.o && c.o.ten_bien) {
                assignedInBody.add(String(c.o.ten_bien).trim());
              }
            });
            let hasOverlap = false;
            readVars.forEach(v => {
              if (assignedInBody.has(v)) hasOverlap = true;
            });
            if (!hasOverlap) {
              diagnostics.push({
                muc_do: "vang",
                ma_loi: "potential_infinite_loop",
                thong_diep: "Vòng lặp có thể lặp vô tận: không có biến điều kiện nào được thay đổi giá trị trong thân",
                node_id: node.id,
                line: node.line_start || null
              });
            }
          }
        } else if (ma === "lap_moi") {
          const dayLap = (node.o && node.o.day) ? String(node.o.day) : "";
          const readVars = trichXuatBien(dayLap);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến dãy '${v}' trong 'Lặp mỗi' chưa được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
        } else if (ma === "tra_ve") {
          const gt = (node.o && node.o.gia_tri) ? String(node.o.gia_tri) : "";
          const readVars = trichXuatBien(gt);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' trong giá trị 'Trả về' chưa được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
        } else if (ma === "pheptinh") {
          const t = (node.o && node.o.trai) ? String(node.o.trai) : "";
          const p = (node.o && node.o.phai) ? String(node.o.phai) : "";
          const readVars = new Set([...trichXuatBien(t), ...trichXuatBien(p)]);
          readVars.forEach(v => cacBienDaDoc.add(v));
          readVars.forEach(v => {
            if (!currentScope.has(v)) {
              diagnostics.push({
                muc_do: "do",
                ma_loi: "undefined_variable",
                thong_diep: `Biến '${v}' trong phép tính chưa được gán`,
                node_id: node.id,
                line: node.line_start || null
              });
            }
          });
        }

        if (node.than && node.than.length > 0) {
          const childScope = new Set(scopeVars);
          const isFn = insideFunction || (ma === "ham");
          if (ma === "ham") {
            const tenH = (node.o && node.o.ten_ham) ? String(node.o.ten_ham).trim() : "";
            if (tenH) {
              scopeVars.add(tenH);
              cacBienDaGan.add(tenH);
            }
            const rawParams = (node.o && node.o.tham_so) ? String(node.o.tham_so) : "";
            const params = trichXuatTenThamSo(rawParams);
            params.forEach(p => {
              childScope.add(p);
              cacBienDaGan.add(p);
            });
          } else if (ma === "lap_moi") {
            const b = (node.o && node.o.bien) ? String(node.o.bien).trim() : "";
            const loopVars = b.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || [];
            loopVars.forEach(v => {
              childScope.add(v);
              cacBienDaGan.add(v);
            });
          }

          kiemTraDanhSach(node.than, depth + 1, isFn, childScope, ma);
        }

        prevNode = node;
      }
    }

    kiemTraDanhSach(nodes, 1, false, new Set(globalSymbols), null);

    // CẢNH BÁO VÀNG 1: Biến gán rồi không dùng
    const chuaDung = [];
    cacBienDaGan.forEach(v => {
      if (!cacBienDaDoc.has(v) && !globalSymbols.has(v) && !v.startsWith("_")) {
        chuaDung.push(v);
      }
    });
    chuaDung.sort();
    chuaDung.forEach(varName => {
      diagnostics.push({
        muc_do: "vang",
        ma_loi: "unused_variable",
        thong_diep: `Biến '${varName}' đã được khai báo nhưng chưa được sử dụng lần nào`,
        node_id: "global",
        line: null
      });
    });

    const soDo = diagnostics.filter(d => d.muc_do === "do").length;
    const soVang = diagnostics.filter(d => d.muc_do === "vang").length;

    return {
      hop_le: (soDo === 0),
      so_loi_do: soDo,
      so_canh_bao_vang: soVang,
      danh_sach: diagnostics,
      so_lan_dung_the: soLanDung
    };
  }

  // `sourceMap` là tham số RA (out-param), tuỳ chọn: mảng rỗng do người gọi
  // truyền vào, hàm này ĐIỀN VÀO — mỗi phần tử là node.id của thẻ sinh ra
  // đúng DÒNG VẬT LÝ đó trong mã cuối cùng. Không đổi kiểu trả về (vẫn là
  // string) nên mọi chỗ gọi cũ không bị ảnh hưởng.
  //
  // Vì sao gắn NGAY TẠI ĐÂY thay vì viết một hàm dò-ngược riêng: hàm dò-ngược
  // sẽ là BẢN SAO logic của hàm này, phải tay đồng bộ mãi mãi — đúng bệnh vừa
  // dọn sáng 24/08 giữa core/lat_nguoc.py và tools/_worker_e1_exec.py. Ở đây
  // sourceMap sinh ra CÙNG LƯỢT với `code`, nên khớp 100% với thứ THẬT SỰ
  // được chạy, không phải suy luận lại từ một bản sinh mã khác.
  function sinhMaPython(nodes, indentLevel = 0, sourceMap = null) {
    if (!nodes) return "";
    const resLines = [];
    const ghiDong = (dong, nodeId) => {
      resLines.push(dong);
      if (sourceMap) sourceMap.push(nodeId);
    };

    for (const node of nodes) {
      const ma = node.ma;
      if (ma === "ma_tho") {
        const raw = (node.o && node.o.nguyen_van) || node.raw_text || "";
        if (raw) {
          const spaces = " ".repeat(indentLevel * 4);
          for (const rl of raw.split("\n")) {
            if (rl.trim()) {
              ghiDong(`${spaces}${rl}`, node.id);
            } else {
              ghiDong("", node.id);
            }
          }
        }
        continue;
      }

      const isElseOrElif = (ma === "nguoc_lai") || (ma === "neu" && node.o && node.o.noi_tiep === "1");
      const curIndent = isElseOrElif ? Math.max(0, indentLevel - 1) : indentLevel;
      const spaces = " ".repeat(curIndent * 4);

      let base = "";
      if (ma === "gan") {
        const tb = (node.o && node.o.ten_bien) || "x";
        const gt = (node.o && node.o.gia_tri) || "None";
        base = `${spaces}${tb} = ${gt}`;
      } else if (ma === "in_ra") {
        const nd = (node.o && node.o.noi_dung) || "";
        base = `${spaces}print(${nd})`;
      } else if (ma === "neu") {
        const dk = (node.o && node.o.dieu_kien) || "True";
        if (node.o && node.o.noi_tiep === "1") {
          base = `${spaces}elif ${dk}:`;
        } else {
          base = `${spaces}if ${dk}:`;
        }
      } else if (ma === "nguoc_lai") {
        base = `${spaces}else:`;
      } else if (ma === "lap_moi") {
        const b = (node.o && node.o.bien) || "item";
        const d = (node.o && node.o.day) || "[]";
        base = `${spaces}for ${b} in ${d}:`;
      } else if (ma === "lap_khi") {
        const dk = (node.o && node.o.dieu_kien) || "True";
        base = `${spaces}while ${dk}:`;
      } else if (ma === "tra_ve") {
        const gt = (node.o && node.o.gia_tri) || "";
        if (gt) {
          base = `${spaces}return ${gt}`.trimEnd();
        } else {
          base = `${spaces}return`;
        }
      } else if (ma === "ham") {
        const th = (node.o && node.o.ten_ham) || "ham";
        const ts = (node.o && node.o.tham_so) || "";
        let ktv = (node.o && node.o.kieu_tra_ve ? String(node.o.kieu_tra_ve).trim() : "");
        const prefix = (node.o && node.o.async === "1") ? "async def" : "def";

        const lines = [];
        if (node.o && node.o.trang_tri) {
          for (const dec of String(node.o.trang_tri).split("\n")) {
            if (dec.trim()) lines.push(`${spaces}${dec.trim()}`);
          }
        }

        let sig = "";
        if (ktv) {
          if (!ktv.startsWith("->")) ktv = `-> ${ktv}`;
          sig = `${spaces}${prefix} ${th}(${ts}) ${ktv}:`;
        } else {
          sig = `${spaces}${prefix} ${th}(${ts}):`;
        }
        lines.push(sig);
        base = lines.join("\n");
      } else if (ma === "goi_ham") {
        const th = (node.o && node.o.ten_ham) || "ham";
        const ds = (node.o && node.o.doi_so) || "";
        base = `${spaces}${th}(${ds})`;
      } else if (ma === "pheptinh") {
        const tr = (node.o && node.o.trai) || "a";
        const p = (node.o && node.o.phep) || "+";
        const ph = (node.o && node.o.phai) || "b";
        base = `${spaces}${tr} ${p} ${ph}`;
      } else if (ma === "chu_thich") {
        let nd = ((node.o && node.o.noi_dung) || "").trim();
        if (!nd.startsWith("#")) nd = `# ${nd}`;
        base = `${spaces}${nd}`;
      } else {
        base = `${spaces}pass`;
      }

      // `base` có thể là NHIỀU dòng vật lý (vd. "ham" kèm decorator, xem
      // dòng lines.join("\n") ở trên) — mỗi dòng đều thuộc về node này.
      // Chú thích cuối dòng (duoi_dong) chỉ dính vào dòng CUỐI của base.
      const baseLines = base.split("\n");
      baseLines.forEach((bl, i) => {
        if (i === baseLines.length - 1 && node.duoi_dong) {
          let dd = node.duoi_dong;
          if (dd.trimStart().startsWith("#") && !dd.startsWith(" ")) {
            dd = " " + dd;
          }
          ghiDong(`${bl}${dd}`, node.id);
        } else {
          ghiDong(bl, node.id);
        }
      });

      const defn = BO_THE_V1[ma];
      if (defn && defn.co_than) {
        if (node.than && node.than.length > 0) {
          const childIndent = curIndent + 1;
          // Truyền THẲNG sourceMap xuống đệ quy con (không tạo mảng con rồi
          // nối sau): con ghi trực tiếp vào cùng mảng, đúng thứ tự đệ quy —
          // trùng khớp tự nhiên với thứ tự dòng trong resLines.join("\n"),
          // không cần tính offset.
          resLines.push(sinhMaPython(node.than, childIndent, sourceMap));
        } else {
          const childSpaces = " ".repeat((curIndent + 1) * 4);
          ghiDong(`${childSpaces}pass`, node.id);
        }
      }
    }

    return resLines.join("\n");
  }

  return {
    BUILTIN_SYMBOLS,
    NHOM_THE,
    BO_THE_V1,
    trichXuatBien,
    demSoLanDungThe,
    kiemTraCayThe,
    sinhMaPython
  };
}));
