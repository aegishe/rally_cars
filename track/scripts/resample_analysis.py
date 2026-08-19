"""
5fps 重采数据验证分析
1. 每段找峰(松油点)/谷(弯心) 精确位置 (±0.2s)
2. 减速段减速度重算 a = (v_peak^2 - v_valley^2) / (2d), d 用 5fps 积分
3. 与 1s 采样结论对比: 松油点位置差、减速度倍率 (动能回收假说)
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

SEGS = [
    ('A 12.4km 减速段', 'u9x', 252.0, 265.0, 'su7', 255.0, 268.0),
    ('B 16.8km 减速段', 'u9x', 354.0, 364.0, 'su7', 357.0, 368.0),
    ('C Döttinger 直道', 'u9x', 369.0, 401.0, 'su7', 374.0, 407.0),
]

def peaks_valleys(t, v):
    """返回 (峰列表, 谷列表), 每项 (t, v); 允许等值平台"""
    vsm = np.convolve(v, np.ones(3)/3, mode='same')
    pks, vls = [], []
    for i in range(2, len(vsm)-2):
        if vsm[i] >= vsm[i-1] and vsm[i] >= vsm[i-2] and vsm[i] >= vsm[i+1] and vsm[i] >= vsm[i+2] \
           and (vsm[i] > vsm[i-1] or vsm[i] > vsm[i+1]):
            if not pks or t[i] - pks[-1][0] > 1.0:
                pks.append((t[i], v[i]))
        if vsm[i] <= vsm[i-1] and vsm[i] <= vsm[i-2] and vsm[i] <= vsm[i+1] and vsm[i] <= vsm[i+2] \
           and (vsm[i] < vsm[i-1] or vsm[i] < vsm[i+1]):
            if not vls or t[i] - vls[-1][0] > 1.0:
                vls.append((t[i], v[i]))
    return pks, vls

def seg_data(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    return t[m], v[m]

def decel_between(t, v, t_peak, t_valley):
    """峰->谷减速度"""
    m = (t >= t_peak) & (t <= t_valley)
    if np.sum(m) < 2:
        return None
    tt, vv = t[m], v[m]
    d = 0.0
    for i in range(len(tt)-1):
        d += (vv[i]+vv[i+1])/2/3.6*(tt[i+1]-tt[i])
    a = (vv[0]**2 - vv[-1]**2) / (2*d*12.96)  # m/s2
    return {'t_peak': tt[0], 't_valley': tt[-1], 'v_peak': vv[0], 'v_valley': vv[-1], 'd': d, 'a': a, 'a_g': a/9.81}

print("=" * 78)
print("5fps 重采: 减速段减速度重算")
print("=" * 78)
for name, cu, tu0, tu1, cs, ts0, ts1 in SEGS:
    tu_s, vu_s = seg_data(tu, vu, tu0, tu1)
    ts_s, vs_s = seg_data(ts, vs, ts0, ts1)
    pks_u, vls_u = peaks_valleys(tu_s, vu_s)
    pks_s, vls_s = peaks_valleys(ts_s, vs_s)
    print(f"\n[{name}]")
    print(f"  U9X 峰: {[f'{t:.1f}s@{v:.0f}' for t, v in pks_u]}")
    print(f"  U9X 谷: {[f'{t:.1f}s@{v:.0f}' for t, v in vls_u]}")
    print(f"  SU7 峰: {[f'{t:.1f}s@{v:.0f}' for t, v in pks_s]}")
    print(f"  SU7 谷: {[f'{t:.1f}s@{v:.0f}' for t, v in vls_s]}")
# 配对峰->谷 (按时间顺序, 每段取第一个有效峰-谷对)
def decel_compare(du_s, ds_s, p_u, v_u2, p_s, v_s2):
    du = decel_between(du_s[0], du_s[1], p_u[0], v_u2[0])
    ds = decel_between(ds_s[0], ds_s[1], p_s[0], v_s2[0])
    if du and ds:
        ratio = du['a_g'] / ds['a_g'] if ds['a_g'] > 0.01 else float('inf')
        print(f"  U9X: {du['v_peak']:.0f}->{du['v_valley']:.0f}km/h @ {du['t_peak']:.1f}-{du['t_valley']:.1f}s "
              f"({du['d']:.0f}m, {du['a_g']:.2f}g)")
        print(f"  SU7: {ds['v_peak']:.0f}->{ds['v_valley']:.0f}km/h @ {ds['t_peak']:.1f}-{ds['t_valley']:.1f}s "
              f"({ds['d']:.0f}m, {ds['a_g']:.2f}g)")
        print(f"  减速度比值 U9X/SU7 = {ratio:.2f}")
        return du, ds
    return None, None

print("\n" + "=" * 70)
print("减速段减速度对比 (5fps)")
print("=" * 70)
for name, cu, tu0, tu1, cs, ts0, ts1 in SEGS:
    tu_s, vu_s = seg_data(tu, vu, tu0, tu1)
    ts_s, vs_s = seg_data(ts, vs, ts0, ts1)
    pks_u, vls_u = peaks_valleys(tu_s, vu_s)
    pks_s, vls_s = peaks_valleys(ts_s, vs_s)
    print(f"\n[{name}]")
    # 第一个有效 峰->谷 对
    done = False
    for iu in range(len(pks_u)):
        for iv in range(len(vls_u)):
            if vls_u[iv][0] > pks_u[iu][0] + 0.5:
                for is_ in range(len(pks_s)):
                    for iv2 in range(len(vls_s)):
                        if vls_s[iv2][0] > pks_s[is_][0] + 0.5:
                            du, ds = decel_compare((tu_s, vu_s), (ts_s, vs_s),
                                                   pks_u[iu], vls_u[iv], pks_s[is_], vls_s[iv2])
                            done = True
                            break
                    if done:
                        break
                break
        if done:
            break

# 直道段: 低谷 -> 刹车点 用时 (5fps 口径)
print("\n" + "=" * 70)
print("Döttinger 直道 (5fps): 低谷 -> 刹车点")
print("=" * 70)
straight = [('U9X', tu, vu, 372.4, 395.8), ('SU7', ts, vs, 377.8, 401.8)]
for car, t_all, v_all, t_val, t_brk in straight:
    t_s, v_s = seg_data(t_all, v_all, t_val - 0.6, t_brk + 0.6)
    r = decel_between(t_s, v_s, t_val, t_brk)
    if r:
        print(f"  {car}: 低谷 {t_val:.1f}s@{r['v_valley']:.0f} -> 峰 {t_brk:.1f}s@{r['v_peak']:.0f}  用时 {t_brk-t_val:.1f}s  距离 {r['d']:.0f}m")
