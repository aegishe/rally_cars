# -*- coding: utf-8 -*-
"""用 faster-whisper 识别音频，输出纯文本（含时间戳）。"""
import sys
from faster_whisper import WhisperModel

audio_path = sys.argv[1]
out_path = sys.argv[2]

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    audio_path, language="zh", beam_size=5, vad_filter=True
)

lines = []
for seg in segments:
    t = seg.text.strip()
    if t:
        lines.append(f"[{seg.start:6.1f}-{seg.end:6.1f}] {t}")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"识别完成，共 {len(lines)} 段，已写入 {out_path}")
