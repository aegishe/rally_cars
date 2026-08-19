"""
5fps 全圈数据功率反推 (U9X + SU7)
数据: track/u9x_5fps.csv / track/su7_5fps.csv (全圈, lap 口径)
模型: P_wheel = (m*a + F_drag + F_rr) * v
平滑: 5点移动平均 (1s窗口) 抑制 0.2s 差分噪声
对比: 1s 采样口径峰值
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

def analyze(name, t, v, m, CdA, book_kw):
    rho, g0, crr = 1.225, 9.81, 0.012
    order = np.argsort(t)
    t, v = t[order], v[order]
    # 剔除孤立跳变 (相邻点 >18km/h 且与前后均值差 >12)
    clean = np.ones(len(v), dtype=bool)
    for i in range(2, len(v) - 2):
        ref = (v[i-2] + v[i-1] + v[i+1] + v[i+2]) / 4
        if abs(v[i] - ref) > 12:
            clean[i] = False
    t, v = t[clean], v[clean]
    # 滑动窗口线性回归 (±0.5s) 得加速度
    a = np.full(len(v), np.nan)
    for i in range(len(v)):
        m_win = (t >= t[i] - 0.5) & (t <= t[i] + 0.5)
        if np.sum(m_win) < 3:
            continue
        slope, _ = np.polyfit(t[m_win], v[m_win] / 3.6, 1)
        a[i] = slope
    # 功率 (仅有效点)
    valid = ~np.isnan(a)
    v_ms = v / 3.6
    F_drag = 0.5 * rho * CdA * v_ms**2
    F_rr = crr * m * g0
    P = np.full(len(v), np.nan)
    P[valid] = (m * a[valid] + F_drag[valid] + F_rr) * v_ms[valid] / 1000.0
    # 峰值 (加速段 P>0)
    mask_p = valid & (P > 0)
    i_max = np.argmax(P[mask_p])
    idx_max = np.where(mask_p)[0][i_max]
    print(f"\n[{name}] m={m}kg CdA={CdA}")
    print(f"  数据点 {len(t)}, 时间 {t[0]:.1f}-{t[-1]:.1f}s (剔除跳变后)")
    print(f"  峰值轮上功率: {P[idx_max]:.0f} kW @ {t[idx_max]:.1f}s ({v[idx_max]:.0f}km/h, a={a[idx_max]:.2f}m/s2)")
    print(f"  账面: {book_kw} kW -> 兑现率 {P[idx_max]/book_kw*100:.0f}%")
    top = np.argsort(P[mask_p])[-8:][::-1]
    idxs = np.where(mask_p)[0][top]
    print("  功率前8点:")
    for i in idxs:
        print(f"    t={t[i]:6.1f}s  v={v[i]:4.0f}  a={a[i]:+.2f}  P={P[i]:5.0f}kW")
    return P, t, v, a

tu, vu = load(r'D:\Project\dsh_rally_cars\track\u9x_5fps.csv')
ts, vs = load(r'D:\Project\dsh_rally_cars\track\su7_5fps.csv')

print("=" * 60)
print("5fps 功率反推")
print("=" * 60)
P_u, t_u2, v_u2, a_u2 = analyze("U9X", tu, vu, 2480 + 75, 0.67, 2220)
P_s, t_s2, v_s2, a_s2 = analyze("SU7", ts, vs, 2360 + 75, 0.47, 1138)

# 保存 5fps 功率 CSV (供图3)
import csv as _csv
for name, t_, v_, P_ in [('u9x', t_u2, v_u2, P_u), ('su7', t_s2, v_s2, P_s)]:
    out = fr'D:\Project\dsh_rally_cars\track\{name}_5fps_power.csv'
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = _csv.writer(f)
        w.writerow(['t_s', 'speed_kmh', 'power_kW'])
        for i in range(len(t_)):
            if not np.isnan(P_[i]):
                w.writerow([f"{t_[i]:.2f}", f"{v_[i]:.1f}", f"{P_[i]:.1f}"])
    print(f"saved {out}")
