# -*- coding: utf-8 -*-
"""Sinh mốc thời gian TỪNG TỪ cho một tệp WAV. In JSON ra stdout.

TỆP NÀY KHÔNG CHẠY BẰNG PYTHON CỦA AURA — nó chạy bằng một venv riêng có
`faster-whisper`. Vì sao (07/09/2026):

`faster-whisper` kéo theo `ctranslate2` · `onnxruntime` · `av` · `numpy` ·
`tokenizers` · `huggingface-hub` — đo được **273 MB và 10+ gói**, cộng 605 MB
model. `CLAUDE.md` mục 1 lấy con số **2 gói ngoài** làm lý do v3 tồn tại. Đẩy
nó lên 12 để thêm một tính năng là tự tay dựng lại đúng cái bệnh của v2:
339 tệp, 33 cờ, 29 cái đang TẮT.

Nên nó đứng ngoài, và `core/can_chu.py` gọi qua tiến trình con — đúng khuôn
`node --check` / `bash -n` mà phòng `epsilon` đã dùng từ 06/09.

WORKER KHÔNG ĐƯỢC TỰ CHẤM PASS (`KY_LUAT_THUC_THI.md` chương VIII). Ở đây nó
in ra mốc thô và **không có một dòng nào** nói "đạt" hay "không đạt". Việc tính
WER, tính độ phủ và ra phán quyết thuộc về `core/can_chu.py` — bên gọi, không
phải bên chạy.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time

# BỌC STDOUT UTF-8, KHÔNG ĐƯỢC BỎ. Tệp này in ra chữ tiếng Việt có dấu, và
# stdout của Python trên Windows mặc định là `cp1252` khi bị chuyển hướng vào
# đường ống. Đo 07/09/2026: bản đầu chết với
# `UnicodeEncodeError: 'charmap' codec can't encode character 'ẽ'` — chữ
# "ẽ". Bên gọi đọc được mã thoát 1 và trả KHONG_DO_DUOC, tức ba trạng thái làm
# đúng việc; nhưng lỗi thì nằm ở đây. Cùng bài "đo tiếng Việt bằng Python,
# đừng qua PowerShell" đã ghi trong `CLAUDE.md` mục 3.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="vi")
    a = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        json.dump({"loi": f"thiếu faster-whisper: {e}", "tu": []},
                  sys.stdout, ensure_ascii=False)
        return 2

    t0 = time.monotonic()
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    t_nap = time.monotonic() - t0

    # GHIM NHIỆT ĐỘ — nếu không, CÙNG MỘT TỆP cho BA kết quả khác nhau.
    #
    # Đo 10/09/2026: sinh giọng một lần, chạy bộ căn 8 lượt trên đúng tệp ấy:
    #     lượt 1,4,5,6,7   PASS  87/114 từ khớp   lệch lớn nhất 0,009062s
    #     lượt 2           PASS  71/114 từ khớp   lệch lớn nhất 0,031375s
    #     lượt 3, 8        KHONG_DAT — không ghi `.ass`
    #
    # `faster-whisper` mặc định dùng THANG NHIỆT ĐỘ DỰ PHÒNG
    # [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]: ngưỡng logprob hoặc tỉ lệ nén không đạt
    # thì nó LẤY MẪU NGẪU NHIÊN lại ở nhiệt độ cao hơn. Truyền đúng một giá trị
    # `0.0` là tắt hẳn thang ấy.
    #
    # `condition_on_previous_text=False`: bật thì mỗi đoạn phụ thuộc văn bản
    # đoạn trước, nên một chữ đổi ở đoạn 1 kéo lệch cả phần đuôi.
    #
    # `beam_size=5` ghim rõ dù trùng mặc định — mặc định của thư viện đổi được
    # ở bản sau, và khi ấy không ai biết vì sao số đổi.
    #
    # NÓI RÕ CÁI KHÔNG ĐỔI: chỗ này làm bộ căn TẤT ĐỊNH, không làm nó CHÍNH XÁC
    # HƠN. 87/114 vẫn là 87/114; thứ mất đi là những lượt 71/114 và KHONG_DAT
    # ngẫu nhiên. Đây là ca "cùng mã, cùng đề, hai phán quyết" — lần trước biến
    # thứ ba là PATH, lần này nó nằm BÊN TRONG bộ đo.
    t0 = time.monotonic()
    doan, _ = m.transcribe(a.wav, language=a.lang, word_timestamps=True,
                           temperature=0.0, beam_size=5,
                           condition_on_previous_text=False)
    tu = [{"bd": round(w.start, 3), "kt": round(w.end, 3), "chu": w.word}
          for d in doan for w in (d.words or [])]
    t_dich = time.monotonic() - t0

    # Hai con số thời gian ĐỂ RIÊNG. Gộp lại thì không đọc ra được cái nào là
    # chi phí cố định — đúng bài đã mắc với Remotion ngày 06/09, đọc "chậm gấp
    # 30 lần" trong khi phần lớn là nạp một lần.
    json.dump({"tu": tu, "model": a.model,
               "giay_nap": round(t_nap, 2), "giay_dich": round(t_dich, 2)},
              sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
