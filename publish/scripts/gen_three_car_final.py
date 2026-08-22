# -*- coding: utf-8 -*-
"""
三车 25fps 同源全量重算：38 弯对照 + 分域统计 + 输出结论
- U9X：_u9x/u9x_clean.csv；量产：_su7f/su7_clean.csv；原型：_p622/pot_clean.csv
- 距离轴：38 弯锚分段校正（各车用自家锚；U9X/量产锚 t 取自 corner CSV 弯心时刻）
"""
import csv
import os

import numpy as np

ROOT = r'D:\Project\dsh_rally_cars'

# ---------- 38 弯位置（赛道坐标） ----------
S = [240,530,1000,1490,2280,3560,3850,5220,5920,6180,6460,6700,6930,7400,7860,8100,8590,8900,9320,9780,10500,10750,11190,11550,12000,12480,12980,13500,14120,14340,14630,15200,15780,16600,16860,17200,17400,20460]


def load_clean(path):
    t, v = [], []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            t.append(float(r['lap_t']))
            v.append(float(r['speed_kmh']))
    return np.array(t), np.array(v)


def anchors_from_csv(tkey):
    """U9X/量产锚：corner CSV 各弯心位置的 t"""
    rows = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'track', 'corner_comparison.csv'), encoding='utf-8')):
        rows[int(float(r['s_m']))] = r
    at = [0.0]
    for s in S:
        at.append(float(rows[s][tkey]))
    at.append(424.9 if tkey == 't_su7' else 419.2)
    return at


# 原型锚（人工读出 38 谷 t）
PROTO_T = [7.0,14.0,24.0,35.6,49.3,65.0,71.7,95.0,109.0,113.9,121.0,128.0,132.0,142.0,153.1,158.0,169.0,172.0,178.0,180.0,198.0,200.0,205.2,214.0,224.5,234.3,245.7,261.0,271.2,276.6,284.1,295.5,306.0,319.8,326.4,333.6,337.9,376.0]

def build_anchor_corrected(t, s_int, at):
    as_ = [0.0] + S + [20600.0]
    return np.interp(t, at, as_)

# ---------- 加载三车 ----------
t_u, v_u = load_clean(os.path.join(ROOT, 'publish', 'assets', '_u9x', 'u9x_clean.csv'))
t_s, v_s = load_clean(os.path.join(ROOT, 'publish', 'assets', '_su7f', 'su7_clean.csv'))
t_p, v_p = load_clean(os.path.join(ROOT, 'publish', 'assets', '_p622', 'pot_clean.csv'))

at_u = anchors_from_csv('t_u9x')
at_s = anchors_from_csv('t_su7')
s_u = build_anchor_corrected(t_u, None, at_u)
s_s = build_anchor_corrected(t_s, None, at_s)
at_p = [0.0] + PROTO_T + [382.09]
s_p = build_anchor_corrected(t_p, None, at_p)

print('三车 38 弯弯谷对照（25fps 同源，各车锚校正距离 ±40m 窗口取谷）:')
print('%-6s %6s %6s %7s %8s' % ('位置', 'U9X', '量产', '原型', '原-量'))
mass_u = {}
mass_s = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'track', 'corner_comparison.csv'), encoding='utf-8')):
    s0 = int(float(r['s_m']))
    mass_u[s0] = float(r['v_u9x'])
    mass_s[s0] = float(r['v_su7'])

rows = []
for s0 in S:
    xu, xs, xp = np.nan, np.nan, np.nan
    m = np.abs(s_u - s0) <= 40
    if m.sum():
        xu = v_u[m].min()
    m = np.abs(s_s - s0) <= 40
    if m.sum():
        xs = v_s[m].min()
    m = np.abs(s_p - s0) <= 40
    if m.sum():
        xp = v_p[m].min()
    rows.append((s0, xu, xs, xp))
    print('%5dm %6.1f %6.1f %7.1f %+8.1f' % (s0, xu, xs, xp, xp - xs))

def band(v):
    return '低速' if v < 100 else ('中速' if v < 150 else ('高速' if v < 200 else '极高速'))

stats = {}
for s0, xu, xs, xp in rows:
    if np.isnan(xp) or np.isnan(xs):
        continue
    b = band(xs)
    stats.setdefault(b, []).append((xp - xs, xp - xu))
print('\n分域统计:')
for b in ['低速', '中速', '高速', '极高速']:
    ds = stats.get(b, [])
    if ds:
        d_ps = np.mean([d[0] for d in ds])
        d_pu = np.mean([d[1] for d in ds])
        print('  %-4s: %2d 弯  原型-量产 %+5.1f km/h (%+4.1f%%)   原型-U9X %+5.1f (%+4.1f%%)' % (
            b, len(ds), d_ps, d_ps / 100 * 100, d_pu, d_pu / 100 * 100))
