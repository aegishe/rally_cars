# -*- coding: utf-8 -*-
"""
6:22 原型车 PotPlayer 逐帧截图（9295 张）→ RapidOCR 全圈 25fps 轨道
- 文件名时间戳 HHMMSS.mmm = 视频时间；Laptime = 视频时间 - 1.77s
- 输出 publish/assets/_p622/pot_ocr.csv（video_t, lap_t, speed）
"""
import csv
import glob
import os
import re

from PIL import Image
from rapidocr_onnxruntime import RapidOCR

DIR = r'G:\Capture\youtube\Xiaomi SU7 Ultra Prototype'
OUT = r'D:\Project\dsh_rally_cars\publish\assets\_p622\pot_ocr.csv'
TMP = r'D:\Project\dsh_rally_cars\publish\assets\_p622\_t.png'
OFFSET = 1.77

ocr = RapidOCR()
files = sorted(glob.glob(os.path.join(DIR, '*.jpg')))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['video_t', 'lap_t', 'speed'])
    for i, f in enumerate(files):
        m = re.search(r'(\d{2})(\d{2})(\d{2})\.(\d{3})\.jpg$', f)
        vt = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
        lap = round(vt - OFFSET, 3)
        img = Image.open(f)
        crop = img.crop((1130, 860, 1520, 1080))
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        crop.save(TMP)
        result, _ = ocr(TMP)
        txt = ' '.join([item[1] for item in result]) if result else ''
        nums = [int(x) for x in re.findall(r'\d{1,3}', txt)]
        cands = [x for x in nums if 10 <= x <= 400]
        speed = max(cands) if cands else ''
        w.writerow([f'{vt:.3f}', f'{lap:.3f}', speed])
        if i % 500 == 0:
            print(f'{i}/{len(files)}  vt={vt:.1f}s  speed={speed}', flush=True)
print('完成:', OUT)
