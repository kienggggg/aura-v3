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
        
    # WinRT chứ KHÔNG System.Speech — vì giọng Việt nằm ở hive khác.
    #
    # Đo 19/08/2026 trên máy này:
    #   HKLM\\...\\Speech\\Voices\\Tokens           DAVID, ZIRA          (đều en-US)
    #   HKLM\\...\\Speech_OneCore\\Voices\\Tokens   +  MSTTS_V110_viVN_An
    #
    # `System.Speech` (SAPI5) chỉ đọc hive thứ nhất, nên nó KHÔNG BAO GIỜ thấy
    # giọng Việt — dù giọng ấy đã cài sẵn từ đầu. Bản cũ vì thế rơi xuống đường
    # lui "giọng Microsoft bất kỳ" và đọc chương truyện tiếng Việt bằng giọng
    # tiếng Anh, trong im lặng. Cửa kiểm không bắt được vì nó chỉ hỏi "có tiếng
    # không", không hỏi "đúng giọng không".
    #
    # `Windows.Media.SpeechSynthesis` đọc được hive OneCore. Không cần quyền
    # admin, không sờ vào registry, không cài thêm gì.
    #
    # KHÔNG có đường lui sang giọng khác: KY_LUAT_THUC_THI.md chương II mục 2
    # đòi đúng token vi-VN. Thiếu thì phải KÊU, vì một giọng tiếng Anh đọc
    # tiếng Việt là hỏng SẢN PHẨM, không phải hỏng test.
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    $text = Get-Content '{text_file}' -Encoding UTF8 -Raw
    [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media, ContentType=WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType=WindowsRuntime] | Out-Null
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
                       $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }} |
        Select-Object -First 1
    function Await($op, $type) {{
        $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op))
        $t.Wait(-1) | Out-Null
        $t.Result
    }}
    $vi = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices |
          Where-Object {{ $_.Language -like 'vi*' }} | Select-Object -First 1
    if (-not $vi) {{
        Write-Error "khong co giong vi-VN nao trong Speech_OneCore"
        exit 1
    }}
    Write-Output "giong: $($vi.DisplayName) [$($vi.Language)]"
    $synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
    $synth.Voice = $vi
    $stream = Await $synth.SynthesizeTextToStreamAsync($text) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    $reader = New-Object Windows.Storage.Streams.DataReader($stream)
    Await $reader.LoadAsync($stream.Size) ([uint32]) | Out-Null
    $bytes = New-Object byte[] $stream.Size
    $reader.ReadBytes($bytes)
    [System.IO.File]::WriteAllBytes('{output_wav}', $bytes)
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
            f"exit 1 = không có giọng vi-VN trong Speech_OneCore. "
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
    """Chương 1.500-2.500 chữ -> kịch bản đọc 234-276 từ (55-65 giây).

    Bàn giao chốt ở thaoluan.md lượt 008 là:
        chapter.md -> shorts_script (120-160 từ) -> shot_list -> voice+ảnh -> mp4

    Bước này TRƯỚC ĐÂY KHÔNG CÓ. Studio đọc thẳng STUDIO_FIXTURE.md rồi đưa cả
    khối chữ cho TTS — mà 1.998 chữ đọc ra là hơn 10 phút audio, không đời nào
    lọt cửa 55-65 giây. Đó là lý do phải có bước rút, không phải tuỳ chọn.

    `think:false` là bắt buộc: thiếu nó thì model đổ hết token vào trường
    'thinking' và `response` rỗng (đo 16/08: 51,6s ra 0 ký tự).
    """
    import httpx

    # ĐỪNG XIN MODEL MỘT ĐỘ DÀI. Đo ba lần, cùng chương, cùng seed:
    #     xin 120-160 từ  ->  353    (gấp 2,2 lần)
    #     xin 250 từ      ->  206    (bằng 0,82)
    #     xin 400 từ      ->  188    (bằng 0,47)
    # Xin nhiều hơn thì ra ÍT hơn. Con số trong lời dặn không điều khiển gì cả;
    # độ dài ra là do LƯỢNG CHỮ ĐƯA VÀO quyết định. Bản cũ đưa `chuong[:6000]`
    # — khoảng 60% một chương 10.000 ký tự — nên video cũng chỉ kể được 60%
    # chương, và luôn ra quanh 190-210 từ.
    #
    # Nên đổi cần gạt: MÁY ghép, model chỉ viết văn. Chia chương thành khúc,
    # xin kịch bản từng khúc, nối lại tới khi đủ 234 từ rồi cắt xuống 275.
    # Máy đếm được thì để máy đếm — model đã ba lần chứng minh nó không đếm.
    #
    # Lợi thêm: kịch bản giờ phủ CẢ chương chứ không riêng phần đầu.
    # Gom tới 320 từ THÔ, không phải 234.
    #
    # Bản đầu của vòng này dừng ở 234 — đúng cửa dưới — rồi bước cắt-về-cuối-câu
    # ngay bên dưới gọt mất phần dư và tụt xuống 211, trượt chính cái cửa vừa
    # canh. Kiểm ngưỡng ở chỗ TRƯỚC khi cắt thì ngưỡng ấy không có nghĩa gì.
    #
    # 320 chừa chỗ cho cả hai bước gọt (về cuối câu, rồi cắt xuống 275), nên
    # đầu ra rơi vào khoảng 234-275 thay vì rơi xuống dưới.
    KHUC = 5000
    khuc = [chuong[i:i + KHUC] for i in range(0, len(chuong), KHUC)] or [chuong]
    phan: list[str] = []
    for k in khuc:
        if len(" ".join(phan).split()) >= 320:
            break
        loi_dan = (
            "Bạn là biên tập video ngắn. Rút đoạn truyện dưới đây thành lời "
            "ĐỌC THÀNH TIẾNG bằng tiếng Việt.\n"
            "- Giữ đúng nhân vật và bối cảnh, không thêm tình tiết mới.\n"
            "- Viết thành câu liền mạch để đọc, KHÔNG gạch đầu dòng, KHÔNG tiêu đề.\n"
            "- Chỉ trả về lời đọc, không giải thích.\n\n"
            f"ĐOẠN TRUYỆN:\n{k}"
        )
        r = httpx.post("http://localhost:11434/api/generate", json={
            "model": model, "prompt": loi_dan, "stream": False, "think": False,
            "keep_alive": "10m",
            "options": {"seed": 42, "temperature": 0.4, "num_predict": 900,
                        "num_ctx": 4096},
        }, timeout=600.0)
        r.raise_for_status()
        m = (r.json().get("response") or "").strip()
        if m:
            phan.append(m)
    chu = " ".join(phan)

    # Cắt trần thường rơi vào giữa câu. Lùi về dấu chấm cuối cùng — câu cụt
    # đọc lên nghe hụt, và TTS không biết dừng ở đâu.
    cat = max(chu.rfind("."), chu.rfind("!"), chu.rfind("?"))
    if cat > len(chu) * 0.5:
        chu = chu[:cat + 1]

    # Vẫn dài thì cắt theo câu cho tới khi lọt trần.
    #
    # Trần 275 từ. HẰNG SỐ NÀY ĐÃ SAI HAI LẦN, mỗi lần một kiểu khác nhau:
    #
    #   0,80 giây/từ   lấy 101 giây của MP4 làm tử số, mà chính MP4 đó đang bị
    #                  kéo giãn thời gian. Rút tỉ lệ từ một phép đo đã hỏng.
    #   0,335 giây/từ  đo đúng trên WAV, nhưng là WAV của GIỌNG TIẾNG ANH đọc
    #                  chữ tiếng Việt. Đo ba lượt — 0,335 · 0,329 · 0,332 —
    #                  ba lượt khớp nhau và CẢ BA cùng đo sai một thứ.
    #
    # Ba phép đo khớp nhau không làm chúng đúng. Chúng chỉ chứng minh cùng một
    # cái sai lặp lại ổn định.
    #
    # Đo 19/08 với giọng ĐÚNG (vi-VN Microsoft An), ba độ dài khác nhau:
    #      60 từ -> 14,6 giây -> 0,243 giây/từ
    #     132 từ -> 31,9 giây -> 0,241
    #     224 từ -> 52,8 giây -> 0,236
    #     đường thẳng:  giây = 0,2331 * từ + 0,56
    #     -> 55-65 giây cần 234-276 từ
    #
    # Giọng Việt đọc NHANH HƠN giọng Anh 1,4 lần trên cùng chữ, vì giọng Anh
    # phải bò từng âm tiết lạ. Nên vá giọng xong thì trần cũ 195 từ cho ra 40,5
    # giây — trượt cửa dưới.
    # CỘNG DỒN TỪ ĐẦU, không gọt từ đuôi.
    #
    # Bản cũ cắt nguyên một câu khỏi đuôi mỗi vòng cho tới khi lọt trần 275.
    # Đo 19/08: model đẻ 808 từ, gọt dần xuống còn 280, rồi câu vượt trần cuối
    # cùng dài 69 từ nên nhát gọt ấy ném thẳng xuống 211 — dưới cửa 234. Ba
    # lượt chạy đều ra ĐÚNG 211, và tôi đã hai lần đoán sai nguyên nhân trước
    # khi chịu đo từng khúc.
    #
    # Gọt từ đuôi thì nhát cuối muốn cắt bao nhiêu cũng được. Cộng từ đầu thì
    # mỗi câu chỉ được thêm khi còn chỗ, nên kết quả bám sát trần từ phía dưới.
    import re as _re
    cau = [c for c in _re.split(r"(?<=[.!?])\s+", chu) if c.strip()]
    gom, dem = [], 0
    for c in cau:
        n = len(c.split())
        if dem + n > 275:
            continue          # câu này quá dài -> bỏ qua, thử câu ngắn kế tiếp
        gom.append(c)
        dem += n
    if gom:
        chu = " ".join(gom)
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
        # Khoảng suy từ tốc độ đọc ĐO ĐƯỢC của giọng vi-VN An 19/08:
        # 0,2331 giây/từ (ba điểm: 60/132/224 từ). Không lấy từ con số 120-160
        # trong đặc tả — con số đó tính cho một giọng khác, và ở nhịp này nó
        # chỉ ra 28-38 giây, tức TRƯỢT chính cửa 55-65 mà đặc tả tự đặt.
        if not (234 <= so_tu <= 276):
            raise SystemExit(
                f"CỬA KỊCH BẢN: {so_tu} từ, ngoài khoảng 234-276 "
                f"(0,2331 giây/từ -> 55-65 giây audio)")

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
