"""
SU7 Ultra 纽北采样数据质量审计
检测: 1) 时间戳间隔异常 2) 孤立速度尖峰(OCR错读特征) 3) 不物理的加速度
输出可疑点清单, 供人工反查原视频截图
"""
import csv
import numpy as np

data_path = r'D:\Project\dsh_rally_cars\track\SU7 Ultra clips.csv'
rows = []
with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for i, row in enumerate(reader):
        if len(row) < 3 or not row[1] or not row[2]:
            continue
        t_str = row[1].strip()
        mm_part, ss_part = t_str.split(':')
        t = int(mm_part) * 60 + float(ss_part)
        rows.append({'lineno': i + 2, 'file': row[0], 't': t, 'v': float(row[2])})

n = len(rows)
times = np.array([r['t'] for r in rows])
speeds = np.array([r['v'] for r in rows])
dt = np.diff(times)
dv = np.diff(speeds)            # km/h per second
a_ms = dv / dt / 3.6            # m/s2

print("=" * 70)
print(f"共 {n} 点, 时间 {times[0]:.2f}s - {times[-1]:.2f}s")
print("=" * 70)

# ---- 1. 时间戳间隔异常 (正常应≈1.0s) ----
print("\n[1] 采样间隔异常 (|dt-1.0| > 0.15s):")
n_bad = 0
for i in range(n - 1):
    if abs(dt[i] - 1.0) > 0.15:
        print(f"  {rows[i]['file']}  t={times[i]:.2f}s -> {times[i+1]:.2f}s  dt={dt[i]:.2f}s")
        n_bad += 1
if n_bad == 0:
    print("  无")

# ---- 2. 不物理加速度 (1秒差分, 噪声基线±0.3m/s2) ----
print("\n[2] 加速度超物理范围 (a>+1.30g 或 a<-1.45g):")
n_bad = 0
for i in range(1, n):
    g = a_ms[i-1] / 9.81
    if g > 1.30 or g < -1.45:
        print(f"  {rows[i]['file']}")
        print(f"      t={times[i]:.2f}s  v: {speeds[i-1]:.0f} -> {speeds[i]:.0f} km/h  a={a_ms[i-1]:+.2f} m/s2 ({g:+.2f}g)")
        n_bad += 1
if n_bad == 0:
    print("  无")

# ---- 3. 孤立尖峰: v[i] 比前后都偏离≥12km/h 且方向相反 ----
print("\n[3] 孤立速度尖峰 (v[i] 与前后两点的差都≥12km/h 且方向相反):")
n_bad = 0
for i in range(1, n - 1):
    d_prev = speeds[i] - speeds[i-1]
    d_next = speeds[i+1] - speeds[i]
    if abs(d_prev) >= 12 and abs(d_next) >= 12 and d_prev * d_next < 0:
        print(f"  {rows[i]['file']}")
        print(f"      t={times[i]:.2f}s  v: {speeds[i-1]:.0f} -> [{speeds[i]:.0f}] -> {speeds[i+1]:.0f} km/h  (dv {d_prev:+.0f} / {d_next:+.0f})")
        n_bad += 1
if n_bad == 0:
    print("  无")

# ---- 4. 单秒大跳变 (低速段尤其可疑): |dv| >= 30 km/h ----
print("\n[4] 单秒速度跳变 >= 30km/h (0.85g, 加速段合理值上限):")
n_bad = 0
for i in range(1, n):
    d = speeds[i] - speeds[i-1]
    if abs(d) >= 30:
        tag = "加速" if d > 0 else "制动"
        print(f"  {rows[i]['file']}")
        print(f"      t={times[i]:.2f}s  v: {speeds[i-1]:.0f} -> {speeds[i]:.0f} km/h  ({tag} {d:+.0f} km/h/s = {d/3.6/dt[i-1]:+.2f} m/s2)")
        n_bad += 1
if n_bad == 0:
    print("  无")

# ---- 5. 速度平台可疑 (10秒内速度完全不变, 弯中不应出现) ----
print("\n[5] 连续3点以上速度完全相同的平台:")
n_bad = 0
i = 0
while i < n - 2:
    if speeds[i] == speeds[i+1] == speeds[i+2]:
        j = i + 3
        while j < n and speeds[j] == speeds[i]:
            j += 1
        print(f"  t={times[i]:.2f}s - {times[j-1]:.2f}s  v={speeds[i]:.0f} km/h 连续{j-i}点")
        n_bad += 1
        i = j
    else:
        i += 1
if n_bad == 0:
    print("  无")

print("\n" + "=" * 70)
print(f"审计完成: 类别2/3/4合计可疑 {sum(1 for _ in [0])} 条规则已执行")
