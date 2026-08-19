"""
SU7 Ultra 纽北圈速视频速度数据 -> 轮上功率反推
数据源: track/SU7 Ultra clips.csv (用户手工记录, 每秒1点, 速度km/h)
模型: P_wheel = (m*a + F_drag + F_rr) * v
与 U9X 分析 (power_analysis.py) 同模型、同参数口径
"""
import csv
import numpy as np

# ========== 读取数据 ==========
data_path = r'D:\Project\dsh_rally_cars\track\SU7 Ultra clips.csv'
times = []   # 秒
speeds = []  # km/h

with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) < 3 or not row[1] or not row[2]:
            continue
        t_str = row[1].strip()
        try:
            if ':' in t_str:
                mm_part, ss_part = t_str.split(':')
                t = int(mm_part) * 60 + float(ss_part)
            else:
                t = float(t_str)
            v = float(row[2])
            times.append(t)
            speeds.append(v)
        except ValueError:
            continue

times = np.array(times)
speeds = np.array(speeds)          # km/h
print(f"数据点: {len(times)} 个, 时间范围 {times[0]:.1f}s - {times[-1]:.1f}s")

# ========== 物理参数 ==========
m = 2360 + 75          # SU7 Ultra 整备质量 + 车手 (kg)
rho = 1.225            # 空气密度 (kg/m3)
g0 = 9.81
crr = 0.012            # 滚动阻力系数 (性能轮胎, 与 U9X 分析同口径)
CdA = 0.47             # Cd=0.195 x 投影面积约2.42m2 (标准模式)
v_ms = speeds / 3.6    # m/s

# ========== 加速度计算 (差分, 与 U9X 同口径) ==========
a = np.zeros_like(speeds)
dt = np.diff(times)
a[1:] = np.diff(v_ms) / dt

F_drag = 0.5 * rho * CdA * v_ms**2
F_rr = crr * m * g0
P = (m * a + F_drag + F_rr) * v_ms  # W
P_kw = P / 1000.0

# 对功率序列做3点移动平均 (抑制单点差分噪声, 峰值口径)
kernel = np.ones(3) / 3.0
P_filt = np.convolve(P_kw, kernel, mode='same')

# ========== 每10秒速度轮廓 (分段辅助) ==========
print("\n[速度轮廓 每10s]")
for t0 in range(0, int(times[-1]) + 10, 10):
    m10 = (times >= t0) & (times < t0 + 10)
    if np.sum(m10) > 0:
        vmax = np.max(speeds[m10])
        print(f"  {t0:3d}-{t0+10:3d}s: vmax={vmax:3.0f} km/h" + ("  <--" if vmax > 280 else ""))

# ========== 全圈统计 ==========
print("=" * 60)
print(f"SU7 Ultra 纽北轮上功率反推 (m={m}kg, CdA={CdA}, Crr={crr})")
print("=" * 60)
pos_mask = P_kw > 0
print(f"\n[全圈统计] {len(times)} 点")
print(f"  峰值速度: {np.max(speeds):.0f} km/h @ {times[np.argmax(speeds)]:.1f}s")
print(f"  峰值轮上功率(原始差分): {np.max(P_kw):.0f} kW @ {times[np.argmax(P_kw)]:.1f}s ({speeds[np.argmax(P_kw)]:.0f} km/h)")
print(f"  峰值轮上功率(功率3点滤波): {np.max(P_filt):.0f} kW @ {times[np.argmax(P_filt)]:.1f}s ({speeds[np.argmax(P_filt)]:.0f} km/h)")
print(f"  峰值加速度: {np.max(a):.2f} m/s2 ({np.max(a)/g0:.2f}g) @ {times[np.argmax(a)]:.1f}s ({speeds[np.argmax(a)]:.0f} km/h)")
print(f"  最小加速度: {np.min(a):.2f} m/s2 ({np.min(a)/g0:.2f}g) (制动)")
print(f"  账面功率: 1138 kW (1548hp)")
print(f"  实测/账面比(原始): {np.max(P_kw)/1138*100:.0f}%   (滤波): {np.max(P_filt)/1138*100:.0f}%")

# ========== 分段统计 (对齐 U9X 四段口径) ==========
def seg(name, t0, t1):
    m = (times >= t0) & (times <= t1)
    if np.sum(m) == 0:
        print(f"  [{name}] 无数据")
        return
    i_p = np.argmax(P_kw[m])
    idx = np.where(m)[0]
    i_peak = idx[i_p]
    i_pf = np.argmax(P_filt[m])
    i_peakf = idx[i_pf]
    i_a = np.argmax(a[m])
    i_amax = idx[i_a]
    print(f"  [{name}] {t0}-{t1}s, {np.sum(m)}点")
    print(f"    峰值功率(原始): {np.max(P_kw[m]):.0f} kW @ {speeds[i_peak]:.0f} km/h (t={times[i_peak]:.1f}s)")
    print(f"    峰值功率(滤波): {np.max(P_filt[m]):.0f} kW @ {speeds[i_peakf]:.0f} km/h (t={times[i_peakf]:.1f}s)")
    print(f"    峰值加速度: {np.max(a[m]):.2f} m/s2 ({np.max(a[m])/g0:.2f}g) @ {speeds[i_amax]:.0f} km/h")

print("\n[分段统计]")
seg("起步暖胎", 0, 20)
seg("第一长直道", 40, 68)
seg("中段加速", 100, 115)
seg("Döttinger 大直道", 380, 410)

# ========== 高速段 (>280 km/h) 自动识别 ==========
print("\n[速度>280km/h 的采样段] (功率为滤波值)")
high = speeds > 280
in_seg = False
for i in range(len(times)):
    if high[i] and not in_seg:
        seg_start = i
        in_seg = True
    if not high[i] and in_seg:
        print(f"  {times[seg_start]:.0f}s - {times[i-1]:.0f}s: "
              f"峰值 {np.max(speeds[seg_start:i]):.0f} km/h, "
              f"段内峰值功率 {np.max(P_filt[seg_start:i]):.0f} kW")
        in_seg = False
if in_seg:
    i = len(times)
    print(f"  {times[seg_start]:.0f}s - {times[-1]:.0f}s: "
          f"峰值 {np.max(speeds[seg_start:]):.0f} km/h, "
          f"段内峰值功率 {np.max(P_filt[seg_start:]):.0f} kW")

# ========== 尾速段细看 (最后高速段, 检查限速特征) ==========
print("\n[尾段速度-加速度-功率逐点 (最后 60s 内 >300km/h 部分)]")
tail_mask = times > (times[-1] - 60)
for i in range(len(times)):
    if tail_mask[i] and speeds[i] > 300:
        print(f"  t={times[i]:6.1f}s  v={speeds[i]:5.0f}km/h  a={a[i]:+5.2f}m/s2  P={P_filt[i]:6.0f}kW")

# ========== 保存完整数据 ==========
out_path = r'D:\Project\dsh_rally_cars\track\SU7_power_analysis.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['t_s', 'speed_kmh', 'accel_m_s2', 'power_kW', 'power_filt_kW'])
    for i in range(len(times)):
        writer.writerow([f"{times[i]:.2f}", f"{speeds[i]:.1f}", f"{a[i]:.3f}", f"{P_kw[i]:.1f}", f"{P_filt[i]:.1f}"])
print(f"\n完整数据已保存: {out_path}")
