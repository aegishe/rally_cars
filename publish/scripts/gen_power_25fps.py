# -*- coding: utf-8 -*-
"""
U9X / SU7 量产 25fps 功率反推（与 power_analysis_5fps 同模型，±0.25s 滑动回归窗口）
P = (m·a + F_drag + F_rr) · v
输出：分段峰值 + 全圈峰值 + 兑现率
"""
import csv
import os

import numpy as np

ROOT = r'D:\Project\dsh_rally_cars'

def load(path):
    t, v = [], []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            t.append(float(r['lap_t']))
            v.append(float(r['speed_kmh']))
    return np.array(t), np.array(v)

def power_profile(t, v, m, CdA, Crr):
    """滑动回归加速度 → 功率"""
    dt = np.median(np.diff(t))
    win = max(3, int(round(0.25 / dt)))  # ±0.25s 窗口（奇数点）
    half = win // 2
    a = np.full(len(v), np.nan)
    for i in range(half, len(v) - half):
        seg = slice(i - half, i + half + 1)
        k, b = np.polyfit(t[seg], v[seg] / 3.6, 1)
        a[i] = k
    v_ms = v / 3.6
    rho = 1.225
    F_drag = 0.5 * rho * CdA * v_ms ** 2
    F_rr = Crr * m * 9.81
    P = (m * np.maximum(a, 0) + F_drag + F_rr) * v_ms
    return t, v, a, P

# U9X：m=2555（2480+75）, CdA=0.67, Crr=0.012
t_u, v_u = load(os.path.join(ROOT, 'publish', 'assets', '_u9x', 'u9x_clean.csv'))
t_u, v_u, a_u, P_u = power_profile(t_u, v_u, 2555, 0.67, 0.012)
# SU7 量产：m=2435（2360+75）, CdA 假设 0.65（小米未公布，按同类取）, Crr=0.012
t_s, v_s = load(os.path.join(ROOT, 'publish', 'assets', '_su7f', 'su7_clean.csv'))
t_s, v_s, a_s, P_s = power_profile(t_s, v_s, 2435, 0.65, 0.012)

print('====== U9X 25fps 功率反推 ======')
# 分段（Laptime 区间沿用篇2 分段）
segs = [('起步暖胎', 0, 25), ('第一长直道', 40, 75), ('中段加速', 190, 230), ('Döttinger', 340, 400)]
for name, lo, hi in segs:
    m = (t_u >= lo) & (t_u <= hi) & (P_u > 0)
    if m.sum():
        i = np.where(m)[0][np.argmax(P_u[m])]
        print('  %-8s 峰值 %6.0f kW @ %.0fkm/h  t=%.1fs' % (name, P_u[i], v_u[i], t_u[i]))
m = P_u > 0
i = np.where(m)[0][np.argmax(P_u[m])]
print('  全圈峰值 %6.0f kW @ %.0fkm/h  t=%.1fs (兑现率 %.0f%% @2220kW)' % (P_u[i], v_u[i], t_u[i], P_u[i] / 2220 * 100))
print('  加速度峰值 %.2f g' % (np.nanmax(a_u) / 9.81))

print('\n====== SU7 量产 25fps 功率反推 ======')
for name, lo, hi in segs:
    m = (t_s >= lo) & (t_s <= hi) & (P_s > 0)
    if m.sum():
        i = np.where(m)[0][np.argmax(P_s[m])]
        print('  %-8s 峰值 %6.0f kW @ %.0fkm/h  t=%.1fs' % (name, P_s[i], v_s[i], t_s[i]))
m = P_s > 0
i = np.where(m)[0][np.argmax(P_s[m])]
print('  全圈峰值 %6.0f kW @ %.0fkm/h  t=%.1fs (兑现率 %.0f%% @1138kW)' % (P_s[i], v_s[i], t_s[i], P_s[i] / 1138 * 100))

# Döttinger 收油点：18-19.2km（三车）
print('\n====== Döttinger 尾段收油点（速度峰值→下降点） ======')
t_p, v_p = load(os.path.join(ROOT, 'publish', 'assets', '_p622', 'pot_clean.csv'))
# 用时间域：量产 Döttinger 在 t≈355-405；U9X t≈350-415；原型 t≈340-375（各自圈速比例）
for name, t_, v_, tlo, thi in [('U9X', t_u, v_u, 350, 419), ('量产', t_s, v_s, 355, 425), ('原型', t_p, v_p, 335, 382)]:
    m = (t_ >= tlo) & (t_ <= thi)
    vv = v_[m]; tt = t_[m]
    if len(vv) < 5:
        continue
    imax = np.argmax(vv)
    # 峰值后的首个下降持续点（收油/刹车点）
    drop = None
    for j in range(imax + 2, len(vv) - 2):
        if vv[j] < vv[j - 1] - 1.5 and vv[j + 1] < vv[j] - 1.5:
            drop = j
            break
    print('  %-4s 峰值 %3.0fkm/h @t=%.1fs%s' % (name, vv[imax], tt[imax],
          ('  收油点 t=%.1fs (%.0fkm/h)' % (tt[drop], vv[drop])) if drop else '  （无下降/限速平台）'))
