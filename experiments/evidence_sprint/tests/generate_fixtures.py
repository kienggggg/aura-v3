import os
import json

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'evidence_sprint'))
RUNS_DIR = os.path.join(DATA_DIR, 'runs')

def setup_run(run_id, content, create_file=True):
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(os.path.join(run_dir, 'raw'), exist_ok=True)
    
    md_path = os.path.join(run_dir, 'ch03.md')
    if create_file:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    artifacts = {
        "ch03.md": {
            "type": "output",
            "path": md_path,
            "sha256": "fakehash"
        }
    }
    
    with open(os.path.join(run_dir, 'artifacts.json'), 'w', encoding='utf-8') as f:
        json.dump(artifacts, f)
        
    print(f"Created fixture: {run_id}")

if __name__ == '__main__':
    # Good content: ~1600 words, no mojibake, contains Kael and Lyra, no leaks
    good_content = "Đây là một đoạn văn bản dài. " * 300 + "\nKael đã gặp Lyra. " * 50
    setup_run("run_known_good", good_content)
    
    # Bad content: 50 words (too short), mojibake, no characters, prompt leaks
    bad_content = "BỐI CẢNH YÊU CẦU CỨNG \ufffd truyện bị lỗi font và quá ngắn. Kael"
    setup_run("run_known_bad", bad_content)
