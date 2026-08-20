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
    "chr", "ord", "hex", "bin", "oct", "pow", "divmod", "format", "repr"
  ]);

  const NHOM_THE = {
    dieu_khien: { ten: "Điều khiển", mau: "#3B82F6" },
    du_lieu: { ten: "Dữ liệu", mau: "#10B981" },
    vao_ra: { ten: "Vào / Ra", mau: "#8B5CF6" },
    ham: { ten: "Hàm", mau: "#F59E0B" },
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

    // Xóa chuỗi ký tự "..." và '...' để không nhận nhầm nội dung trong chuỗi là tên biến
    str = str.replace(/"(?:[^"\\]|\\.)*"/g, " ");
    str = str.replace(/'(?:[^'\\]|\\.)*'/g, " ");

    const tokens = str.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || [];
    const res = new Set();
    for (const t of tokens) {
      if (!BUILTIN_SYMBOLS.has(t)) {
        res.add(t);
      }
    }
    return res;
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

  function kiemTraCayThe(nodes) {
    const diagnostics = [];
    const soLanDung = {};
    for (const k in BO_THE_V1) {
      soLanDung[k] = 0;
    }
    demSoLanDungThe(nodes, soLanDung);

    const cacBienDaGan = new Set();
    const cacBienDaDoc = new Set();

    function kiemTraDanhSach(nodeList, depth, insideFunction, scopeVars) {
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

        // LỖI ĐỎ 2: nguoc_lai không đứng ngay sau neu
        if (ma === "nguoc_lai") {
          if (!prevNode || prevNode.ma !== "neu") {
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
            rawParams.split(",").forEach(p => {
              const trimmed = p.trim();
              if (trimmed) {
                childScope.add(trimmed);
                cacBienDaGan.add(trimmed);
              }
            });
          } else if (ma === "lap_moi") {
            const b = (node.o && node.o.bien) ? String(node.o.bien).trim() : "";
            if (b) {
              childScope.add(b);
              cacBienDaGan.add(b);
            }
          }

          kiemTraDanhSach(node.than, depth + 1, isFn, childScope);
        }

        prevNode = node;
      }
    }

    kiemTraDanhSach(nodes, 1, false, new Set());

    // CẢNH BÁO VÀNG 1: Biến gán rồi không dùng
    const chuaDung = [];
    cacBienDaGan.forEach(v => {
      if (!cacBienDaDoc.has(v)) {
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

  function sinhMaPython(nodes, indentLevel = 0) {
    if (!nodes) return "";
    const resLines = [];
    const spaces = " ".repeat(indentLevel * 4);

    for (const node of nodes) {
      const ma = node.ma;
      if (ma === "ma_tho") {
        const raw = (node.o && node.o.nguyen_van) || node.raw_text || "";
        if (raw) resLines.push(raw);
        continue;
      }

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
        base = `${spaces}if ${dk}:`;
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
        base = `${spaces}return ${gt}`.trimEnd();
      } else if (ma === "ham") {
        const th = (node.o && node.o.ten_ham) || "ham";
        const ts = (node.o && node.o.tham_so) || "";
        base = `${spaces}def ${th}(${ts}):`;
      } else if (ma === "goi_ham") {
        const th = (node.o && node.o.ten_ham) || "ham";
        const ds = (node.o && node.o.doi_so) || "";
        base = `${spaces}${th}(${ds})`;
      } else if (ma === "pheptinh") {
        const tr = (node.o && node.o.trai) || "a";
        const p = (node.o && node.o.phep) || "+";
        const ph = (node.o && node.o.phai) || "b";
        base = `${spaces}${tr} ${p} ${ph}`;
      } else {
        base = `${spaces}pass`;
      }

      if (node.duoi_dong) {
        let dd = node.duoi_dong;
        if (dd.trimStart().startsWith("#") && !dd.startsWith(" ")) {
          dd = " " + dd;
        }
        resLines.push(`${base}${dd}`);
      } else {
        resLines.push(base);
      }

      const defn = BO_THE_V1[ma];
      if (defn && defn.co_than) {
        if (node.than && node.than.length > 0) {
          resLines.push(sinhMaPython(node.than, indentLevel + 1));
        } else {
          const childSpaces = " ".repeat((indentLevel + 1) * 4);
          resLines.push(`${childSpaces}pass`);
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
