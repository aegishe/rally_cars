"""
U9X vs SU7 Ultra: 按物理分段重新对账
段界 = 速度局部极值 (时间域峰谷交替):
  [减速段] 峰(刹车点) -> 谷(弯心), a<0
  [加速段] 谷(弯心)   -> 峰(刹车点), a>0   (出弯加速+弯间加速连续一体)
段界映射到距离域后配对, 逐段对比两车用时
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

# 时间域累计距离
def cumdist(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    tt, vv = t[m], v[m]
    s = np.zeros_like(tt)
    for i in range(1, len(tt)):
        s[i] = s[i-1] + (vv[i-1]+vv[i])/2/3.6*(tt[i]-tt[i-1])
    return tt, s, vv

tu, su, vu = cumdist(t_u, v_u, 0.0, 419.2)
ts_, ss_, vs_ = cumdist(t_s, v_s, 0.72, 424.9)

def extrema(t, v):
    """3点平滑后找峰谷, 强制 P/V 交替; 返回 [(kind, orig_idx, v)]"""
    k = np.ones(3) / 3.0
    vs = np.convolve(v, k, mode='valid')   # 长度 n-2, 对应原索引 1..n-2
    pts = []
    for i in range(1, len(vs) - 1):
        is_p = vs[i] > vs[i-1] and vs[i] >= vs[i+1]
        is_v = vs[i] < vs[i-1] and vs[i] <= vs[i+1]
        if not (is_p or is_v):
            continue
        kind = 'P' if is_p else 'V'
        if pts and pts[-1][0] == kind:
            j = pts[-1][1]
            if (kind == 'P' and vs[i] > vs[j]) or (kind == 'V' and vs[i] < vs[j]):
                pts[-1] = (kind, i)
        else:
            pts.append((kind, i))
    return [(knd, j + 1, v[j + 1]) for (knd, j) in pts]

ext_u = extrema(tu, vu)
ext_s = extrema(ts_, vs_)
print(f"U9X 极值点: {len(ext_u)} 个, SU7: {len(ext_s)} 个")

def build_segments(t, ext, s, v):
    segs = []
    for k in range(len(ext)-1):
        k1, k2 = ext[k], ext[k+1]
        i1, i2 = k1[1], k2[1]
        segs.append({
            'type': '减速' if k1[0] == 'P' else '加速',
            's1': s[i1], 's2': s[i2],
            'v1': v[i1], 'v2': v[i2],
            'dt': t[i2] - t[i1],
            'i1': i1, 'i2': i2,
        })
    return segs

segs_u = build_segments(tu, ext_u, su, vu)
segs_s = build_segments(ts_, ext_s, ss_, vs_)

# 配对: 按段中点距离, 类型一致, 中点差<120m
pairs = []
for su_seg in segs_u:
    mid = (su_seg['s1'] + su_seg['s2']) / 2
    best = None
    for ss_seg in segs_s:
        if ss_seg['type'] != su_seg['type']:
            continue
        mid2 = (ss_seg['s1'] + ss_seg['s2']) / 2
        if abs(mid - mid2) < 120:
            if best is None or abs(mid - mid2) < abs(mid - best['d']):
                best = {'seg': ss_seg, 'd': abs(mid - mid2)}
    if best:
        pairs.append((su_seg, best['seg']))

print(f"配对的段: {len(pairs)} 个")
print(f"\n{'类型':>4} | {'中点距离':>8} | {'U9X用时':>8} | {'SU7用时':>8} | {'差(SU7-U9X)':>11}")
dec_acc = {'减速': [], '加速': []}
for a, b in pairs:
    mid = (a['s1'] + a['s2']) / 2
    d = b['dt'] - a['dt']
    dec_acc[a['type']].append(d)
    print(f"{a['type']:>4} | {mid:8.0f}m | {a['dt']:8.2f}s | {b['dt']:8.2f}s | {d:+11.2f}s")

print("\n" + "=" * 50)
for typ in ['减速', '加速']:
    ds = dec_acc[typ]
    print(f"{typ}段: {len(ds)}段, U9X净赚合计 {np.sum(ds):+.2f}s, 平均 {np.mean(ds):+.2f}s/段")
    pos = sum(1 for d in ds if d > 0.05)
    neg = sum(1 for d in ds if d < -0.05)
    print(f"   U9X赚 {pos} 段 / 平 {len(ds)-pos-neg} / SU7赚 {neg} 段")

total = np.sum(dec_acc['减速']) + np.sum(dec_acc['加速'])
print(f"\n对账: 减速段 {np.sum(dec_acc['减速']):+.2f}s + 加速段 {np.sum(dec_acc['加速']):+.2f}s = {total:+.2f}s (总圈速差 5.7s)")

# 刹车点早晚对比 (峰位置 = 刹车点)
print("\n各刹车点位置差 (U9X峰距离 - SU7峰距离, 正=U9X刹车更晚):")
n = 0
for a, b in pairs:
    if a['type'] == '减速':
        n += 1
        print(f"  {n:2d}. U9X峰@{a['s1']:6.0f}m(v={a['v1']:.0f})  SU7峰@{b['s1']:6.0f}m(v={b['v1']:.0f})  差 {a['s1']-b['s1']:+.0f}m")
