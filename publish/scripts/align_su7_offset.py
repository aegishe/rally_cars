# -*- coding: utf-8 -*-
"""用当时的 OCR 截图与视频帧做像素级对齐，锁定 SU7 视频时间偏移"""
import subprocess, os, sys
import numpy as np
from PIL import Image

VIDEO = r'G:\Capture\youtube\Xiaomi SU7 Ultra ｜ Official uncut Nürburgring footage [I2EjtbqkZIU].mp4'
REF = r'G:\Capture\youtube\Xiaomi SU7 Ultra\Xiaomi SU7 Ultra20260819_145104.066.jpg'  # clips 00:07.72
TMP = r'D:\Project\dsh_rally_cars\publish\assets\_anchor\frame_cmp.jpg'

ref = Image.open(REF).convert('L')
ref_a = np.asarray(ref, dtype=np.float32)

best = (1e18, None)
for t10 in range(70, 135):  # 7.0s ~ 13.5s，步进 0.1s
    t = t10 / 10.0
    subprocess.run(['ffmpeg', '-y', '-ss', f'{t:.2f}', '-i', VIDEO,
                    '-frames:v', '1', '-q:v', '2', TMP],
                   check=True, capture_output=True)
    img = Image.open(TMP).convert('L')
    if img.size != ref.size:
        continue
    a = np.asarray(img, dtype=np.float32)
    d = float(np.mean(np.abs(a - ref_a)))
    if d < best[0]:
        best = (d, t)
    print(f't={t:5.2f}  mae={d:7.1f}', flush=True)

print('BEST:', best)
