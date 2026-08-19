import os
import json
import hashlib
import time
from datetime import datetime, timezone
import uuid
import subprocess
import shutil

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'evidence_sprint'))
RUNS_DIR = os.path.join(DATA_DIR, 'runs')

def get_current_run_dir(run_id: str) -> str:
    return os.path.join(RUNS_DIR, run_id)

def init_run(model_name: str, config: dict, input_files: list = None) -> str:
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    run_dir = get_current_run_dir(run_id)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)

    # artifacts.json PHAI co ngay tu dau, ke ca khi rong.
    #
    # Truoc 18/08 no chi ra doi khi log_artifact() chay trot lot. Ket qua: 8/8
    # luot hong deu THIEU artifacts.json — mot trong 5 tep bat buoc cua
    # KY_LUAT_THUC_THI.md chuong I muc 1. Omega bao thanh 8 viec rieng, trong
    # khi goc chi la mot: hong thi thoat som, khong kip ghi.
    #
    # "{}" la mot cau DUNG: luot nay chua khai hien vat nao. Con tep VANG thi
    # mo ho — khong biet la khong co hien vat, hay bo ghi da chet giua chung.
    # Vang mat khong phai bang chung.
    with open(os.path.join(run_dir, 'artifacts.json'), 'w', encoding='utf-8') as f:
        json.dump({}, f)


    git_commit = "unknown"
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=os.path.dirname(__file__)).decode('utf-8').strip()
    except Exception:
        pass
        
    input_hashes = {}
    if input_files:
        for fpath in input_files:
            if os.path.exists(fpath):
                # Snapshot input file
                fname = os.path.basename(fpath)
                dest_path = os.path.join(run_dir, 'raw', fname)
                shutil.copy2(fpath, dest_path)
                input_hashes[fname] = calculate_file_sha256(dest_path)

    import psutil
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    ollama_proc = []
    for p in psutil.process_iter(['name', 'memory_info']):
        try:
            if p.info['name'] and 'ollama' in p.info['name'].lower():
                ollama_proc.append({"name": p.info['name'], "rss_mb": p.info['memory_info'].rss / (1024 * 1024)})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    sys_snapshot = {
        "ram_available_mb": mem.available / (1024 * 1024),
        "swap_free_mb": swap.free / (1024 * 1024),
        "ollama_processes": ollama_proc
    }

    # Calculate config hash
    import hashlib
    config_canon = json.dumps(config, sort_keys=True).encode('utf-8')
    config_sha256 = hashlib.sha256(config_canon).hexdigest()
    
    # Prompt is typically hashed later, but we add placeholder
    
    manifest = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit,
        "model": model_name,
        "model_digest": "sha256:unknown",
        "config": config,
        "config_sha256": config_sha256,
        "prompt_sha256": None,
        "sys_snapshot": sys_snapshot,
        "input_hashes": input_hashes,
        "num_ctx": config.get("num_ctx", 4096),
        "max_output": config.get("num_predict", 4096),
        "timeout": config.get("timeout", 300),
        "attempts": 1
    }
    
    with open(os.path.join(run_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    open(os.path.join(run_dir, 'commands.jsonl'), 'a').close()
    
    return run_id

def update_manifest(run_id: str, updates: dict):
    run_dir = get_current_run_dir(run_id)
    manifest_path = os.path.join(run_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        manifest.update(updates)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

def log_command(run_id: str, entrypoint: str, exit_code: int, wall_time_ms: int, peak_ram_mb: float = None):
    run_dir = get_current_run_dir(run_id)
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "entrypoint": entrypoint,
        "exit_code": exit_code,
        "wall_time_ms": wall_time_ms,
        "peak_ram_mb": peak_ram_mb
    }
    with open(os.path.join(run_dir, 'commands.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def log_artifact(run_id: str, artifact_name: str, file_path: str, artifact_type: str = "output"):
    run_dir = get_current_run_dir(run_id)
    artifacts_dir = os.path.join(run_dir, 'artifacts')
    
    import pathlib
    file_path_resolved = str(pathlib.Path(file_path).resolve(strict=False))
    artifacts_dir_resolved = str(pathlib.Path(artifacts_dir).resolve(strict=False))
    
    if not os.path.exists(file_path_resolved):
        raise ValueError(f"Artifact {file_path_resolved} does not exist.")
    if not os.path.isfile(file_path_resolved):
        raise ValueError(f"Artifact {file_path_resolved} is not a regular file.")
    if os.path.getsize(file_path_resolved) == 0:
        raise ValueError(f"Artifact {file_path_resolved} is empty (0 bytes).")
        
    # Check if file is inside the artifacts folder of the run
    if not pathlib.Path(file_path_resolved).is_relative_to(pathlib.Path(artifacts_dir_resolved)):
        raise ValueError(f"Artifact {file_path_resolved} is outside run artifacts directory {artifacts_dir_resolved}.")

    artifacts_file = os.path.join(run_dir, 'artifacts.json')
    artifacts = {}
    if os.path.exists(artifacts_file):
        with open(artifacts_file, 'r', encoding='utf-8') as f:
            artifacts = json.load(f)
            
    sha256 = calculate_file_sha256(file_path_resolved)
    if not sha256:
        raise ValueError(f"Empty SHA256 for {file_path_resolved} is not allowed.")
    
    artifacts[artifact_name] = {
        "type": artifact_type,
        "path": file_path_resolved,
        "sha256": sha256
    }
    
    with open(artifacts_file, 'w', encoding='utf-8') as f:
        json.dump(artifacts, f, indent=2, ensure_ascii=False)

def log_metrics(run_id: str, status: str, reason: str = "", gate_results: dict = None):
    run_dir = get_current_run_dir(run_id)
    metrics = {
        "status": status,
        "reason": reason,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "gate_results": gate_results or {}
    }
    with open(os.path.join(run_dir, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    # Also update manifest with gate status
    gate_status = {}
    if gate_results:
        for k, v in gate_results.items():
            if isinstance(v, dict) and 'status' in v:
                gate_status[k] = v['status']
            else:
                gate_status[k] = "PASS" # for non-standard gates like studio/scout/alpha
    update_manifest(run_id, {"gate_status": gate_status})

def log_error(run_id: str, error_message: str, error_type: str = "UNKNOWN"):
    run_dir = get_current_run_dir(run_id)
    error_file = os.path.join(run_dir, 'raw', 'error.txt')
    
    import re
    filtered_msg = error_message
    patterns = [
        r'(Bearer\s+)[A-Za-z0-9\-\._~+]+', 
        r'(sk-[a-zA-Z0-9]{20,})', 
        r'(AIza[0-9A-Za-z-_]{35})',
        r'(xox[baprs]-[0-9a-zA-Z]{10,})'
    ]
    for pattern in patterns:
        filtered_msg = re.sub(pattern, r'\1[REDACTED]', filtered_msg)

    
    with open(error_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] {error_type}: {filtered_msg}\n")

def calculate_file_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_string_sha256(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
