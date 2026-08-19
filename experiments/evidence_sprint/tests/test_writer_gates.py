import os
import json
import pytest
import shutil
import hashlib
import pathlib
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logger
import gates

def get_target_run_dir():
    run_id = os.environ.get('TARGET_RUN_ID')
    if not run_id:
        pytest.fail("TARGET_RUN_ID environment variable is not set")
    run_dir = logger.get_current_run_dir(run_id)
    if not os.path.exists(run_dir):
        pytest.fail(f"Run directory not found: {run_dir}")
    return run_dir

def load_verified_run_artifact(artifact_name: str):
    run_dir = get_target_run_dir()
    artifacts_file = os.path.join(run_dir, 'artifacts.json')
    if not os.path.exists(artifacts_file):
        pytest.fail(f"Artifacts file not found: {artifacts_file}")
    with open(artifacts_file, 'r', encoding='utf-8') as f:
        artifacts = json.load(f)
        
    art_info = artifacts.get(artifact_name)
    if not art_info:
        pytest.fail(f"Artifact {artifact_name} not found in artifacts.json")
        
    file_path = str(pathlib.Path(art_info['path']).resolve(strict=False))
    artifacts_dir = str(pathlib.Path(os.path.join(run_dir, 'artifacts')).resolve(strict=False))
    
    if not pathlib.Path(file_path).is_relative_to(pathlib.Path(artifacts_dir)):
        pytest.fail(f"Artifact path {file_path} is outside the artifacts directory {artifacts_dir}.")
        
    if not os.path.exists(file_path):
        pytest.fail(f"Artifact file does not exist: {file_path}")
        
    if not os.path.isfile(file_path):
        pytest.fail(f"Artifact file is not a regular file: {file_path}")
        
    if os.path.getsize(file_path) == 0:
        pytest.fail(f"Artifact file is empty (0 bytes): {file_path}")
        
    actual_hash = logger.calculate_file_sha256(file_path)
    if actual_hash != art_info['sha256']:
        pytest.fail(f"SHA256 mismatch for {artifact_name}. Expected {art_info['sha256']}, got {actual_hash}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_snapshot_input(filename: str):
    run_dir = get_target_run_dir()
    path = os.path.join(run_dir, 'raw', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_run_status():
    run_dir = get_target_run_dir()
    metrics_file = os.path.join(run_dir, 'metrics.json')
    with open(metrics_file, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
        
    status = metrics.get('status')
    if os.environ.get('EXPECTED_STATUS'):
        assert status == os.environ.get('EXPECTED_STATUS')

def test_writer_gates():
    content = load_verified_run_artifact("ch03.md")
    
    # Check that input snapshots exist and load them
    run_dir = get_target_run_dir()
    bible_path = os.path.join(run_dir, 'raw', 'bible.json')
    style_path = os.path.join(run_dir, 'raw', 'style_card.json')
    
    results = gates.run_all_gates(content, bible_path, style_path)
    
    for k, v in results.items():
        assert v['status'] == "PASS", f"Gate {k} failed: {v['msg']}"

def test_logger_zero_byte(tmp_path):
    run_id = "test_run_zero"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    fpath = os.path.join(run_dir, 'artifacts', 'zero.md')
    open(fpath, 'w').close()
    
    with pytest.raises(ValueError, match="is empty"):
        logger.log_artifact(run_id, "zero", fpath)
        
    shutil.rmtree(run_dir, ignore_errors=True)

def test_logger_outside_path(tmp_path):
    run_id = "test_run_out"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    fpath = os.path.join(tmp_path, 'outside.md')
    with open(fpath, 'w') as f:
        f.write("content")
        
    with pytest.raises(ValueError, match="outside run artifacts directory"):
        logger.log_artifact(run_id, "out", fpath)
        
    shutil.rmtree(run_dir, ignore_errors=True)

def test_hash_mismatch(tmp_path):
    run_id = "test_run_hash"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    fpath = os.path.join(run_dir, 'artifacts', 'hash.md')
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write("content")
        
    logger.log_artifact(run_id, "hash", fpath)
    
    # Tamper with the file
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write("tampered")
        
    os.environ['TARGET_RUN_ID'] = run_id
    with pytest.raises(pytest.fail.Exception, match="SHA256 mismatch"):
        load_verified_run_artifact("hash")
        
    shutil.rmtree(run_dir, ignore_errors=True)
    
def test_missing_artifact():
    run_id = "test_run_missing"
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    
    fpath = os.path.join(run_dir, 'artifacts', 'missing.md')
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write("content")
        
    logger.log_artifact(run_id, "missing.md", fpath)
    
    # Delete the file so it becomes missing
    os.remove(fpath)
        
    os.environ['TARGET_RUN_ID'] = run_id
    with pytest.raises(pytest.fail.Exception, match="Artifact file does not exist"):
        load_verified_run_artifact("missing.md")
        
    shutil.rmtree(run_dir, ignore_errors=True)
