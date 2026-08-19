"""
全圈 5fps 减速段账本
数据: track/u9x_5fps.csv, track/su7_5fps.csv (全圈, lap_offset 校准)
方法: 时间域峰谷检测 -> 距离域配对 -> 每减速段减速度 a=(vp^2-vv^2)/(2d)
输出: 全 38 减速段对比 + 分档统计 + 与 1s 口径对照
"""
import csv
import numpy as np

def load(path):
    ts, vs = [], []
    with open(path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            ts.append(float(row[0]))
            vs.append(float(row[1]))
    return np.array(ts), np.array(vs)

tu, vu = load(r'D:\Project\dsh_rally_cars\track\u9x_5fps.csv')
ts, vs = load(r'D:\Project\dsh_rally_cars\track\su7_5fps.csv')

# 时间域累计距离
def cumdist(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    tt, vv = t[m], v[m]
    s = np.zeros_like(tt)
    for i in range(1, len(tt)):
        s[i] = s[i-1] + (vv[i-1] + vv[i]) / 2 / 3.6 * (tt[i] - tt[i-1])
    return tt, s, vv

tu_c, su, vu_c = cumdist(tu, vu, 0.0, 419.2)
ts_c, ss_, vs_c = cumdist(ts, vs, 0.0, 424.9)
print(f"U9X 总距离 {su[-1]:.0f}m, SU7 {ss_[-1]:.0f}m")

# 时间域峰谷 (5点窗口平滑, 强制交替)
def extrema(t, v):
    k = np.ones(5) / 5.0
    vsm = np.convolve(v, k, mode='same')
    pts = []
    for i in range(3, len(vsm) - 3):
        is_p = vsm[i] >= np.max(vsm[i-3:i+4]) and vsm[i] > vsm[i-1] and vsm[i] > vsm[i+1]
        is_v = vsm[i] <= np.min(vsm[i-3:i+4]) and vsm[i] < vsm[i-1] and vsm[i] < vsm[i+1]
        if not (is_p or is_v):
            continue
        kind = 'P' if is_p else 'V'
        if pts and pts[-1][0] == kind:
            j = pts[-1][1]
            if (kind == 'P' and v[i] > v[j]) or (kind == 'V' and v[i] < v[j]):
                pts[-1] = (kind, i)
        else:
            pts.append((kind, i))
    return pts

ext_u = extrema(tu_c, vu_c)
ext_s = extrema(ts_c, vs_c)
print(f"U9X 峰谷 {len(ext_u)} 个, SU7 {len(ext_s)} 个")

# 减速段: 峰->谷
def decel_segs(t, v, s, ext):
    segs = []
    for k in range(len(ext) - 1):
        if ext[k][0] == 'P' and ext[k+1][0] == 'V':
            i1, i2 = ext[k][1], ext[k+1][1]
            d = s[i2] - s[i1]
            if d < 30:   # 距离太短不可信
                continue
            a = (v[i1]**2 - v[i2]**2) / (2 * d * 12.96) / 9.81  # g
            segs.append({'s1': s[i1], 's2': s[i2], 'vp': v[i1], 'vv': v[i2],
                         'd': d, 'a': a, 't1': t[i1], 't2': t[i2]})
    return segs

segs_u = decel_segs(tu_c, vu_c, su, ext_u)
segs_s = decel_segs(ts_c, vs_c, ss_, ext_s)
print(f"U9X 减速段 {len(segs_u)}, SU7 {len(segs_s)}")

# 配对 (中点距离 <90m)
pairs = []
for a in segs_u:
    mid = (a['s1'] + a['s2']) / 2
    best = None
    for b in segs_s:
        mid2 = (b['s1'] + b['s2']) / 2
        if abs(mid - mid2) < 90:
            if best is None or abs(mid - mid2) < abs(mid - best['dm']):
                best = {'seg': b, 'dm': abs(mid - mid2)}
    if best:
        pairs.append((a, best['seg']))
print(f"配对减速段 {len(pairs)}")

print(f"\n{'位置':>6} | {'U9X 减速':>12} | {'SU7 减速':>12} | {'a(U9X)':>7} | {'a(SU7)':>7} | {'比值':>5} | 档位")
results = []
for a, b in pairs:
    mid = (a['s1'] + a['s2']) / 2
    ratio = a['a'] / b['a'] if b['a'] > 0.02 else float('inf')
    vv_ref = a['vv']
    band = '低速' if vv_ref < 100 else ('中速' if vv_ref < 150 else ('高速' if vv_ref < 200 else '极高速'))
    results.append((mid, a, b, ratio, band))
    print(f"{mid:6.0f}m | {a['vp']:4.0f}->{a['vv']:3.0f} | {b['vp']:4.0f}->{b['vv']:3.0f} | {a['a']:6.2f}g | {b['a']:6.2f}g | {ratio:5.2f} | {band}")

print("\n" + "=" * 60)
print("分档统计 (5fps 全圈):")
for band in ['低速', '中速', '高速', '极高速']:
    rs = [r for r in results if r[4] == band]
    if rs:
        rs_u = [r[1]['a'] for r in rs]
        rs_s = [r[2]['a'] for r in rs]
        n_u9 = sum(1 for r in rs if r[3] > 1.2)
        n_eq = sum(1 for r in rs if 0.8 <= r[3] <= 1.2)
        n_su7 = sum(1 for r in rs if r[3] < 0.8)
        print(f"  {band}: {len(rs)}段  平均减速度 U9X {np.mean(rs_u):.2f}g vs SU7 {np.mean(rs_s):.2f}g  "
              f"(U9X猛 {n_u9} / 相当 {n_eq} / SU7猛 {n_su7})")

# 汇总
all_a_u = [r[1]['a'] for r in results]
all_a_s = [r[2]['a'] for r in results]
print(f"\n全圈减速段: U9X 平均 {np.mean(all_a_u):.3f}g vs SU7 {np.mean(all_a_s):.3f}g")
print(f"U9X > SU7×1.2 的段: {sum(1 for r in results if r[3] > 1.2)}/{len(results)}")
print(f"SU7 > U9X×1.25 的段: {sum(1 for r in results if r[3] < 0.8)}/{len(results)}")
