import os
import sys
import json
import time
import subprocess
import logger
import hashlib
from PIL import Image, ImageDraw, ImageFont

def generate_sapi_tts(text, output_wav):
    text_file = "tts_text.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)
        
    ps_script = f"""
    $text = Get-Content '{text_file}' -Encoding UTF8 -Raw
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -match "Microsoft An" }}
    if (-not $voice) {{
        $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -match "Microsoft" }} | Select-Object -First 1
    }}
    if ($voice) {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
    }} else {{
        exit 1
    }}
    $synth.SetOutputToWaveFile('{output_wav}')
    $synth.Speak($text)
    """
    ps_file = "tts.ps1"
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_script)
    
    start_time = time.time()
    # BẮT lấy lời PowerShell nói. Bản cũ chạy trần, mọi lỗi mất sạch, rồi câu
    # `raise` phía dưới KHẲNG ĐỊNH nguyên nhân là "không thấy giọng Microsoft
    # An" cho BẤT KỲ mã thoát khác 0 nào — kể cả lỗi ghi tệp hay lỗi cú pháp.
    #
    # Hai lượt 14/08 vào sổ đúng câu đó, và nó dẫn người đọc đi tìm giọng nói
    # trong khi máy này chỉ có David với Zira và đường lui ở trên đã tự xử lý.
    # Một câu báo lỗi khẳng định thứ nó chưa đo thì tệ hơn là không báo gì.
    res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    tts_ms = int((time.time() - start_time) * 1000)
    os.remove(ps_file)
    if os.path.exists(text_file): os.remove(text_file)

    if res.returncode != 0:
        loi = ((res.stderr or "") + (res.stdout or "")).strip()[:300]
        raise Exception(
            f"TTS thất bại, PowerShell thoát {res.returncode}. "
            f"exit 1 = không có giọng Microsoft nào; mã khác = lỗi khác. "
            f"Lời PowerShell: {loi or '(không nói gì)'}")

    # Thoát 0 KHÁC có tiếng. SAPI ghi tệp rỗng khi văn bản rỗng, và một wav 0
    # byte đi tiếp thì chết ở tận cửa hiện vật với câu "empty (0 bytes)" —
    # cách chỗ hỏng thật ba bước.
    if not os.path.exists(output_wav) or os.path.getsize(output_wav) == 0:
        raise Exception(f"TTS thoát 0 nhưng {output_wav} rỗng hoặc không có")

    return tts_ms

