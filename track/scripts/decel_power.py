"""
U9X/SU7 减速功率反推
方法: 减速段 (a<0) 逐点算 P_decel = (m*(-a) - F_drag - F_rr) * v  (制动力做功功率)
      其中 F_drag/F_rr 是"免费"减速力, 其余由制动系统(机械刹车+电机回收)吸收
对比: 前轴电机账面 2x555kW=1110kW, 电池充电功率上限估计
输出: 峰值减速功率 + 全圈减速功率分布
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

def decel_power(t, v, m, CdA, name):
    rho, g0, crr = 1.225, 9.81, 0.012
    order = np.argsort(t)
    t, v = t[order], v[order]
    # 剔除孤立跳变
    clean = np.ones(len(v), dtype=bool)
    for i in range(2, len(v) - 2):
        ref = (v[i-2] + v[i-1] + v[i+1] + v[i+2]) / 4
        if abs(v[i] - ref) > 12:
            clean[i] = False
    t, v = t[clean], v[clean]
    # 滑动回归加速度 ±0.5s
    a = np.full(len(v), np.nan)
    for i in range(len(v)):
        mw = (t >= t[i] - 0.5) & (t <= t[i] + 0.5)
        if np.sum(mw) < 3:
            continue
        a[i] = np.polyfit(t[mw], v[mw] / 3.6, 1)[0]
    v_ms = v / 3.6
    F_drag = 0.5 * rho * CdA * v_ms**2
    F_rr = crr * m * g0
    P_dec = np.full(len(v), np.nan)
    dec_mask = a < -0.05
    P_dec[dec_mask] = (m * (-a[dec_mask]) - F_drag[dec_mask] - F_rr) * v_ms[dec_mask] / 1000.0
    valid = ~np.isnan(P_dec) & (P_dec > 0)
    i_max = np.argmax(P_dec[valid])
    idx_max = np.where(valid)[0][i_max]
    print(f"\n[{name}] m={m}kg CdA={CdA}")
    print(f"  峰值减速功率: {P_dec[idx_max]:.0f} kW @ {t[idx_max]:.1f}s ({v[idx_max]:.0f}km/h, 减速度 {-a[idx_max]:.2f}m/s2 = {-a[idx_max]/g0:.2f}g)")
    # 前8
    top = np.argsort(P_dec[valid])[-8:][::-1]
    idxs = np.where(valid)[0][top]
    print("  减速功率前8点:")
    for i in idxs:
        print(f"    t={t[i]:6.1f}s  v={v[i]:4.0f}  a={a[i]:+.2f}  P_dec={P_dec[i]:5.0f}kW")
    # 速度分档峰值
    print("  速度分档峰值减速功率:")
    for lo, hi in [(80, 140), (140, 200), (200, 260), (260, 350)]:
        m_b = valid & (v >= lo) & (v < hi)
        if np.sum(m_b) > 0:
            i_b = np.argmax(P_dec[m_b])
            idx_b = np.where(m_b)[0][i_b]
            print(f"    {lo}-{hi}km/h: {P_dec[idx_b]:.0f}kW @ {v[idx_b]:.0f}km/h ({-a[idx_b]/g0:.2f}g)")
    return P_dec, t, v, a, valid

tu, vu = load(r'D:\Project\dsh_rally_cars\track\u9x_5fps.csv')
ts, vs = load(r'D:\Project\dsh_rally_cars\track\su7_5fps.csv')

print("=" * 64)
print("减速功率反推 (5fps 全圈)")
print("=" * 64)
P_u, t_u, v_u, a_u, val_u = decel_power(tu, vu, 2480 + 75, 0.67, "U9X")
P_s, t_s, v_s, a_s, val_s = decel_power(ts, vs, 2360 + 75, 0.47, "SU7")

# 回收功率对比: 前轴电机账面 vs 电池充电 C 率
print("\n" + "=" * 64)
print("回收/制动功率对比基准")
print("=" * 64)
print("  U9X 前轴电机账面: 2x555kW = 1110kW (反拖能力上限, 电机侧)")
print("  U9X 电池充电功率 (80kWh x C率):")
for c in [3, 4, 5, 6]:
    print(f"    {c}C = {80*c}kW")
print("  SU7 后轴双电机 2x425kW=850kW; 电池 93.7kWh x 4-5C = 375-470kW")
print("  (回收瓶颈通常不是电机而是电池充电功率)")
