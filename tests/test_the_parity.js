// test_the_parity.js — Bộ kiểm thử đối chiếu 1:1 giữa Validator JS và Validator Python
// Chạy qua Node.js v24.16.0 với 22 mẫu cây thẻ đa dạng.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { kiemTraCayThe, sinhMaPython } = require('../interface/web/the_v1/validator');

const TEST_CASES = [
  // 1. Hàm cộng hợp lệ
  {
    name: "01_ham_cong_hop_le",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
        { id: "2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
      ]},
      { id: "3", ma: "gan", o: { ten_bien: "kq", gia_tri: "cong(5, 7)" }, than: [] },
      { id: "4", ma: "in_ra", o: { noi_dung: "kq" }, than: [] }
    ]
  },
  // 2. Lỗi đỏ: Ô bắt buộc còn trống
  {
    name: "02_o_bat_buoc_trong",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "", gia_tri: "10" }, than: [] }
    ]
  },
  // 3. Lỗi đỏ: nguoc_lai đứng đầu (mồ côi)
  {
    name: "03_nguoc_lai_mo_coi",
    tree: [
      { id: "1", ma: "nguoc_lai", o: {}, than: [
        { id: "2", ma: "in_ra", o: { noi_dung: '"hello"' }, than: [] }
      ]}
    ]
  },
  // 4. Lỗi đỏ: tra_ve nằm ngoài hàm
  {
    name: "04_tra_ve_ngoai_ham",
    tree: [
      { id: "1", ma: "tra_ve", o: { gia_tri: "42" }, than: [] }
    ]
  },
  // 5. Lỗi đỏ: Biến dùng mà chưa từng gán
  {
    name: "05_bien_chua_gan_trong_in_ra",
    tree: [
      { id: "1", ma: "in_ra", o: { noi_dung: "chua_co_bien + 1" }, than: [] }
    ]
  },
  // 6. Lỗi đỏ: Thân rỗng trong thẻ neu
  {
    name: "06_than_rong_neu",
    tree: [
      { id: "1", ma: "neu", o: { dieu_kien: "True" }, than: [] }
    ]
  },
  // 7. Cảnh báo vàng: Biến gán rồi không dùng
  {
    name: "07_bien_gan_khong_dung",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "thua", gia_tri: "123" }, than: [] },
      { id: "2", ma: "in_ra", o: { noi_dung: '"ok"' }, than: [] }
    ]
  },
  // 8. Cảnh báo vàng: lap_khi điều kiện không đổi trong thân
  {
    name: "08_lap_khi_vo_tan",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "x", gia_tri: "10" }, than: [] },
      { id: "2", ma: "lap_khi", o: { dieu_kien: "x > 0" }, than: [
        { id: "3", ma: "in_ra", o: { noi_dung: "x" }, than: [] }
      ]}
    ]
  },
  // 9. Cảnh báo vàng: Thẻ nằm sau tra_ve
  {
    name: "09_the_sau_tra_ve",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "fn", tham_so: "" }, than: [
        { id: "2", ma: "tra_ve", o: { gia_tri: "1" }, than: [] },
        { id: "3", ma: "in_ra", o: { noi_dung: '"dead"' }, than: [] }
      ]}
    ]
  },
  // 10. Cảnh báo vàng: Lồng sâu quá 4 tầng
  {
    name: "10_long_sau_qua_4_tang",
    tree: [
      { id: "1", ma: "neu", o: { dieu_kien: "True" }, than: [
        { id: "2", ma: "neu", o: { dieu_kien: "True" }, than: [
          { id: "3", ma: "neu", o: { dieu_kien: "True" }, than: [
            { id: "4", ma: "neu", o: { dieu_kien: "True" }, than: [
              { id: "5", ma: "in_ra", o: { noi_dung: '"deep"' }, than: [] }
            ]}
          ]}
        ]}
      ]}
    ]
  },
  // 11. Vòng lặp lap_moi hợp lệ với biến lặp
  {
    name: "11_lap_moi_hop_le",
    tree: [
      { id: "1", ma: "lap_moi", o: { bien: "item", day: "range(5)" }, than: [
        { id: "2", ma: "in_ra", o: { noi_dung: "item * 2" }, than: [] }
      ]}
    ]
  },
  // 12. Phép tính hợp lệ và gán
  {
    name: "12_pheptinh_hop_le",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "a", gia_tri: "10" }, than: [] },
      { id: "2", ma: "gan", o: { ten_bien: "b", gia_tri: "20" }, than: [] },
      { id: "3", ma: "pheptinh", o: { trai: "a", phep: "+", phai: "b" }, than: [] }
    ]
  },
  // 13. Phép tính có biến chưa gán
  {
    name: "13_pheptinh_chua_gan",
    tree: [
      { id: "1", ma: "pheptinh", o: { trai: "a_chua_co", phep: "+", phai: "1" }, than: [] }
    ]
  },
  // 14. Thẻ nếu kèm ngược lại hợp lệ
  {
    name: "14_neu_nguoc_lai_hop_le",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "n", gia_tri: "4" }, than: [] },
      { id: "2", ma: "neu", o: { dieu_kien: "n % 2 == 0" }, than: [
        { id: "3", ma: "in_ra", o: { noi_dung: '"Chan"' }, than: [] }
      ]},
      { id: "4", ma: "nguoc_lai", o: {}, than: [
        { id: "5", ma: "in_ra", o: { noi_dung: '"Le"' }, than: [] }
      ]}
    ]
  },
  // 15. Biến chưa gán trong điều kiện lap_khi
  {
    name: "15_lap_khi_bien_dieu_kien_chua_gan",
    tree: [
      { id: "1", ma: "lap_khi", o: { dieu_kien: "chua_gan > 0" }, than: [
        { id: "2", ma: "in_ra", o: { noi_dung: '"loop"' }, than: [] }
      ]}
    ]
  },
  // 16. Biến chưa gán trong dãy lap_moi
  {
    name: "16_lap_moi_day_chua_gan",
    tree: [
      { id: "1", ma: "lap_moi", o: { bien: "x", day: "day_chua_co" }, than: [
        { id: "2", ma: "in_ra", o: { noi_dung: "x" }, than: [] }
      ]}
    ]
  },
  // 17. Gọi hàm không có biến
  {
    name: "17_goi_ham_hop_le",
    tree: [
      { id: "1", ma: "goi_ham", o: { ten_ham: "khoi_dong", doi_so: '"ngay"' }, than: [] }
    ]
  },
  // 18. Thẻ mã thô hợp lệ
  {
    name: "18_ma_tho_hop_le",
    tree: [
      { id: "1", ma: "ma_tho", o: { nguyen_van: "import os\nprint(os.name)" }, than: [] }
    ]
  },
  // 19. Vòng lặp lap_khi hợp lệ (có biến thay đổi trong thân)
  {
    name: "19_lap_khi_hop_le_co_thay_doi",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "dem", gia_tri: "5" }, than: [] },
      { id: "2", ma: "lap_khi", o: { dieu_kien: "dem > 0" }, than: [
        { id: "3", ma: "in_ra", o: { noi_dung: "dem" }, than: [] },
        { id: "4", ma: "gan", o: { ten_bien: "dem", gia_tri: "dem - 1" }, than: [] }
      ]}
    ]
  },
  // 20. Hàm nhiều tham số hợp lệ
  {
    name: "20_ham_nhieu_tham_so",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "tinh_tong_3", tham_so: "x, y, z" }, than: [
        { id: "2", ma: "tra_ve", o: { gia_tri: "x + y + z" }, than: [] }
      ]},
      { id: "3", ma: "in_ra", o: { noi_dung: "tinh_tong_3(1, 2, 3)" }, than: [] }
    ]
  },
  // 21. Thân rỗng trong thẻ ham
  {
    name: "21_than_rong_ham",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "rong", tham_so: "" }, than: [] }
    ]
  },
  // 22. Thân rỗng trong thẻ lap_moi
  {
    name: "22_than_rong_lap_moi",
    tree: [
      { id: "1", ma: "lap_moi", o: { bien: "i", day: "range(5)" }, than: [] }
    ]
  },
  // 23. Tham số hàm chữ ký thật từ kho (có chú thích kiểu, giá trị mặc định, *)
  {
    name: "23_tham_so_that_tu_kho",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "_tinh_cay", tham_so: "nut: ast.AST, an: tuple[str, float] | None = None" }, than: [
        { id: "2", ma: "tra_ve", o: { gia_tri: "nut if an is None else None" }, than: [] }
      ]},
      { id: "3", ma: "ham", o: { ten_ham: "tinh_giup", tham_so: "text: str, *, now: datetime | None = None" }, than: [
        { id: "4", ma: "tra_ve", o: { gia_tri: "text if now is None else text" }, than: [] }
      ]},
      { id: "5", ma: "ham", o: { ten_ham: "sinh_khay", tham_so: 'goc: Path, thu_muc: tuple[str, ...] = ("core", "interface", "tools")' }, than: [
        { id: "6", ma: "tra_ve", o: { gia_tri: "goc if len(thu_muc) > 0 else None" }, than: [] }
      ]},
      { id: "7", ma: "ham", o: { ten_ham: "remember", tham_so: "text: str, *, confirmed_by_user: bool = False" }, than: [
        { id: "8", ma: "tra_ve", o: { gia_tri: "text if confirmed_by_user else None" }, than: [] }
      ]},
      { id: "9", ma: "ham", o: { ten_ham: "sinh_ma_python", tham_so: "nodes: List[TheNode], indent_level: int = 0" }, than: [
        { id: "10", ma: "tra_ve", o: { gia_tri: "nodes if indent_level >= 0 else []" }, than: [] }
      ]}
    ]
  },
  // 24. Import thật từ kho trong thẻ ma_tho
  {
    name: "24_import_that_tu_kho",
    tree: [
      { id: "1", ma: "ma_tho", o: { nguyen_van: "from urllib.parse import urlsplit, urlunsplit\nimport hashlib, hmac, json, os, secrets, tempfile\nfrom pathlib import Path" }, than: [] },
      { id: "2", ma: "gan", o: { ten_bien: "u", gia_tri: 'urlsplit("http://localhost:8088")' }, than: [] },
      { id: "3", ma: "gan", o: { ten_bien: "h", gia_tri: 'hashlib.sha256(b"aura").hexdigest()' }, than: [] },
      { id: "4", ma: "in_ra", o: { noi_dung: 'json.dumps({"path": str(Path("."))})' }, than: [] }
    ]
  },
  // 25. Hàm tự định nghĩa thật được gọi trong cùng tệp
  {
    name: "25_ham_tu_dinh_nghia_that",
    tree: [
      { id: "1", ma: "ham", o: { ten_ham: "bo_dau", tham_so: "s: str" }, than: [
        { id: "2", ma: "tra_ve", o: { gia_tri: "s.strip()" }, than: [] }
      ]},
      { id: "3", ma: "ham", o: { ten_ham: "_khop", tham_so: "s: str, pat: str" }, than: [
        { id: "4", ma: "gan", o: { ten_bien: "clean_s", gia_tri: "bo_dau(s)" }, than: [] },
        { id: "5", ma: "tra_ve", o: { gia_tri: "pat in clean_s" }, than: [] }
      ]},
      { id: "6", ma: "gan", o: { ten_bien: "kq", gia_tri: '_khop("xin chao", "chao")' }, than: [] },
      { id: "7", ma: "in_ra", o: { noi_dung: "kq" }, than: [] }
    ]
  },
  // 26. Biến comprehension và vòng lặp thật
  {
    name: "26_bien_comprehension_va_vong_lap_that",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "raw_text", gia_tri: '"a, b, c"' }, than: [] },
      { id: "2", ma: "gan", o: { ten_bien: "items", gia_tri: '[p.strip() for p in raw_text.split(",") if p.strip()]' }, than: [] },
      { id: "3", ma: "lap_moi", o: { bien: "item", day: "items" }, than: [
        { id: "4", ma: "in_ra", o: { noi_dung: "item" }, than: [] }
      ]}
    ]
  },
  // 27. Builtin mở rộng thật của Python
  {
    name: "27_builtin_mo_rong_that",
    tree: [
      { id: "1", ma: "gan", o: { ten_bien: "s", gia_tri: "frozenset([1, 2, 3])" }, than: [] },
      { id: "2", ma: "gan", o: { ten_bien: "has_len", gia_tri: 'hasattr(s, "__len__")' }, than: [] },
      { id: "3", ma: "gan", o: { ten_bien: "attr_val", gia_tri: 'getattr(s, "__doc__", "")' }, than: [] },
      { id: "4", ma: "in_ra", o: { noi_dung: "isinstance(s, frozenset)" }, than: [] }
    ]
  }
];

