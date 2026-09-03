# -*- coding: utf-8 -*-
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from faster_whisper import WhisperModel

AUDIO = r"D:\Project\dsh_rally_cars\.tmp\bili_audio.m4s"
OUT = r"D:\Project\dsh_rally_cars\.tmp\bili_transcript.txt"

print("[whisper] loading model small ...")
t0 = time.time()
model = WhisperModel("small", device="cpu", compute_type="int8")
print("[whisper] model loaded in %.1fs" % (time.time()-t0))

print("[whisper] transcribing ...")
t1 = time.time()
segments, info = model.transcribe(AUDIO, language="zh", vad_filter=True, beam_size=5)
print("[whisper] detected language", info.language, "prob", info.language_probability, "dur", info.duration)

lines = []
for seg in segments:
    line = "[%06.2f -> %06.2f] %s" % (seg.start, seg.end, seg.text.strip())
    lines.append(line)
    print(line, flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("[whisper] DONE in %.1fs, %d segments -> %s" % (time.time()-t1, len(lines), OUT))
