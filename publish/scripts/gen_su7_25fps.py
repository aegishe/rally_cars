# -*- coding: utf-8 -*-
"""
SU7 量产 25fps 抽帧（10933 张）→ RapidOCR 全圈轨道
- 帧号 n → 视频时间 n/25；Laptime = 视频时间 - 2.08s
- 输出 publish/assets/_su7f/su7_ocr.csv + 清洗积分 su7_clean.csv
"""
import csv
import glob
import os
import re

import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

DIR = r'D:\Project\dsh_rally_cars\publish\assets\_su7f'
OUT = os.path.join(DIR, 'su7_ocr.csv')
CLEAN = os.path.join(DIR, 'su7_clean.csv')
OFFSET = 2.08

ocr = RapidOCR()
files = sorted(glob.glob(os.path.join(DIR, '*.jpg')))
print('帧数:', len(files), flush=True)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['lap_t', 'speed'])
    for i, fp in enumerate(files):
        lap = round(i / 25.0 - OFFSET, 3)
        img = Image.open(fp)
        crop = img.crop((1130, 860, 1520, 1080))
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        tmp = os.path.join(DIR, '_t.png')
        crop.save(tmp)
        result, _ = ocr(tmp)
        txt = ' '.join([item[1] for item in result]) if result else ''
        nums = [int(x) for x in re.findall(r'\d{1,3}', txt)]
        cands = [x for x in nums if 10 <= x <= 400]
        speed = max(cands) if cands else ''
        w.writerow([f'{lap:.3f}', speed])
        if i % 1000 == 0:
            print(f'{i}/{len(files)}  lap={lap:.1f}s  speed={speed}', flush=True)
        os.remove(tmp)
print('完成:', OUT)

rows = []
for r in csv.DictReader(open(OUT, encoding='utf-8')):
    if r['speed'] != '':
        rows.append((float(r['lap_t']), float(r['speed'])))
rows.sort()
t = np.array([r[0] for r in rows]); v = np.array([r[1] for r in rows])
print(f'读入 {len(t)} 点（读出率 {len(t)/len(files)*100:.1f}%）')
for i in range(1, len(v) - 1):
    if abs(v[i] - v[i-1]) > 15 and abs(v[i] - v[i+1]) > 15:
        v[i] = (v[i-1] + v[i+1]) / 2
s = np.zeros_like(t)
for i in range(1, len(t)):
    s[i] = s[i-1] + (v[i-1] + v[i]) / 2 / 3.6 * (t[i] - t[i-1])
print(f'积分全长 {s[-1]:.0f} m ({s[-1]/20600*100:.1f}%)')
with open(CLEAN, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['lap_t', 'speed_kmh', 's_m'])
    for i in range(len(t)):
        w.writerow([f'{t[i]:.3f}', f'{v[i]:.1f}', f'{s[i]:.1f}'])
# 与 corner CSV（量产 5fps 口径）交叉验证
corner = {}
for r in csv.DictReader(open(r'D:\Project\dsh_rally_cars\track\corner_comparison.csv', encoding='utf-8')):
    corner[float(r['s_m'])] = float(r['v_su7'])
diffs = []
for s0, v0 in corner.items():
    if s0 > s[-1]:
        continue
    i = np.argmin(np.abs(s - s0))
    if abs(s[i] - s0) < 15:
        diffs.append(abs(v[i] - v0))
if diffs:
    print(f'与 corner CSV 交叉验证：{len(diffs)} 点，平均差 {np.mean(diffs):.1f} km/h，中位 {np.median(diffs):.1f}，>10 的 {sum(1 for d in diffs if d > 10)} 个')
