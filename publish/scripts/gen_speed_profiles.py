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

# ---------- U9X / 量产 ----------
s_g, v_u, v_s = [], [], []
with open(os.path.join(ROOT, 'track', 'corner_comparison.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        s_g.append(float(r['s_m']))
        v_u.append(float(r['v_u9x']))
        v_s.append(float(r['v_su7']))
s_g = np.array(s_g); v_u = np.array(v_u); v_s = np.array(v_s)

# ---------- 原型 OCR 轨道（高清 mp4 1s） ----------
raw = {}
for line in open(os.path.join(ROOT, 'publish', 'assets', '_p622', 'mp4s_ocr.txt'), encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 2:
        continue
    m = re.match(r's(\d+)\.jpg', parts[0])
    if not m:
        continue
    n = int(m.group(1))
    text = re.sub(r'\d{1,2}[:：]\d{2}\s*[,，.]?\s*\d*', ' ', parts[1])
    nums = [int(x) for x in re.findall(r'\d{1,3}', text)]
    if nums:
        raw[n] = nums
# 连续性+百位补全
seq = []
prev = None
for n in sorted(raw):
    cands = [x for x in raw[n] if 10 <= x <= 400]
    if not cands:
        seq.append((n, None))
        continue
    if prev is None:
        big = [x for x in cands if x >= 60]
        v = max(big) if big else (max(cands) + 200 if max(cands) < 60 else max(cands))
    else:
        c2 = []
        for x in cands:
            c2.append(x)
            if x < 100 and 100 + x <= 400 and abs(100 + x - prev) < 60:
                c2.append(100 + x)
            if x < 100 and 200 + x <= 400 and abs(200 + x - prev) < 60:
                c2.append(200 + x)
        v = min(c2, key=lambda x: abs(x - prev))
    seq.append((n, v))
    prev = v
tp = np.array([n for n, v in seq], dtype=float)
vp = np.array([v if v is not None else np.nan for n, v in seq], dtype=float)
valid = ~np.isnan(vp)
for i in range(1, len(vp) - 1):
    if valid[i] and (valid[i-1] or valid[i+1]):
        ref = vp[i-1] if valid[i-1] else vp[i+1]
        if abs(vp[i] - ref) > 45:
            vp[i] = np.nan
valid = ~np.isnan(vp)
idx = np.where(valid)[0]
vpi = np.interp(tp, tp[idx], vp[idx])

# ---------- 38 谷人工读数（t, v）与量产弯谷位置 s ----------
corners = [
    (7.0, 85, 240), (14.0, 182, 530), (24.0, 124, 1000), (35.6, 104, 1490),
    (49.3, 205, 2280), (65.0, 232, 3560), (71.7, 109, 3850), (95.0, 84, 5220),
    (109.0, 187, 5920), (113.9, 115, 6180), (121.0, 101, 6460), (132.0, 159, 6700),
    (139.0, 139, 6930), (142.0, 76, 7400), (153.1, 120, 7860), (158.0, 117, 8100),
    (169.0, 216, 8590), (172.0, 111, 8900), (178.0, 215, 9320), (180.0, 244, 9780),
    (198.0, 246, 10500), (200.0, 203, 10750), (205.2, 237, 11190), (214.0, 92, 11550),
    (224.5, 91, 12000), (234.3, 198, 12480), (245.7, 119, 12980), (261.0, 133, 13500),
    (271.2, 125, 14120), (276.6, 117, 14340), (284.1, 105, 14630), (295.5, 155, 15200),
    (306.0, 213, 15780), (319.8, 133, 16600), (326.4, 112, 16860), (333.6, 153, 17200),
    (337.9, 183, 17400), (376.0, 91, 20460),
]

# 人工谷覆盖进轨道：先插值到 1s 连续网格，再按时间覆盖（弯谷不被平滑掉）
t_grid = np.arange(0, 383, 1.0)
v_grid = np.interp(t_grid, tp, vpi)
for tt, vv, ss in corners:
    i = int(round(tt))
    if 0 <= i < len(t_grid):
        v_grid[i] = vv
        v_grid[max(0, i-1)] = min(v_grid[max(0, i-1)], vv)  # 邻帧下拉，保谷形
        v_grid[min(len(t_grid)-1, i+1)] = min(v_grid[min(len(t_grid)-1, i+1)], vv)
tp = t_grid
vpi = v_grid

# ---------- 弯谷序号对齐：t_proto → s 分段线性 ----------
anchors_t = [0.0] + [c[0] for c in corners] + [382.09]
anchors_s = [0.0] + [c[2] for c in corners] + [20600.0]
s_proto = np.interp(tp, anchors_t, anchors_s)

# ---------- 画图 ----------
fig, ax = plt.subplots(figsize=(14, 5.6), dpi=150)
ax.plot(s_g, v_u, color='#c0392b', lw=1.1, label='仰望 U9 Xtreme（6:59.157）')
ax.plot(s_g, v_s, color='#2471a3', lw=1.1, label='SU7 Ultra 量产（7:04.957）')
ax.plot(s_proto, vpi, color='#e67e22', lw=1.5, alpha=0.9, label='SU7 Ultra 原型（6:22.091）')

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

# 快速自检：几个地标处三车速度
print('自检（地标处速度）:')
for pos, name in [(3560,'Flugplatz'), (6700,'AdenauerForst'), (8590,'Wehrseifen'), (9320,'Ex-Mühle'), (16600,'Pflanzgarten')]:
    iu = np.argmin(np.abs(s_g - pos))
    ip = np.argmin(np.abs(s_proto - pos))
    print('  %-14s U9X %5.1f | 量产 %5.1f | 原型 %5.1f' % (name, v_u[iu], v_s[iu], vpi[ip]))
