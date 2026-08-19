import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logger
import gates

def setup_run(run_id, content, create_file=True):
    run_dir = logger.get_current_run_dir(run_id)
    os.makedirs(os.path.join(run_dir, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
    
    # Need to fake snapshots
    bible_path = os.path.join(run_dir, 'raw', 'bible.json')
    style_path = os.path.join(run_dir, 'raw', 'style_card.json')
    import shutil
    src_bible = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_inputs', 'bible.json'))
    src_style = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_inputs', 'style_card.json'))
    shutil.copy2(src_bible, bible_path)
    shutil.copy2(src_style, style_path)
    
    md_path = os.path.join(run_dir, 'artifacts', 'ch03.md')
    if create_file:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    try:
        logger.log_artifact(run_id, "ch03.md", md_path)
    except Exception as e:
        print(f"[{run_id}] Failed to log artifact intentionally: {e}")
        # Note: Do NOT write fake JSON anymore

    gate_results = gates.run_all_gates(content, bible_path, style_path)
    status = "PASS" if gates.check_gate_overall(gate_results) else "FAIL"
    logger.log_metrics(run_id, status, gate_results=gate_results)
    
    print(f"Created fixture: {run_id}")

if __name__ == '__main__':
    # Good content: ~1600 words, no mojibake, contains Kael and Lyra, no leaks
    good_content = "Đây là một đoạn văn bản dài. " * 300 + "\nKael đã gặp Lyra. " * 50
    setup_run("run_known_good", good_content)
    
    setup_run("run_bad_word_count_low", "Kael Lyra " * 10)
    setup_run("run_bad_word_count_high", "Kael Lyra " * 1500) # 3000 words
    setup_run("run_bad_mojibake", good_content + " \ufffd")
    setup_run("run_bad_control_char", good_content + " \x00")
    
    setup_run("run_bad_missing_char", "Đây là một đoạn văn bản dài. " * 300)
    setup_run("run_bad_prompt_leak", good_content + " BỐI CẢNH")
