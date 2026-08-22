# -*- coding: utf-8 -*-
"""
6:22 原型车全圈 5fps 采样（RapidOCR 版）
- ffmpeg 抽帧（视频时间 = Laptime + 1.77s）→ PIL 裁剪速度数字区并放大 → RapidOCR
- 输出 publish/assets/_p622/rapid5.csv（帧号, t_lap, ocr文本）
"""
import csv
import os
import subprocess

import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT = r'D:\Project\dsh_rally_cars'
VIDEO = r'G:\Capture\youtube\Xiaomi SU7 Ultra prototype ｜ Official uncut Nürburgring footage [M2zt0yAcplU].mp4'
WORK = os.path.join(ROOT, 'publish', 'assets', '_p622', 'rapid5')
OUT = os.path.join(ROOT, 'publish', 'assets', '_p622', 'rapid5.csv')

# 速度数字显示范围（用户提供 1175,645-1336,1047，数字主体在右下），裁剪留白
CROP = (1130, 860, 1520, 1080)

os.makedirs(WORK, exist_ok=True)
ocr = RapidOCR()

N = 1911  # 5fps × 382.1s
with open(OUT, 'w', newline='', encoding='utf-8') as fout:
    w = csv.writer(fout)
    w.writerow(['frame', 't_lap', 'ocr'])
    for k in range(N):
        t_lap = k * 0.2
        tmp = os.path.join(WORK, f'f{k:04d}.jpg')
        if not os.path.exists(tmp):
            subprocess.run(['ffmpeg', '-y', '-ss', f'{1.77 + t_lap:.3f}', '-i', VIDEO,
                            '-frames:v', '1', '-q:v', '2', tmp],
                           check=True, capture_output=True)
        img = Image.open(tmp).crop(CROP)
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        tmp2 = os.path.join(WORK, f'c{k:04d}.png')
        img.save(tmp2)
        result, _ = ocr(tmp2)
        txt = ' '.join([item[1] for item in result]) if result else ''
        w.writerow([k, f'{t_lap:.1f}', txt])
        os.remove(tmp)
        os.remove(tmp2)
        if k % 200 == 0:
            print(f'{k}/{N}  t={t_lap:.0f}s  ocr=[{txt}]', flush=True)
print('完成:', OUT)
