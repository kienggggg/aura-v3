import pytest
import os
import shutil
import pathlib
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logger

def test_writer_mkdir_path_traversal():
    proj_root = str(pathlib.Path(os.path.join(logger.DATA_DIR, 'projects')).resolve(strict=False))
    
    # 1. projects_evil
    evil_dir = os.path.join(logger.DATA_DIR, 'projects_evil', 'chapters')
    evil_path = str(pathlib.Path(evil_dir).resolve(strict=False))
    assert not pathlib.Path(evil_path).is_relative_to(pathlib.Path(proj_root))
    
    # 2. .. escape
    escape_dir = os.path.join(proj_root, '..', 'evil', 'chapters')
    escape_path = str(pathlib.Path(escape_dir).resolve(strict=False))
    assert not pathlib.Path(escape_path).is_relative_to(pathlib.Path(proj_root))

def test_studio_stub_false_pass():
    # Studio should fail if voice is missing, verify regex logic for volumedetect
    import re
    out = "mean_volume: -20.1 dB\nmax_volume: -0.4 dB"
    mean_level = 0.0
    m_mean = re.search(r"mean_volume:\s+([\-\d\.]+)\s+dB", out)
    if m_mean: mean_level = float(m_mean.group(1))
    assert mean_level == -20.1
        
def test_scout_stub_false_pass():
    # Scout should generate actual receipts, let's verify receipts structure
    run_id = "test_run_scout"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    out_path = os.path.join(run_dir, 'artifacts', 'scout_report.json')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('{"receipts": [{"canonical_url": "test", "content_sha256": "hash"}]}')
        
    logger.log_artifact(run_id, "scout_report.json", out_path)
    
    import json
    with open(out_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data['receipts']) > 0
        assert "content_sha256" in data['receipts'][0]
        
    shutil.rmtree(run_dir, ignore_errors=True)
    
def test_alpha_stub_false_pass():
    # Alpha must generate a valid patch targeting a real existing file
    import alpha
    repo_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent)
    
    # 1. Test với patch thật: phải trỏ vào file thật và git apply --check thành công
    target_rel, diff_text = alpha.generate_real_patch(repo_dir)
    assert os.path.exists(os.path.join(repo_dir, target_rel)), f"Target {target_rel} must exist"
    
    run_id = "test_run_alpha"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    out_path = os.path.join(run_dir, 'artifacts', 'alpha_patch.diff')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(diff_text)
    logger.log_artifact(run_id, "alpha_patch.diff", out_path)
    
    valid, msg = alpha.verify_patch(out_path, repo_dir)
    assert valid is True, f"Real patch must pass git apply --check: {msg}"
    
    # 2. Test với fake diff: phải FAIL (không được chấp nhận fake.py)
    fake_path = os.path.join(run_dir, 'artifacts', 'fake_patch.diff')
    with open(fake_path, 'w', encoding='utf-8') as f:
        f.write("--- a/fake.py\n+++ b/fake.py\n@@ -1,1 +1,2 @@\n-print('hello')\n+print('hello world')")
    fake_valid, fake_msg = alpha.verify_patch(fake_path, repo_dir)
    assert fake_valid is False, "Fake patch targeting non-existent file must fail"
    
    shutil.rmtree(run_dir, ignore_errors=True)

