"""
U9X 纽北圈速视频速度数据 -> 轮上功率反推
数据源: U9X clips.csv (用户手工记录, 每秒1帧, 速度km/h + G力)
模型: P_wheel = (m*a + F_drag + F_rr) * v
"""
import csv
import numpy as np

# ========== 读取数据 ==========
times = []   # 秒
speeds = []  # km/h
gs = []      # G力

with open(r'D:\Project\rally_cars\track\U9X clips.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if not row or not row[1] or not row[4]:
            continue
        try:
            mm = int(row[1]); ss = int(row[2]); ff = int(row[3])
            t = mm * 60 + ss + ff / 25.0
            # 丢弃最后一行异常点 (FF=15, 间隔0.32s不物理)
            if ff == 15:
                continue
            v = float(row[4])
            g = float(row[5]) if row[5] and row[5] != '-' else None
            times.append(t)
            speeds.append(v)
            gs.append(g)
        except (ValueError, IndexError):
            continue

times = np.array(times)
speeds = np.array(speeds)          # km/h
gs = np.array(gs, dtype=float)     # G力 (部分为nan)

# ========== 物理参数 ==========
m = 2480 + 75          # 车重 + 车手 (kg)
rho = 1.225            # 空气密度 (kg/m3) - 纽北海拔~300-600m
g0 = 9.81
crr = 0.012            # 滚动阻力系数 (性能轮胎)
v_ms = speeds / 3.6    # m/s

# ========== 加速度计算 (1秒间隔差分) ==========
dt = np.diff(times)
a = np.zeros_like(speeds)
a[1:] = np.diff(v_ms) / dt

# ========== CdA 反推: 用极速段 ==========
# 大直道尾段 348-349km/h 附近加速度≈0 -> P全部用于阻力
# 找速度 > 345 且 |a| < 0.05 的点
high_mask = (speeds > 344) & (np.abs(a) < 0.08)
if np.sum(high_mask) > 3:
    v_high = np.mean(v_ms[high_mask])
    # 此时: P = F_drag * v + F_rr * v, 若 P_known 未知则先用典型值估计
    # 方法1: 假设尾速段功率 = 前面加速段反推的功率, 迭代
    # 方法2: 用官方数据 349km/h 时接近电子限速
    print(f"高速段采样点: {np.sum(high_mask)}个, 平均速度 {v_high*3.6:.1f} km/h")

# 先用初始猜测 CdA=0.55 试算, 然后迭代修正
CdA = 0.55
F_drag = 0.5 * rho * CdA * v_ms**2
F_rr = crr * m * g0

# 功率初算
P = (m * a + F_drag + F_rr) * v_ms  # W
P_kw = P / 1000.0

# ========== 分段分析 ==========
def segment_analysis(name, t_start, t_end):
    mask = (times >= t_start) & (times <= t_end) & (P_kw > 0)
    if np.sum(mask) == 0:
        print(f"\n[{name}] 无有效数据")
        return
    seg_t = times[mask]
    seg_v = speeds[mask]
    seg_a = a[mask]
    seg_p = P_kw[mask]
    seg_g = gs[mask]
    
    v_min = np.min(seg_v); v_max = np.max(seg_v)
    p_max = np.max(seg_p)
    a_max = np.max(seg_a)
    a_max_g = np.nanmax(seg_g)
    
    # 最大加速度对应速度
    idx_amax = np.argmax(seg_a)
    
    print(f"\n[{name}] {t_start}s-{t_end}s, 采样{np.sum(mask)}点")
    print(f"  速度范围: {v_min:.0f} - {v_max:.0f} km/h")
    print(f"  最大轮上功率(估): {p_max:.0f} kW @ {seg_v[np.argmax(seg_p)]:.0f} km/h")
    print(f"  最大加速度: {a_max:.2f} m/s2 ({a_max/g0:.2f}g) @ {seg_v[idx_amax]:.0f} km/h")
    if not np.isnan(a_max_g):
        print(f"  PotPlayer G力峰值: {a_max_g:.2f} G")
    return p_max, a_max, v_min, v_max

print("=" * 60)
print("U9X 纽北轮上功率反推")
print(f"车重假设: {m}kg, CdA初值: {CdA}, Crr: {crr}")
print("=" * 60)

# 低速出弯段 (第一段 0:00-0:20)
segment_analysis("起步+第一段", 0, 20)
# 中速段 0:40-1:06 (直线加速 125->314)
segment_analysis("第一长直道", 40, 66)
# 第二段加速 1:47-1:53 (127->278)
segment_analysis("中段加速", 107, 115)
# 大直道 Döttinger Höhe 6:15-6:45
segment_analysis("Dottinger大直道", 375, 405)
# 全圈
mask_all = P_kw > 0
print(f"\n[全圈统计]")
print(f"  峰值轮上功率(估): {np.max(P_kw):.0f} kW")
print(f"  峰值速度: {np.max(speeds):.0f} km/h")
print(f"  峰值加速度: {np.max(a):.2f} m/s2 ({np.max(a)/g0:.2f}g)")
print(f"  PotPlayer G力峰值: {np.nanmax(gs):.2f} G")
print(f"  账面功率: 2220 kW")
print(f"  实测/账面比: {np.max(P_kw)/2220*100:.0f}%")

# ========== 功率-速度散点 (大直道) ==========
mask_straight = (times >= 375) & (times <= 405)
print(f"\n[大直道功率-速度曲线]")
for i in range(len(times)):
    if mask_straight[i] and P_kw[i] > 0:
        print(f"  {times[i]:.0f}s  {speeds[i]:.0f}km/h  a={a[i]:.2f}  P={P_kw[i]:.0f}kW")
# 保存完整数据到CSV
out_path = r'D:\Project\rally_cars\track\U9X_power_analysis.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['t_s', 'speed_kmh', 'accel_m_s2', 'power_kW'])
    for i in range(len(times)):
        writer.writerow([f"{times[i]:.2f}", f"{speeds[i]:.1f}", f"{a[i]:.3f}", f"{P_kw[i]:.1f}"])
print(f"\n完整数据已保存: {out_path}")