def check_audio_ffprobe(wav_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=sample_rate,channels",
        "-of", "json", wav_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(res.stdout)
    
    # Run volumedetect
    cmd_vol = [
        "ffmpeg", "-i", wav_path, "-af", "volumedetect",
        "-f", "null", "/dev/null"
    ]
    res_vol = subprocess.run(cmd_vol, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = res_vol.stdout
    mean_level = 0.0
    max_level = 0.0
    import re
    m_mean = re.search(r"mean_volume:\s+([\-\d\.]+)\s+dB", out)
    if m_mean: mean_level = float(m_mean.group(1))
    m_max = re.search(r"max_volume:\s+([\-\d\.]+)\s+dB", out)
    if m_max: max_level = float(m_max.group(1))
    
    return {
        "duration_s": float(info.get("format", {}).get("duration", 0)),
        "sample_rate": int(info.get("streams", [{}])[0].get("sample_rate", 0)),
        "channels": int(info.get("streams", [{}])[0].get("channels", 0)),
        "mean_level": mean_level,
        "max_level": max_level
    }

def create_visual_cards(run_dir):
    cards = []
    import pathlib
    for i in range(3):
        img_path = os.path.join(run_dir, 'raw', f'card_{i}.png')
        img = Image.new('RGB', (720, 1280), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10,10), f"Generated Card {i}", fill=(255,255,0))
        img.save(img_path)
        
        cards.append({
            "kind": "generated_template",
            "path": img_path,
            "sha256": logger.calculate_file_sha256(img_path),
            "owner": "Antigravity",
            "license": "Internal"
        })
    return cards

def run_ffmpeg_encode(cards, wav_path, out_mp4):
    # Just loop the first card and audio
    start = time.time()
    # `-shortest` KHÔNG ĐỦ với ảnh tĩnh lặp. Đo 16/08: audio 26,17 giây mà mp4
    # ra 97 giây — dài gấp 3,7 lần. `-loop 1 -framerate 1` cho mỗi khung tồn
    # tại 1 giây ở đầu vào, rồi bộ mã hoá xuất ở nhịp khác, nên trục thời gian
    # bị kéo giãn và `-shortest` cắt theo luồng đã giãn.
    #
    # Chữa bằng cách nói THẲNG thời lượng: đọc độ dài audio rồi truyền `-t`.
    # Không để ffmpeg tự suy ra từ hai luồng lệch nhịp.
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", wav_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    audio_giay = float((r.stdout or "0").strip() or 0)
    if audio_giay <= 0:
        raise ValueError("Không đọc được thời lượng audio để đặt -t cho ffmpeg")

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30",
        "-i", cards[0]["path"],
        "-i", wav_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac",
        "-t", f"{audio_giay:.3f}",
        out_mp4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise Exception(f"ffmpeg encode failed: {res.stderr}")
        
    return int((time.time() - start) * 1000)

def check_blackdetect(mp4_path):
    # `/dev/null` là đường dẫn Unix. Trên Windows ffmpeg sẽ cố TẠO một tệp tên
    # "null" trong thư mục "dev" không tồn tại. Dùng "-" cho cả hai hệ.
    cmd = [
        "ffmpeg", "-i", mp4_path, "-vf", "blackdetect=d=2:pix_th=0.00",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if "black_start" in res.stdout:
        return False
    return True


def kiem_mp4(mp4_path):
    """Cửa cứng cho MP4. Trả về dict, ném lỗi nếu trượt.

    16/08/2026: ba lượt Studio báo PASS mà không lượt nào đạt cửa cứng —
    một tệp 16 byte ffprobe không mở nổi, và hai tệp 143 giây / 117 giây
    trong khi trần là 65.

    Nguyên nhân: mã cũ chỉ kiểm `audio_info["duration_s"]` — THỜI LƯỢNG CỦA
    TỆP WAV. Cửa đặt cho mp4 nhưng đo ở chỗ khác, nên mp4 dài bao nhiêu cũng
    lọt, và một mp4 hỏng hoàn toàn cũng lọt vì nó không hề bị hỏi tới.

    Hàm này hỏi ĐÚNG tệp cuối cùng, và hỏi trước hết câu rẻ nhất: mở được không.
    """
    if not os.path.exists(mp4_path):
        raise ValueError(f"CỬA MP4: không có tệp {mp4_path}")
    kich_thuoc = os.path.getsize(mp4_path)
    if kich_thuoc < 10240:
        raise ValueError(f"CỬA MP4: tệp chỉ {kich_thuoc} byte — không thể là video")

    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", mp4_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise ValueError(f"CỬA MP4: ffprobe không mở được — {res.stderr.strip()[:160]}")

    info = json.loads(res.stdout or "{}")
    loai = [s.get("codec_type") for s in info.get("streams", [])]
    if "video" not in loai:
        raise ValueError(f"CỬA MP4: không có luồng video (chỉ có {loai})")
    if "audio" not in loai:
        raise ValueError(f"CỬA MP4: không có luồng audio (chỉ có {loai})")

    giay = float(info.get("format", {}).get("duration", 0))
    if giay < 55 or giay > 65:
        raise ValueError(f"CỬA MP4: thời lượng {giay:.1f}s, ngoài khoảng 55-65s")

    return {"mp4_duration_s": round(giay, 2), "mp4_bytes": kich_thuoc,
            "streams": loai}

def rut_kich_ban(chuong: str, model: str = "qwen3.5:4b") -> str:
    """Chương 1.500-2.500 chữ -> kịch bản đọc 120-160 từ.

    Bàn giao chốt ở thaoluan.md lượt 008 là:
        chapter.md -> shorts_script (120-160 từ) -> shot_list -> voice+ảnh -> mp4

    Bước này TRƯỚC ĐÂY KHÔNG CÓ. Studio đọc thẳng STUDIO_FIXTURE.md rồi đưa cả
    khối chữ cho TTS — mà 1.998 chữ đọc ra là hơn 10 phút audio, không đời nào
    lọt cửa 55-65 giây. Đó là lý do phải có bước rút, không phải tuỳ chọn.

    `think:false` là bắt buộc: thiếu nó thì model đổ hết token vào trường
    'thinking' và `response` rỗng (đo 16/08: 51,6s ra 0 ký tự).
    """
    import httpx
    loi_dan = (
        "Bạn là biên tập video ngắn. Rút đoạn truyện dưới đây thành một kịch "
        "bản ĐỌC THÀNH TIẾNG dài 120-160 từ tiếng Việt.\n"
        "- Giữ đúng nhân vật và bối cảnh, không thêm tình tiết mới.\n"
        "- Viết thành câu liền mạch để đọc, KHÔNG gạch đầu dòng, KHÔNG tiêu đề.\n"
        "- Chỉ trả về kịch bản, không giải thích.\n\n"
        f"ĐOẠN TRUYỆN:\n{chuong[:6000]}"
    )
    # ĐỪNG CẦU MODEL ĐẾM TỪ. Đo 16/08: xin 120-160 từ, model 4b trả về 353 —
    # gấp hơn hai lần. Nó không cố tình cãi; nó đơn giản không đếm được từ
    # trong lúc viết.
    #
    # Máy siết được thì để máy siết: `num_predict` là trần CỨNG, model không
    # vượt qua được dù muốn. 160 từ tiếng Việt ~ 210-260 token.
    r = httpx.post("http://localhost:11434/api/generate", json={
        "model": model, "prompt": loi_dan, "stream": False, "think": False,
        "keep_alive": "10m",
        "options": {"seed": 42, "temperature": 0.4, "num_predict": 420,
                    "num_ctx": 4096},
    }, timeout=600.0)
    r.raise_for_status()
    chu = (r.json().get("response") or "").strip()

    # Cắt trần thường rơi vào giữa câu. Lùi về dấu chấm cuối cùng — câu cụt
    # đọc lên nghe hụt, và TTS không biết dừng ở đâu.
    cat = max(chu.rfind("."), chu.rfind("!"), chu.rfind("?"))
    if cat > len(chu) * 0.5:
        chu = chu[:cat + 1]

    # Vẫn dài thì cắt theo câu cho tới khi lọt trần.
    #
    # Trần 195 từ, suy từ tốc độ đọc ĐO TRÊN TỆP WAV:
    #     78 từ  ->  26,17 giây audio  ->  0,335 giây/từ
    #     60 giây / 0,335 = ~179 từ
    #
    # Lần đầu tôi tính ra 0,80 giây/từ và siết trần xuống 90 — SAI, vì tôi lấy
    # 101 giây của MP4 làm tử số, mà chính mp4 đó đang bị lỗi kéo giãn thời
    # gian (xem chú thích ở `run_ffmpeg_encode`). Rút tỉ lệ từ một phép đo đã
    # hỏng thì ra một trần sai, rồi trần sai lại làm hỏng phép đo sau.
    # Đo đúng chỗ: WAV, không phải MP4.
    while len(chu.split()) > 195:
        cat = max(chu.rstrip(".!?").rfind("."), chu.rstrip(".!?").rfind("!"),
                  chu.rstrip(".!?").rfind("?"))
        if cat <= 0:
            break
        chu = chu[:cat + 1]
    return chu.strip()


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)

    # Nhận chương THẬT từ Writer nếu được truyền vào; không có thì mới dùng
    # fixture. Chạy trên fixture là thử riêng Studio — nó KHÔNG thay được phép
    # thử bàn giao Writer->Studio, tức cổng Ngày 3.
    nguon = sys.argv[1] if len(sys.argv) > 1 else None
    dung_fixture = nguon is None
    config = {"mode": "offline",
              "input": "STUDIO_FIXTURE" if dung_fixture else nguon}
    run_id = logger.init_run("studio", config)

    run_dir = logger.get_current_run_dir(run_id)

    if dung_fixture:
        fixture_path = os.path.join(base_dir, "data_inputs", "STUDIO_FIXTURE.md")
        with open(fixture_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        with open(nguon, 'r', encoding='utf-8') as f:
            chuong = f.read()
        text = rut_kich_ban(chuong)
        so_tu = len(text.split())
        print(f"kịch bản rút được: {so_tu} từ")
        os.makedirs(os.path.join(run_dir, 'artifacts'), exist_ok=True)
        kb_path = os.path.join(run_dir, 'artifacts', 'shorts_script.md')
        with open(kb_path, 'w', encoding='utf-8') as f:
            f.write(text)
        # Khoảng suy ra từ tốc độ đọc ĐO ĐƯỢC của SAPI (~0,80 giây/từ), không
        # từ con số 120-160 trong đặc tả — đặc tả viết cho giọng neural.
        if not (150 <= so_tu <= 200):
            raise SystemExit(
                f"CỬA KỊCH BẢN: {so_tu} từ, ngoài khoảng 150-200 "
                f"(~0,335 giây/từ -> 50-67 giây audio)")

    try:
        # 1. SAPI
        wav_path = os.path.join(run_dir, 'raw', 'tts.wav')
        tts_ms = generate_sapi_tts(text, wav_path)
        audio_info = check_audio_ffprobe(wav_path)
        audio_info["tts_synthesis_ms"] = tts_ms
        
        # Audio chỉ cần KHÔNG IM LẶNG và có thời lượng đo được. Cửa 55-65 giây
        # thuộc về MP4 và được kiểm ở `kiem_mp4()` phía dưới — xem chú thích ở
        # đó về ba lượt PASS sai ngày 14/08.
        if audio_info["duration_s"] <= 0:
            raise ValueError("Audio rỗng hoặc không đo được thời lượng.")
            
        # 2. Visual cards
        cards = create_visual_cards(run_dir)
        
        # 3. FFmpeg encode
        out_mp4 = os.path.join(run_dir, 'artifacts', 'studio_output.mp4')
        encode_ms = run_ffmpeg_encode(cards, wav_path, out_mp4)
        
        # 4. CỬA CỨNG TRÊN CHÍNH MP4 — mở được, có đủ hai luồng, đúng thời lượng
        mp4_info = kiem_mp4(out_mp4)

        # 5. Blackdetect
        if not check_blackdetect(out_mp4):
            raise Exception("blackdetect failed")

        logger.log_artifact(run_id, "studio_output.mp4", out_mp4)

        metrics = {
            "audio_info": audio_info,
            "mp4_info": mp4_info,
            "visual_cards": cards,
            "nguon": "STUDIO_FIXTURE" if dung_fixture else nguon,
        }
        logger.log_metrics(run_id, "PASS", gate_results=metrics)
        import psutil
        logger.log_command(run_id, "studio.py", 0, encode_ms, psutil.virtual_memory().used / 1024**2)
        sys.exit(0)
    except Exception as e:
        logger.log_error(run_id, str(e))
        logger.log_metrics(run_id, "FAIL", str(e))
        logger.log_command(run_id, "studio.py", 1, 0, None)
        sys.exit(1)
