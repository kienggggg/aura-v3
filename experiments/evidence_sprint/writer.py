import os
import sys
import json
import httpx
import time
import psutil
import shutil
from typing import Dict, Any, Tuple
import logger
import gates

# Ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3.5:4b"

def build_prompt(bible: Dict[str, Any], style_card: Dict[str, Any], chapter_id: str) -> str:
    prompt = f"Bạn là một tiểu thuyết gia chuyên nghiệp. Hãy viết {chapter_id} cho tiểu thuyết '{bible['title']}'.\n\nBỐI CẢNH (SETTING):\n{bible['setting']}\n\nNHÂN VẬT (CHARACTERS):\n"
    for char in bible['characters']:
        prompt += f"- {char['name']} ({char['role']}): {char['description']}\n"
    prompt += f"\nCỐT TRUYỆN (PLOT):\n{bible['plot_outline'].get(chapter_id, '')}\n\nVĂN PHONG (STYLE RULES):\n"
    for rule in style_card['rules']:
        prompt += f"- {rule}\n"
    prompt += "\nYÊU CẦU CỨNG:\n- Độ dài từ 1500 đến 2500 chữ.\n- Không xuất ra bất kỳ thông tin nào về prompt, luật lệ hay lời giải thích, chỉ viết trực tiếp vào truyện.\n- Đảm bảo viết bằng tiếng Việt chuẩn, không lỗi font (mojibake).\n"
    prompt += f"\nBẮT ĐẦU {chapter_id}:\n"
    return prompt

