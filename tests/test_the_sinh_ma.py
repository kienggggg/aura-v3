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
