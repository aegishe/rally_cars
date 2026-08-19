"""
刹车点->弯心距离对比 (V型走线量化)
方法: 5fps 数据积分距离 s(t), 减速段 = 峰(松油点)->谷(弯心)
      刹车距离 d = s_apex - s_peak (各车自己的距离积分)
V型走线特征: 刹车距离更短 (同样减速幅度, 更晚刹车+更大减速度)
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

def cumdist(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    tt, vv = t[m], v[m]
    s = np.zeros_like(tt)
    for i in range(1, len(tt)):
        s[i] = s[i-1] + (vv[i-1] + vv[i]) / 2 / 3.6 * (tt[i] - tt[i-1])
    return tt, s, vv

tu_c, su, vu_c = cumdist(tu, vu, 0.0, 419.2)
ts_c, ss_, vs_c = cumdist(ts, vs, 0.0, 424.9)

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

def decel_segs(t, v, s, ext):
    segs = []
    for k in range(len(ext) - 1):
        if ext[k][0] == 'P' and ext[k+1][0] == 'V':
            i1, i2 = ext[k][1], ext[k+1][1]
            d = s[i2] - s[i1]
            if d < 50:
                continue
            segs.append({'s_peak': s[i1], 's_apex': s[i2], 'd': d,
                         'vp': v[i1], 'vv': v[i2],
                         'a': (v[i1]**2 - v[i2]**2) / (2 * d * 12.96) / 9.81})
    return segs

segs_u = decel_segs(tu_c, vu_c, su, ext_u)
segs_s = decel_segs(ts_c, vs_c, ss_, ext_s)

# 配对 (双锚点: 谷位<90m 且 峰位<150m)
pairs = []
used = set()
for a in segs_u:
    best = None
    for j, b in enumerate(segs_s):
        if j in used:
            continue
        if abs(a['s_apex'] - b['s_apex']) < 90 and abs(a['s_peak'] - b['s_peak']) < 150:
            if best is None or abs(a['s_apex'] - b['s_apex']) < abs(a['s_apex'] - best['s_apex']):
                best = b
                best_j = j
    if best:
        pairs.append((a, best))
        used.add(best_j)
print(f"配对减速段 {len(pairs)}")

print(f"\n{'位置':>6} | {'U9X 峰位':>8} | {'SU7 峰位':>8} | {'峰位差':>7} | {'U9X刹车距':>9} | {'SU7刹车距':>9} | {'距差':>7} | {'弯心速':>6} | 档位")
results = []
for a, b in pairs:
    s_apex = a['s_apex']
    d_peak = a['s_peak'] - b['s_peak']          # 正=U9X松油点更靠后
    d_brake = b['d'] - a['d']                    # 正=SU7刹车距离更长
    vv_ref = a['vv']
    band = '低速' if vv_ref < 100 else ('中速' if vv_ref < 150 else ('高速' if vv_ref < 200 else '极高速'))
    results.append((s_apex, d_peak, a['d'], b['d'], d_brake, vv_ref, band))
    print(f"{s_apex:6.0f}m | {a['s_peak']:8.0f}m | {b['s_peak']:8.0f}m | {d_peak:+7.0f}m | {a['d']:9.0f}m | {b['d']:9.0f}m | {d_brake:+7.0f}m | {vv_ref:6.0f} | {band}")

print("\n" + "=" * 60)
print("分档统计:")
for band in ['低速', '中速', '高速', '极高速']:
    rs = [r for r in results if r[6] == band]
    if rs:
        dp = np.mean([r[1] for r in rs])
        db = np.mean([r[4] for r in rs])
        n_late = sum(1 for r in rs if r[1] > 5)   # U9X 松油更晚
        n_short = sum(1 for r in rs if r[4] > 5)  # SU7 刹车距离更长(U9X更短)
        print(f"  {band}: {len(rs)}段  峰位差平均 {dp:+.0f}m (U9X晚 {n_late}/{len(rs)})  "
              f"刹车距离差平均 {db:+.0f}m (U9X短 {n_short}/{len(rs)})")

dp_all = np.mean([r[1] for r in results])
db_all = np.mean([r[4] for r in results])
n_late_all = sum(1 for r in results if r[1] > 5)
n_short_all = sum(1 for r in results if r[4] > 5)
print(f"\n全圈 {len(results)} 段:")
print(f"  松油点位置差平均: {dp_all:+.0f}m  (U9X 更晚松油: {n_late_all}/{len(results)} 段)")
print(f"  刹车距离差平均:   {db_all:+.0f}m  (U9X 刹车距离更短: {n_short_all}/{len(results)} 段)")
