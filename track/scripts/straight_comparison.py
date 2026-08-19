"""
U9X vs SU7 Ultra: Döttinger 大直道时间差计算
直道段定义: 出弯加速点(≈181km/h) -> 刹车点(≈340km/h)
U9X:  375.28s - 397.28s (视频时间轴, 起点≈计时轴)
SU7:  378.72s - 402.72s
方法: 1) 段内距离积分验证同一赛道段 2) 用时差 3) 对齐后逐秒速度对比
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

# ---- 直道段 ----
u0, u1 = 376.28, 397.28    # U9X 181km/h -> 刹车点339
s0, s1 = 379.72, 402.72    # SU7 181km/h -> 刹车点341

mu = (t_u >= u0) & (t_u <= u1)
ms = (t_s >= s0) & (t_s <= s1)
tu, vu = t_u[mu], v_u[mu]
ts, vs = t_s[ms], v_s[ms]

# 距离积分 (梯形, km/h -> m)
def dist(t, v):
    d = 0.0
    for i in range(len(t)-1):
        d += (v[i] + v[i+1]) / 2 / 3.6 * (t[i+1] - t[i])
    return d

du = dist(tu, vu)
ds = dist(ts, vs)
print("=" * 60)
print("Döttinger 直道段对比")
print("=" * 60)
print(f"\nU9X 段: t={u0}-{u1}s  速度 {vu[0]:.0f} -> {vu[-1]:.0f} km/h  用时 {u1-u0:.1f}s  距离 {du:.0f}m")
print(f"SU7 段: t={s0}-{s1}s  速度 {vs[0]:.0f} -> {vs[-1]:.0f} km/h  用时 {s1-s0:.1f}s  距离 {ds:.0f}m")
print(f"\n距离差: {du-ds:+.0f}m ({(du-ds)/du*100:+.1f}%)  <- 验证同一赛道段")
print(f"直道段用时差: SU7 比 U9X 慢 {(s1-s0)-(u1-u0):.1f} 秒")

# ---- 极速点时间差 ----
i_umax = np.argmax(v_u)
i_smax = np.argmax(v_s)
print(f"\n极速点: U9X {v_u[i_umax]:.0f}km/h @ {t_u[i_umax]:.2f}s | SU7 {v_s[i_smax]:.0f}km/h @ {t_s[i_smax]:.2f}s")
print(f"极速点时间差(各轴): {t_s[i_smax]-t_u[i_umax]:.1f}s")

# ---- 直道入口对齐偏移 (限直道区间内搜索) ----
reg = (t_u >= 370) & (t_u <= 405)
reg_s = (t_s >= 370) & (t_s <= 405)
i_u181 = np.where(reg)[0][np.argmin(np.abs(v_u[reg] - 181))]
i_s181 = np.where(reg_s)[0][np.argmin(np.abs(v_s[reg_s] - 181))]
print(f"\n对齐锚点1 (≈181km/h出弯加速): U9X t={t_u[i_u181]:.2f}s({v_u[i_u181]:.0f})  SU7 t={t_s[i_s181]:.2f}s({v_s[i_s181]:.0f})  偏移 {t_s[i_s181]-t_u[i_u181]:.2f}s")

# 直道前重刹点 (a 最小处, 350-375s 区间)
a_u = np.diff(v_u) / np.diff(t_u) / 3.6
a_s = np.diff(v_s) / np.diff(t_s) / 3.6
m_u = (t_u[:-1] >= 350) & (t_u[:-1] <= 375)
m_s = (t_s[:-1] >= 350) & (t_s[:-1] <= 375)
i_u_br = np.where(m_u)[0][np.argmin(a_u[m_u])]
i_s_br = np.where(m_s)[0][np.argmin(a_s[m_s])]
print(f"对齐锚点2 (Galgenkopf前重刹): U9X t={t_u[i_u_br]:.2f}s  SU7 t={t_s[i_s_br]:.2f}s  偏移 {t_s[i_s_br]-t_u[i_u_br]:.2f}s")

OFFSET = t_s[i_s181] - t_u[i_u181]
print(f"\n对齐后对比 (SU7时间轴 = U9X时间轴 + {OFFSET:.2f}s):")
print(f"{'U9X时刻':>8} {'U9X速度':>8} {'SU7同位置':>10} {'速度差':>8}")
for i in range(len(tu)):
    tt = tu[i]
    if tt < 375.28 or tt > 397.28:
        continue
    # SU7 在 (tt+OFFSET) 处的速度 (线性插值)
    vs_at = np.interp(tt + OFFSET, t_s, v_s)
    print(f"{tt:8.2f}s {vu[i]:8.0f} {vs_at:10.0f} {vu[i]-vs_at:+8.0f}")

# ---- 加速段用时对比 (直道区间内: U9X 163->345, SU7 161->346) ----
reg_u = (t_u >= 370) & (t_u <= 400)
reg_s2 = (t_s >= 370) & (t_s <= 410)
i_u0 = np.where(reg_u)[0][np.argmin(np.abs(v_u[reg_u] - 163))]
i_u1x = np.where(reg_u)[0][np.argmin(np.abs(v_u[reg_u] - 345))]
i_s0x = np.where(reg_s2)[0][np.argmin(np.abs(v_s[reg_s2] - 161))]
i_s1x = np.where(reg_s2)[0][np.argmin(np.abs(v_s[reg_s2] - 346))]
tu_acc = t_u[i_u1x] - t_u[i_u0]
ts_acc = t_s[i_s1x] - t_s[i_s0x]
print(f"\n加速用时: U9X {v_u[i_u0]:.0f}->{v_u[i_u1x]:.0f}km/h 用 {tu_acc:.1f}s | SU7 {v_s[i_s0x]:.0f}->{v_s[i_s1x]:.0f}km/h 用 {ts_acc:.1f}s | SU7 慢 {ts_acc-tu_acc:.1f}s")
print(f"极速点: U9X {np.max(v_u[reg_u]):.0f}km/h 达到时刻 {t_u[np.argmax(v_u[reg_u])]:.2f}s | SU7 {np.max(v_s[reg_s2]):.0f}km/h @ {t_s[np.argmax(v_s[reg_s2])]:.2f}s")

# ---- 全圈时间账 ----
entry_gap = t_s[i_s181] - t_u[i_u181]          # 直道入口 U9X 领先
brk_gap = (s1 - u1)                             # 刹车点 U9X 领先
print("\n全圈时间账 (U9X领先秒数):")
print(f"  总圈速差: 7:04.9 - 6:59.2 = 5.7s")
print(f"  直道入口前 U9X 领先: {entry_gap:.2f}s")
print(f"  刹车点 U9X 领先: {brk_gap:.2f}s  -> 直道段贡献 {brk_gap-entry_gap:.2f}s")
print(f"  刹车点后到终点线贡献: {5.7-brk_gap:.2f}s")

# ============ 口径2: 直道前缘高峰/低谷锚点 (用户指出的 168/152 vs 160/150) ============
print("\n" + "=" * 60)
print("口径2: 直道前缘 高峰->低谷 锚点")
print("=" * 60)
# 在直道前缘小波浪内找高峰和低谷 (用户锚点: U9X 168峰/152谷, SU7 160峰/150谷)
seg_u = (t_u >= 370) & (t_u <= 375)
seg_s = (t_s >= 374) & (t_s <= 378)
i_u_peak = np.where(seg_u)[0][np.argmax(v_u[seg_u])]
i_s_peak = np.where(seg_s)[0][np.argmax(v_s[seg_s])]
i_u_val = np.where(seg_u)[0][np.argmin(v_u[seg_u])]
i_s_val = np.where(seg_s)[0][np.argmin(v_s[seg_s])]
print(f"高峰: U9X {v_u[i_u_peak]:.0f}km/h @ {t_u[i_u_peak]:.2f}s | SU7 {v_s[i_s_peak]:.0f}km/h @ {t_s[i_s_peak]:.2f}s | 偏移 {t_s[i_s_peak]-t_u[i_u_peak]:.2f}s")
print(f"低谷: U9X {v_u[i_u_val]:.0f}km/h @ {t_u[i_u_val]:.2f}s | SU7 {v_s[i_s_val]:.0f}km/h @ {t_s[i_s_val]:.2f}s | 偏移 {t_s[i_s_val]-t_u[i_u_val]:.2f}s")

# 从低谷到刹车点: 用时与距离
u_val_t, s_val_t = t_u[i_u_val], t_s[i_s_val]
mu2 = (t_u >= u_val_t) & (t_u <= u1)
ms2 = (t_s >= s_val_t) & (t_s <= s1)
tu2, vu2 = t_u[mu2], v_u[mu2]
ts2, vs2 = t_s[ms2], v_s[ms2]
du2, ds2 = dist(tu2, vu2), dist(ts2, vs2)
print(f"\n[低谷 -> 刹车点]")
print(f"  U9X: {u_val_t:.2f}s - {u1:.2f}s  速度 {vu2[0]:.0f}->{vu2[-1]:.0f}  用时 {u1-u_val_t:.1f}s  距离 {du2:.0f}m")
print(f"  SU7: {s_val_t:.2f}s - {s1:.2f}s  速度 {vs2[0]:.0f}->{vs2[-1]:.0f}  用时 {s1-s_val_t:.1f}s  距离 {ds2:.0f}m")
print(f"  距离差: {du2-ds2:+.0f}m ({(du2-ds2)/du2*100:+.1f}%)")
print(f"  直道净快(低谷口径): {(s1-s_val_t)-(u1-u_val_t):.1f}s")

# 从高峰到刹车点
mu3 = (t_u >= t_u[i_u_peak]) & (t_u <= u1)
ms3 = (t_s >= t_s[i_s_peak]) & (t_s <= s1)
tu3, vu3 = t_u[mu3], v_u[mu3]
ts3, vs3 = t_s[ms3], v_s[ms3]
du3, ds3 = dist(tu3, vu3), dist(ts3, vs3)
print(f"\n[高峰 -> 刹车点]")
print(f"  U9X: {t_u[i_u_peak]:.2f}s - {u1:.2f}s  速度 {vu3[0]:.0f}->{vu3[-1]:.0f}  用时 {u1-t_u[i_u_peak]:.1f}s  距离 {du3:.0f}m")
print(f"  SU7: {t_s[i_s_peak]:.2f}s - {s1:.2f}s  速度 {vs3[0]:.0f}->{vs3[-1]:.0f}  用时 {s1-t_s[i_s_peak]:.1f}s  距离 {ds3:.0f}m")
print(f"  距离差: {du3-ds3:+.0f}m ({(du3-ds3)/du3*100:+.1f}%)")
print(f"  直道净快(高峰口径, 含前缘波浪): {(s1-t_s[i_s_peak])-(u1-t_u[i_u_peak]):.1f}s")

# 波浪段本身: 高峰->低谷用时
print(f"\n[前缘波浪段 高峰->低谷]")
print(f"  U9X: {v_u[i_u_peak]:.0f}->{v_u[i_u_val]:.0f}km/h 用 {t_u[i_u_val]-t_u[i_u_peak]:.1f}s")
print(f"  SU7: {v_s[i_s_peak]:.0f}->{v_s[i_s_val]:.0f}km/h 用 {t_s[i_s_val]-t_s[i_s_peak]:.1f}s")

# 修正全圈时间账 (低谷口径)
print(f"\n全圈时间账修正 (低谷口径):")
print(f"  直道(低谷)前 U9X 领先: {t_s[i_s_val]-t_u[i_u_val]:.2f}s")
print(f"  直道贡献(低谷->刹车点): {(s1-s_val_t)-(u1-u_val_t):.1f}s")
print(f"  尾段贡献: {5.7-((t_s[i_s_val]-t_u[i_u_val])+(s1-s_val_t)-(u1-u_val_t)):.2f}s")
print(f"  合计: {(t_s[i_s_val]-t_u[i_u_val])+(s1-s_val_t)-(u1-u_val_t)+5.7-((t_s[i_s_val]-t_u[i_u_val])+(s1-s_val_t)-(u1-u_val_t)):.1f}s")
