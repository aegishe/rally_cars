# -*- coding: utf-8 -*-
"""
三车全程速度-距离曲线（最终版）
- U9X / SU7 量产：corner_comparison.csv（10m 网格）
- SU7 原型 6:22：OCR 清洗轨道 + 38 弯谷人工读数覆盖 → 弯谷序号对齐（分段线性时间翘曲）
输出：publish/assets/chapter2s-4-speed-profiles.png
"""
import csv
import re
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = r'D:\Project\dsh_rally_cars'
OUT = os.path.join(ROOT, 'publish', 'assets', 'chapter2s-4-speed-profiles.png')

for fp in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf']:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        zh = font_manager.FontProperties(fname=fp).get_name()
        plt.rcParams['font.family'] = zh
        break
plt.rcParams['axes.unicode_minus'] = False

# ---------- 三车 25fps 同源轨道（各自锚校正距离） ----------
S_POS = [240,530,1000,1490,2280,3560,3850,5220,5920,6180,6460,6700,6930,7400,7860,8100,8590,8900,9320,9780,10500,10750,11190,11550,12000,12480,12980,13500,14120,14340,14630,15200,15780,16600,16860,17200,17400,20460]

def load_clean(path):
    t, v = [], []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            t.append(float(r['lap_t']))
            v.append(float(r['speed_kmh']))
    return np.array(t), np.array(v)

def anchors_from_csv(tkey, endt):
    rows = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'track', 'corner_comparison.csv'), encoding='utf-8')):
        rows[int(float(r['s_m']))] = r
    return [0.0] + [float(rows[s][tkey]) for s in S_POS] + [endt]

t_u, v_u = load_clean(os.path.join(ROOT, 'publish', 'assets', '_u9x', 'u9x_clean.csv'))
t_s, v_s = load_clean(os.path.join(ROOT, 'publish', 'assets', '_su7f', 'su7_clean.csv'))
_t_p, _v_p = load_clean(os.path.join(ROOT, 'publish', 'assets', '_p622', 'pot_clean.csv'))

# 原型锚（人工读出 38 谷 t）
PROTO_T = [7.0,14.0,24.0,35.6,49.3,65.0,71.7,95.0,109.0,113.9,121.0,128.0,132.0,142.0,153.1,158.0,169.0,172.0,178.0,180.0,198.0,200.0,205.2,214.0,224.5,234.3,245.7,261.0,271.2,276.6,284.1,295.5,306.0,319.8,326.4,333.6,337.9,376.0]
at_p = [0.0] + PROTO_T + [382.09]

def correct(t, at):
    return np.interp(t, at, [0.0] + S_POS + [20600.0])

s_u = correct(t_u, anchors_from_csv('t_u9x', 419.2))
s_s = correct(t_s, anchors_from_csv('t_su7', 424.9))
s_p = correct(_t_p, at_p)
tp = _t_p
vpi = _v_p

# ---------- 画图 ----------
fig, ax = plt.subplots(figsize=(14, 5.6), dpi=150)
ax.plot(s_u, v_u, color='#c0392b', lw=1.1, label='仰望 U9 Xtreme（6:59.157）')
ax.plot(s_s, v_s, color='#2471a3', lw=1.1, label='SU7 Ultra 量产（7:04.957）')
ax.plot(s_p, vpi, color='#e67e22', lw=1.5, alpha=0.9, label='SU7 Ultra 原型（6:22.091）')

landmarks = [
    (240, 'Antoniusbuche'), (530, 'Hatzenbach'), (1490, 'Hocheichen'),
    (3560, 'Flugplatz'), (5220, 'Aremberg'), (5920, 'Fuchsröhre'),
    (6700, 'Adenauer Forst'), (7400, 'Metzgesfeld'), (8590, 'Wehrseifen'),
    (8900, 'Breidscheid'), (9320, 'Ex-Mühle'), (9780, 'Bergwerk'),
    (10750, 'Kesselchen'), (11550, 'Steilstrecke'), (12000, 'Karussell'),
    (13500, 'Hohe Acht'), (15200, 'Brünnchen'), (16600, 'Pflanzgarten'),
    (17400, 'Galgenkopf'),
]
for pos, name in landmarks:
    ax.axvline(pos, color='#999999', lw=0.6, ls='--', alpha=0.5)
    ax.text(pos, 358, name, rotation=90, va='top', ha='right', fontsize=7.5, color='#555555')

ax.set_xlabel('赛道距离（m，三车按 38 个弯谷对齐）')
ax.set_ylabel('速度（km/h）')
ax.set_ylim(0, 360)
ax.set_title('三车全程速度-距离曲线：U9X / SU7 量产 / SU7 原型（6:22.091）', fontsize=13)
ax.legend(loc='lower right', fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(OUT)
print(f'[完成] {OUT}')

# 快速自检：几个地标处三车速度（±40m 窗口谷）
print('自检（地标处速度，±40m 窗口谷）:')
for pos, name in [(3560,'Flugplatz'), (6700,'AdenauerForst'), (8590,'Wehrseifen'), (9320,'Ex-Mühle'), (16600,'Pflanzgarten')]:
    mu = np.abs(s_u - pos) <= 40
    ms = np.abs(s_s - pos) <= 40
    mp = np.abs(s_p - pos) <= 40
    vu = v_u[mu].min() if mu.sum() else np.nan
    vs = v_s[ms].min() if ms.sum() else np.nan
    vp = vpi[mp].min() if mp.sum() else np.nan
    print('  %-14s U9X %5.1f | 量产 %5.1f | 原型 %5.1f' % (name, vu, vs, vp))
