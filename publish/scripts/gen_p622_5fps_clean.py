# -*- coding: utf-8 -*-
"""
6:22 原型车 YouTube 原版 5fps 数据清洗（复用量产管线逻辑）
- 读 _p622/yt5_ocr_s5.txt（fNNNN.jpg + time + speed）
- 速度候选提取（10-400）+ 百位补全（OCR 丢百位：10=210 等，连续性优先）
- 孤立跳变剔除（0.2s 内 >12km/h 不物理 → NaN）
- 输出 publish/assets/_p622/p622_5fps.csv（t_s=Laptime=帧号*0.2, speed）
"""
import csv
import re
import os

import numpy as np

ROOT = r'D:\Project\dsh_rally_cars'
IN = os.path.join(ROOT, 'publish', 'assets', '_p622', 'yt5_ocr_s5.txt')
OUT = os.path.join(ROOT, 'publish', 'assets', '_p622', 'p622_5fps.csv')

rows = []
for line in open(IN, encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 2:
        continue
    m = re.match(r'f(\d+)\.jpg', parts[0])
    if not m:
        continue
    n = int(m.group(1))
    text = parts[1]
    # 剔除时间 token（MM:SS 及小数变体），剩速度文本
    text = re.sub(r'\d{1,2}[:：]\d{2}\s*[,，.]?\s*\d*', ' ', text)
    nums = [int(x) for x in re.findall(r'\d{1,3}', text)]
    rows.append((n, nums))

out = []
prev = None
for n, nums in rows:
    cands = [x for x in nums if 10 <= x <= 400]
    if not cands:
        out.append((n, None))
        continue
    if prev is None:
        big = [x for x in cands if x >= 60]
        v = max(big) if big else (max(cands) + 200 if max(cands) < 60 else max(cands))
    else:
        cands2 = []
        for x in cands:
            cands2.append(x)
            if x < 100 and 100 + x <= 400 and abs(100 + x - prev) < 60:
                cands2.append(100 + x)
            if x < 100 and 200 + x <= 400 and abs(200 + x - prev) < 60:
                cands2.append(200 + x)
        v = min(cands2, key=lambda x: abs(x - prev))
    out.append((n, v))
    prev = v

t = np.array([n * 0.2 for n, v in out])
sp = np.array([v if v is not None else np.nan for n, v in out], dtype=float)
valid = ~np.isnan(sp)
for i in range(1, len(sp) - 1):
    if valid[i] and (valid[i-1] or valid[i+1]):
        ref = sp[i-1] if valid[i-1] else sp[i+1]
        if abs(sp[i] - ref) > 12:
            sp[i] = np.nan

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['t_s', 'speed_kmh'])
    for i in range(len(t)):
        if not np.isnan(sp[i]):
            w.writerow([f'{t[i]:.2f}', f'{sp[i]:.1f}'])

n_valid = np.sum(~np.isnan(sp))
print(f'{IN} -> {OUT}')
print(f'共 {len(t)} 帧, 有效 {n_valid} ({n_valid/len(t)*100:.0f}%)')