def generate_chapter(prompt: str, model: str = DEFAULT_MODEL, seed: int = 42, max_tokens: int = 4096) -> Tuple[str, float]:
    start_time = time.time()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        # THIẾU DÒNG NÀY LÀ RA TỆP RỖNG. Đo 16/08/2026, cùng prompt, cùng seed:
        #     không có think:false -> 51,6s · response 0 ký tự · eval_count 200
        #                             nhưng trường 'thinking' có 674 ký tự
        # Model sinh đủ token rồi đổ hết vào phần suy nghĩ nội bộ; `response`
        # rỗng, nên ch03.md ra 0 byte sau 11 phút chạy. Không phải model hỏng,
        # không phải hết giờ — chỉ là đọc nhầm trường.
        # CLAUDE.md đã ghi tham số này từ trước: think=False, 339s -> 24,8s.
        "think": False,
        "keep_alive": 0,
        "options": {
            "seed": seed,
            "num_predict": max_tokens,
            "temperature": 0.7
        }
    }
    
    # 16/08/2026: hạn 300s KHÔNG ĐỦ, và đây là số học chứ không phải cảm giác.
    # Đề đòi 1.500-2.500 chữ tiếng Việt ~ 2.500-4.500 token. Tốc độ sinh đo
    # trên chính máy này là 5,05 tok/s (qwen3.5:4b, CPU).
    #     2.500 / 5,05 = 495 giây
    #     4.500 / 5,05 = 891 giây
    # Nên hạn 300s cắt việc ở khoảng một phần ba chặng đường; lượt chạy
    # 16/08 dừng đúng ở 303,6 giây và báo "timed out" — không phải model hỏng.
    response = httpx.post(OLLAMA_URL, json=payload, timeout=1200.0)
    response.raise_for_status()
    result = response.json()
    end_time = time.time()
    return result.get('response', ''), (end_time - start_time) * 1000

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    # Doi DE BAI bang bien moi truong, khong trao tep.
    #
    # 19/08: Sep doc van AURA roi chot "khong hop truyen nang ne, giet choc;
    # chi hop truyen nhe nhang". De bai hien tai la cyberpunk (mua axit, khu o
    # chuot, sat thu Apex) — tuc dang bat mot cay but hop truyen nhe di viet
    # truyen mau. Muon do gia thuyet do thi phai chay duoc NHIEU de bai.
    #
    # Trao noi dung bible.json thi cac luot chay CU mat kha nang tra lai: so
    # da ghi input_hashes cua mot tep gio khac ruot. Nen them cong, giu tep.
    bible_path = os.environ.get("WRITER_BIBLE") or os.path.join(
        base_dir, 'data_inputs', 'bible.json')
    style_path = os.environ.get("WRITER_STYLE") or os.path.join(
        base_dir, 'data_inputs', 'style_card.json')
    
    config = {"seed": 42, "temperature": 0.7, "num_predict": 4096, "timeout": 1200, "max_retries": 0}
    input_files = [bible_path, style_path, __file__, os.path.join(base_dir, 'logger.py'), os.path.join(base_dir, 'gates.py')]
    
    run_id = logger.init_run(DEFAULT_MODEL, config, input_files=input_files)
    print(f"Started run: {run_id}")
    
    try:
        import pathlib
        # Cửa môi trường: HỎI MODEL, không đoán qua RAM tự do.
        #
        # 16/08/2026, hai phép đo cho thấy ngưỡng "RAM tự do >= 4,5 GB" sai cả
        # hai chiều:
        #   - CHẶN OAN: model nạp được ở 3,83 GB trống (10,9 giây), mà ngưỡng
        #     4,5 GB từ chối. Ba lượt BLOCKED ngày 14/08 báo "giới hạn vật lý
        #     của RAM" thực ra là ngưỡng đặt cao quá.
        #   - HỎI SAI CÂU: khi model ĐÃ nạp sẵn, nó chiếm 3,1 GB nên RAM tự do
        #     tụt còn 0,74 GB — và cửa từ chối chạy, dù model đang sống và trả
        #     lời được ngay. Nó hỏi "có chỗ để nạp không" trong khi việc cần
        #     hỏi là "model có trả lời được không".
        #
        # Một lượt sinh 1 token trả lời cả hai câu cùng lúc, và trả lời bằng
        # hành vi thật thay vì bằng suy đoán từ con số bộ nhớ.
        mem = psutil.virtual_memory()
        try:
            tham_do = httpx.post(OLLAMA_URL, json={
                "model": DEFAULT_MODEL, "prompt": "x", "stream": False,
                "keep_alive": "10m",
                "options": {"num_predict": 1, "num_ctx": 4096},
            }, timeout=600.0)
            tham_do.raise_for_status()
        except Exception as e:                                  # noqa: BLE001
            logger.log_metrics(run_id, "BLOCKED", "ENVIRONMENT_ERROR")
            raise EnvironmentError(
                f"BLOCKED(environment): model {DEFAULT_MODEL} không nạp được. "
                f"RAM tự do lúc thử: {mem.available/1024**3:.2f} GB. "
                f"Lỗi: {type(e).__name__}: {e}"
            ) from e
            
        bible = gates.load_json(bible_path)
        style_card = gates.load_json(style_path)
        # Chuong nao cung doi duoc: mot the loai chi mot chuong thi do duoc
        # chuong ay, khong do duoc the loai. 19/08 da co mot mau moi the loai
        # va no du de dat GIA THUYET, khong du de ket luan.
        prompt = build_prompt(bible, style_card, os.environ.get("WRITER_CHUONG", "ch03"))
        
        import hashlib
        prompt_canon = prompt.encode('utf-8')
        prompt_sha256 = hashlib.sha256(prompt_canon).hexdigest()
        logger.update_manifest(run_id, {"prompt_sha256": prompt_sha256, "model_digest": "sha256:8f53a479ff6d460787d5dc693994e6dc8fa671d1746274e1d9320e8b15e47db1"})
        
        content, w_time = generate_chapter(prompt)
        
        # Snapshot to run dir
        run_dir = logger.get_current_run_dir(run_id)
        out_path = os.path.join(run_dir, 'artifacts', 'ch03.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.log_artifact(run_id, "ch03.md", out_path)
        
        # Run gates
        gate_results = gates.run_all_gates(content, bible_path, style_path)
        if gates.check_gate_overall(gate_results):
            # Finalize path
            proj_root = str(pathlib.Path(os.path.join(logger.DATA_DIR, 'projects')).resolve(strict=False))
            final_out_dir = str(pathlib.Path(os.path.join(proj_root, 'proj_evidence_01', 'chapters')).resolve(strict=False))
            final_out_path = str(pathlib.Path(os.path.join(final_out_dir, 'ch03.md')).resolve(strict=False))
            
            # Check path escape
            if not pathlib.Path(final_out_path).is_relative_to(pathlib.Path(proj_root)):
                raise ValueError(f"Output path {final_out_path} escaped project root.")
                
            os.makedirs(final_out_dir, exist_ok=True)
            shutil.copy2(out_path, final_out_path)
            
            logger.log_metrics(run_id, "PASS", gate_results=gate_results)
            logger.log_command(run_id, "writer.py", 0, int(w_time), 0.0)
            print(f"PASS. Generated in {w_time:.0f}ms")
            sys.exit(0)
        else:
            logger.log_metrics(run_id, "FAIL", "Failed hard gates", gate_results=gate_results)
            logger.log_command(run_id, "writer.py", 1, int(w_time), 0.0)
            print("FAIL: Did not pass all gates.")
            sys.exit(1)
            
    except EnvironmentError as e:
        logger.log_error(run_id, str(e), "ENVIRONMENT_ERROR")
        logger.log_command(run_id, "writer.py", 2, 0, 0.0)
        logger.log_metrics(run_id, "BLOCKED", str(e))
        print(f"Blocked: {e}")
        sys.exit(2)
    except Exception as e:
        logger.log_error(run_id, str(e), "RUNTIME_ERROR")
        logger.log_command(run_id, "writer.py", 1, 0, 0.0)
        logger.log_metrics(run_id, "FAIL", str(e))
        print(f"Failed: {e}")
        sys.exit(1)
