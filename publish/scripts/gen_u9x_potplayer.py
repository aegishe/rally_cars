# -*- coding: utf-8 -*-
"""
U9X PotPlayer 逐帧截图（10352 张）→ RapidOCR 全圈 25fps 轨道
- 文件名时间戳 HHMMSS.mmm = 视频时间；Laptime = 视频时间 - 1.28s
- 输出 publish/assets/_u9x/u9x_ocr.csv
"""
import csv
import glob
import os
import re

from PIL import Image
from rapidocr_onnxruntime import RapidOCR

DIR = r'G:\Capture\youtube\U9X'
OUT = r'D:\Project\dsh_rally_cars\publish\assets\_u9x\u9x_ocr.csv'
TMP = r'D:\Project\dsh_rally_cars\publish\assets\_u9x\_t.png'
OFFSET = 1.28

os.makedirs(os.path.dirname(OUT), exist_ok=True)
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
        crop = img.crop((1020, 900, 1320, 1090))
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        crop.save(TMP)
        result, _ = ocr(TMP)
        txt = ' '.join([item[1] for item in result]) if result else ''
        nums = [int(x) for x in re.findall(r'\d{1,3}', txt)]
        cands = [x for x in nums if 10 <= x <= 400]
        speed = max(cands) if cands else ''
        w.writerow([f'{vt:.3f}', f'{lap:.3f}', speed])
        if i % 1000 == 0:
            print(f'{i}/{len(files)}  vt={vt:.1f}s  speed={speed}', flush=True)
print('完成:', OUT)

# ---- 清洗 + 积分 + 与 corner CSV 交叉验证 ----
import numpy as np
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
with open(r'D:\Project\dsh_rally_cars\publish\assets\_u9x\u9x_clean.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['lap_t', 'speed_kmh', 's_m'])
    for i in range(len(t)):
        w.writerow([f'{t[i]:.3f}', f'{v[i]:.1f}', f'{s[i]:.1f}'])
# 与 corner CSV（u9x 5fps）对比：每 20m 取速度差
corner = {}
for r in csv.DictReader(open(r'D:\Project\dsh_rally_cars\track\corner_comparison.csv', encoding='utf-8')):
    corner[float(r['s_m'])] = float(r['v_u9x'])
diffs = []
for s0, v0 in corner.items():
    if s0 > s[-1]:
        continue
    i = np.argmin(np.abs(s - s0))
    if abs(s[i] - s0) < 15:
        diffs.append(abs(v[i] - v0))
if diffs:
    print(f'与 corner CSV 交叉验证：{len(diffs)} 个采样点，平均差 {np.mean(diffs):.1f} km/h，中位 {np.median(diffs):.1f}，>10 的 {sum(1 for d in diffs if d > 10)} 个')
