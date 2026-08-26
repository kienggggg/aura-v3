import ast
from pathlib import Path
from core.the_cst import doc_tep_py_sang_cay_the
from core.the_v1 import sinh_ma_python

def test_sinh_ma_python_tat_ca_22_tep_core_parse_duoc():
    """Tat ca 22 tep trong core/ sau khi sinh_ma_python tu cay the CST deu phai parse duoc bang ast.parse."""
    core_files = sorted(Path("core").glob("*.py"))
    assert len(core_files) >= 20
    
    for p in core_files:
        rec = doc_tep_py_sang_cay_the(p)
        gen_code = sinh_ma_python(rec.tree)
        gen_ast = ast.parse(gen_code)
        assert gen_ast is not None, f"Tep {p.name} sinh ma rong hoac khong parse duoc"

def test_bao_toan_kieu_tra_ve_ham():
    """Tat ca cac ham co chu thich kieu tra ve trong tep goc khong duoc bi mat khi sinh ma."""
    core_files = sorted(Path("core").glob("*.py"))
    
    for p in core_files:
        orig_ast = ast.parse(p.read_text(encoding="utf-8"))
        orig_fns = {
            n.name: ast.unparse(n.returns)
            for n in ast.walk(orig_ast)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None
        }
        
        rec = doc_tep_py_sang_cay_the(p)
        gen_code = sinh_ma_python(rec.tree)
        gen_ast = ast.parse(gen_code)
        gen_fns = {
            n.name: ast.unparse(n.returns)
            for n in ast.walk(gen_ast)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None
        }
        
        for fn_name, ret_type in orig_fns.items():
            assert fn_name in gen_fns, f"[{p.name}] Ham '{fn_name}' bi mat chu ky tra ve '{ret_type}'!"
            assert gen_fns[fn_name] == ret_type, f"[{p.name}] Ham '{fn_name}' bi lech kieu: goc '{ret_type}' vs sinh '{gen_fns[fn_name]}'"


def test_sinh_lai_giu_nguyen_tep_don_gian_tung_byte():
    """Tệp kiểu người mới học phải sinh lại GIỐNG HỆT bản gốc, từng byte.

    26/08/2026. Đây là điều kiện để mở hàng rào "không được thêm/bớt thẻ":
    `interface/the_api.py::_sinh_lai_duoc_tron_ven` chỉ cho sinh lại cả tệp
    khi sinh lại cây GỐC ra đúng bản gốc. Hỏng phép này thì hàng rào đóng sập
    lại với mọi tệp, và người mới học lại không thêm được thẻ nào vào bài của
    mình — im lặng, vì không có gì nổ.

    Trước bản vá cùng ngày, `sinh_ma_python` nối các thẻ bằng đúng một xuống
    dòng nên MỌI dòng trống giữa các câu lệnh biến mất, và chuỗi trả về không
    có xuống dòng cuối tệp. Đo vòng tròn khi ấy: 0/33 tệp giống bản gốc.

    Ba ca dưới là ba thứ đã hỏng thật: dòng trống, xuống dòng cuối, và quy
    ước CRLF của Windows — nơi app này chạy.
    """
    from core.the_v1 import sinh_ma_python_ca_tep
    from core.the_cst import doc_chuoi_py_sang_cay_the

    CAC_CA = {
        "hai dòng trống giữa hàm và lời gọi": (
            "def chao(ten):\n"
            '    print("Xin chao", ten)\n'
            "\n"
            "\n"
            'chao("Kien")\n'
        ),
        "một dòng trống, có chú thích đầu tệp": (
            "# Bai 1\n"
            "x = 10\n"
            "\n"
            "print(x)\n"
        ),
        "không dòng trống nào": (
            "for i in range(5):\n"
            "    print(i)\n"
        ),
    }

    for ten_ca, goc in CAC_CA.items():
        for nhan_xd, nguon in (("LF", goc), ("CRLF", goc.replace("\n", "\r\n"))):
            rec = doc_chuoi_py_sang_cay_the(nguon, "bai_tap.py")
            moi = sinh_ma_python_ca_tep(rec.tree, rec.newline)
            assert moi == nguon, (
                f"[{ten_ca} · {nhan_xd}] sinh lại KHÁC bản gốc.\n"
                f"  gốc  : {nguon!r}\n"
                f"  sinh : {moi!r}"
            )
