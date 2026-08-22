# -*- coding: utf-8 -*-
"""
PotPlayer 25fps 轨道清洗 → 积分距离 → 三车曲线
读 pot_ocr.csv（video_t, lap_t, speed）：
1. 跳变剔除（相邻 0.04s >15km/h 不物理 → NaN）
2. 速度积分 → 距离（Laptime 轴）
3. 与 38 人工锚交叉验证
输出：_p622/pot_clean.csv（lap_t, speed, s_m）
"""
import csv
import re
import os

import numpy as np

ROOT = r'D:\Project\dsh_rally_cars'
IN = os.path.join(ROOT, 'publish', 'assets', '_p622', 'pot_ocr.csv')
OUT = os.path.join(ROOT, 'publish', 'assets', '_p622', 'pot_clean.csv')

rows = []
with open(IN, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['speed'] != '':
            rows.append((float(r['lap_t']), float(r['speed'])))
rows.sort()
t = np.array([r[0] for r in rows])
v = np.array([r[1] for r in rows])
print(f'读入 {len(t)} 点（读出率 {len(t)/9295*100:.1f}%）')

# 跳变剔除
bad = 0
for i in range(1, len(v) - 1):
    if abs(v[i] - v[i-1]) > 15 and abs(v[i] - v[i+1]) > 15:
        v[i] = (v[i-1] + v[i+1]) / 2
        bad += 1
print(f'修正跳变 {bad} 点')

# 积分
s = np.zeros_like(t)
for i in range(1, len(t)):
    s[i] = s[i-1] + (v[i-1] + v[i]) / 2 / 3.6 * (t[i] - t[i-1])
print(f'积分全长 {s[-1]:.0f} m ({s[-1]/20600*100:.1f}%)')

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['lap_t', 'speed_kmh', 's_m'])
    for i in range(len(t)):
        w.writerow([f'{t[i]:.3f}', f'{v[i]:.1f}', f'{s[i]:.1f}'])

# 人工锚交叉验证
anchors = [(7.0,85),(14.0,182),(24.0,124),(35.6,104),(49.3,205),(65.0,232),(71.7,109),(95.0,84),(109.0,187),(113.9,115),(121.0,101),(128.0,175),(132.0,159),(142.0,76),(153.1,120),(158.0,117),(169.0,216),(172.0,111),(178.0,215),(180.0,244),(198.0,246),(200.0,203),(205.2,237),(214.0,92),(224.5,91),(234.3,198),(245.7,119),(261.0,133),(271.2,125),(276.6,117),(284.1,105),(295.5,155),(306.0,213),(319.8,133),(326.4,112),(333.6,153),(337.9,183),(376.0,91)]
print('人工锚验证（±0.1s 窗口取最近帧）:')
hit = 0
for tt, vv in anchors:
    m = np.abs(t - tt) <= 0.1
    if m.sum():
        i = np.where(m)[0][np.argmin(np.abs(t[m] - tt))]
        d = abs(v[i] - vv)
        flag = '✓' if d <= 3 else ('~' if d <= 8 else '✗')
        if d <= 8: hit += 1
        print('  t=%6.1f 人工%3d  轨道%4.0f %s' % (tt, vv, v[i], flag))
print(f'命中 {hit}/{len(anchors)}')
print('保存:', OUT)