function runParityTest() {
  console.log(`=== BẮT ĐẦU CHẠY KIỂM THỬ ĐỐI CHIẾU PARITY JS <-> PYTHON (${TEST_CASES.length} TEST CASES) ===`);
  const pythonPath = path.resolve(__dirname, '..', 'venv', 'Scripts', 'python.exe');
  
  let passedCount = 0;
  let totalCases = TEST_CASES.length;

  const pythonRunner = `
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from core.the_v1 import TheNode, kiem_tra_cay_the

raw = sys.stdin.read()
data = json.loads(raw)
nodes = [TheNode.from_dict(item) for item in data]
res = kiem_tra_cay_the(nodes)
out = {
    "hop_le": res.hop_le,
    "so_loi_do": res.so_loi_do,
    "so_canh_bao_vang": res.so_canh_bao_vang,
    "danh_sach": [
        {"muc_do": d.muc_do, "ma_loi": d.ma_loi, "thong_diep": d.thong_diep}
        for d in res.danh_sach
    ],
    "so_lan_dung_the": res.so_lan_dung_the
}
print(json.dumps(out, ensure_ascii=False))
`;

  const { spawnSync } = require('child_process');

  for (const tc of TEST_CASES) {
    // 1. Chạy JS Validator
    const jsResult = kiemTraCayThe(tc.tree);

    // 2. Chạy Python Validator
    const inputJson = JSON.stringify(tc.tree);
    const proc = spawnSync(pythonPath, ['-c', pythonRunner], {
      input: inputJson,
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: path.resolve(__dirname, '..') }
    });

    if (proc.status !== 0) {
      console.error(`Python error on ${tc.name}:`, proc.stderr);
      process.exit(1);
    }

    const pyResult = JSON.parse(proc.stdout.trim());

    // 3. So sánh kết quả
    const hopLeMatch = jsResult.hop_le === pyResult.hop_le;
    const soDoMatch = jsResult.so_loi_do === pyResult.so_loi_do;
    const soVangMatch = jsResult.so_canh_bao_vang === pyResult.so_canh_bao_vang;

    // So sánh danh sách mã lỗi
    const jsMaLoi = jsResult.danh_sach.map(d => `${d.muc_do}:${d.ma_loi}`).sort();
    const pyMaLoi = pyResult.danh_sach.map(d => `${d.muc_do}:${d.ma_loi}`).sort();
    const maLoiMatch = JSON.stringify(jsMaLoi) === JSON.stringify(pyMaLoi);

    // So sánh bộ đếm xN
    const xNMatch = JSON.stringify(jsResult.so_lan_dung_the) === JSON.stringify(pyResult.so_lan_dung_the);

    if (hopLeMatch && soDoMatch && soVangMatch && maLoiMatch && xNMatch) {
      console.log(`  [PASS] ${tc.name}: hop_le=${jsResult.hop_le}, do=${jsResult.so_loi_do}, vang=${jsResult.so_canh_bao_vang}`);
      passedCount++;
    } else {
      // 25/08: THONG BAO PHAI CHI RA CHO LECH.
      //
      // Ban cu in dung hai dong hop_le/do/vang/loi roi bao "KHONG KHOP".
      // Hom nay them 5 the vao JS ma chua them vao Python: cua do dung, nhung
      // hai dong in ra GIONG HET NHAU — vi cho lech nam o `so_lan_dung_the`,
      // thu khong he duoc in. Mat mot luot doc ma nguon cua chinh bo test moi
      // biet no dang so cai gi.
      //
      // Cung ho voi §4 "phan quyet phai di kem phep do tao ra no".
      const lech = [];
      if (!hopLeMatch) lech.push(`hop_le: JS=${jsResult.hop_le} PY=${pyResult.hop_le}`);
      if (!soDoMatch) lech.push(`so_loi_do: JS=${jsResult.so_loi_do} PY=${pyResult.so_loi_do}`);
      if (!soVangMatch) lech.push(`so_canh_bao_vang: JS=${jsResult.so_canh_bao_vang} PY=${pyResult.so_canh_bao_vang}`);
      if (!maLoiMatch) {
        lech.push(`ma_loi:
         chi co JS: ${JSON.stringify(jsMaLoi.filter(x => !pyMaLoi.includes(x)))}` +
                  `
         chi co PY: ${JSON.stringify(pyMaLoi.filter(x => !jsMaLoi.includes(x)))}`);
      }
      if (!xNMatch) {
        const kJS = Object.keys(jsResult.so_lan_dung_the || {});
        const kPY = Object.keys(pyResult.so_lan_dung_the || {});
        const theChiJS = kJS.filter(k => !kPY.includes(k));
        const thePY = kPY.filter(k => !kJS.includes(k));
        const soLech = kJS.filter(k => kPY.includes(k) &&
          jsResult.so_lan_dung_the[k] !== pyResult.so_lan_dung_the[k])
          .map(k => `${k}: JS=${jsResult.so_lan_dung_the[k]} PY=${pyResult.so_lan_dung_the[k]}`);
        const phan = [];
        if (theChiJS.length) phan.push(`THE CHI CO TRONG JS (chua them vao Python): ${theChiJS.join(', ')}`);
        if (thePY.length) phan.push(`THE CHI CO TRONG PYTHON (chua them vao JS): ${thePY.join(', ')}`);
        if (soLech.length) phan.push(`dem lech: ${soLech.join(' | ')}`);
        lech.push('so_lan_dung_the:\n         ' + phan.join('\n         '));
      }
      console.error(`  [FAIL] ${tc.name} KHONG KHOP GIUA JS VA PYTHON:`);
      lech.forEach(l => console.error(`     ${l}`));
      process.exit(1);
    }
  }

  console.log(`\n=== KẾT QUẢ: ${passedCount}/${totalCases} TEST CASES ĐỐI CHIẾU KHỚP 100% ===\n`);
}

runParityTest();
