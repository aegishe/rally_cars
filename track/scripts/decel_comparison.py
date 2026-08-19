"""
验证假说: U9X 减速段减速度是否系统性大于 SU7 (动能回收假说)
减速段 = 速度峰(松油点) -> 速度谷(弯心), 同一赛道段
a_avg = (v_peak^2 - v_valley^2) / (2 * d)  距离域, 不受1秒采样量化影响
"""
import csv
import numpy as np

def load(path):
    ts, vs = [], []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            ts.append(float(row[0]))
            vs.append(float(row[1]))
    return np.array(ts), np.array(vs)

t_u, v_u = load(r'D:\Project\dsh_rally_cars\track\U9X_power_analysis.csv')
t_s, v_s = load(r'D:\Project\dsh_rally_cars\track\SU7_power_analysis.csv')

def cumdist(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    tt, vv = t[m], v[m]
    s = np.zeros_like(tt)
    for i in range(1, len(tt)):
        s[i] = s[i-1] + (vv[i-1]+vv[i])/2/3.6*(tt[i]-tt[i-1])
    return tt, s, vv

tu, su, vu = cumdist(t_u, v_u, 0.0, 419.2)
ts_, ss_, vs_ = cumdist(t_s, v_s, 0.72, 424.9)

def extrema(v):
    k = np.ones(3)/3.0
    vsm = np.convolve(v, k, mode='valid')
    pts = []
    for i in range(1, len(vsm)-1):
        is_p = vsm[i] > vsm[i-1] and vsm[i] >= vsm[i+1]
        is_v = vsm[i] < vsm[i-1] and vsm[i] <= vsm[i+1]
        if not (is_p or is_v):
            continue
        kind = 'P' if is_p else 'V'
        if pts and pts[-1][0] == kind:
            j = pts[-1][1]
            if (kind == 'P' and vsm[i] > vsm[j]) or (kind == 'V' and vsm[i] < vsm[j]):
                pts[-1] = (kind, i)
        else:
            pts.append((kind, i))
    return [(knd, j+1, v[j+1]) for (knd, j) in pts]

ext_u = extrema(vu)
ext_s = extrema(vs_)

def decel_segments(ext, s, v):
    segs = []
    for k in range(len(ext)-1):
        if ext[k][0] == 'P' and ext[k+1][0] == 'V':
            i1, i2 = ext[k][1], ext[k+1][1]
            vp, vv = v[i1], v[i2]
            d = s[i2] - s[i1]
            a = (vp**2 - vv**2) / (2 * d * 12.96)  # (km/h)^2 / (2*d*m * 3.6^2) -> m/s2
            segs.append({'s1': s[i1], 's2': s[i2], 'vp': vp, 'vv': vv, 'd': d, 'a': a})
    return segs

segs_u = decel_segments(ext_u, su, vu)
segs_s = decel_segments(ext_s, ss_, vs_)
print(f"U9X 减速段 {len(segs_u)} 个, SU7 {len(segs_s)} 个")

# 配对 (中点距离<100m)
pairs = []
for a in segs_u:
    mid = (a['s1']+a['s2'])/2
    best = None
    for b in segs_s:
        mid2 = (b['s1']+b['s2'])/2
        if abs(mid-mid2) < 100:
            if best is None or abs(mid-mid2) < abs(mid-best[0]):
                best = (abs(mid-mid2), b)
    if best:
        pairs.append((a, best[1]))

print(f"配对减速段 {len(pairs)} 个\n")
print(f"{'位置':>7} | {'U9X 速度':>9} | {'SU7 速度':>9} | {'U9X减速度':>9} | {'SU7减速度':>9} | {'比值':>5} | {'段长差':>6}")
diffs = []
for a, b in pairs:
    mid = (a['s1']+a['s2'])/2
    ratio = a['a']/b['a'] if b['a'] > 0.01 else float('inf')
    diffs.append((mid, a['a'], b['a'], ratio, a['vp']-b['vp']))
    print(f"{mid:7.0f} | {a['vp']:4.0f}->{a['vv']:3.0f} | {b['vp']:4.0f}->{b['vv']:3.0f} | {a['a']:8.2f}g | {b['a']:8.2f}g | {ratio:5.2f} | {a['d']-b['d']:+6.0f}m")

a_u = np.array([d[1] for d in diffs])
a_s = np.array([d[2] for d in diffs])
print("\n" + "=" * 50)
print(f"U9X 平均减速度: {np.mean(a_u):.3f}g  中位 {np.median(a_u):.3f}g")
print(f"SU7 平均减速度: {np.mean(a_s):.3f}g  中位 {np.median(a_s):.3f}g")
print(f"U9X 减速度 > SU7 的段: {np.sum(a_u > a_s + 0.02)} / {len(diffs)}")
print(f"SU7 减速度 > U9X 的段: {np.sum(a_s > a_u + 0.02)} / {len(diffs)}")
print(f"\n分段减速度差均值: {np.mean(a_u-a_s):+.3f}g")
