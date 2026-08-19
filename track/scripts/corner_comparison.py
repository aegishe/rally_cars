"""
U9X vs SU7 Ultra: 全圈弯道对比
方法: 速度积分 -> 累计赛道距离 s(t) (两车共用同一赛道坐标系)
     在距离域找弯心(局部速度最低点), 逐弯对比弯心速度
     并计算时间差剖面 dt(s) = t_su7(s) - t_u9x(s)
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
        s[i] = s[i-1] + (vv[i-1] + vv[i]) / 2 / 3.6 * (tt[i] - tt[i-1])
    return tt, s, vv

# U9X: 视频0s=过线(104km/h滚动起跑), 圈速6:59.2=419.2s, 尾部4.3s缓冲
# SU7: 视频时间轴=计时轴, 过线帧 424.9s
tu, su, vu = cumdist(t_u, v_u, 0.0, 419.2)
ts, ss, vs = cumdist(t_s, v_s, 0.72, 424.9)
print(f"U9X 圈速段距离: {su[-1]:.0f} m  ({su[-1]/20832*100:.1f}% 官方长度)")
print(f"SU7 圈速段距离: {ss[-1]:.0f} m  ({ss[-1]/20832*100:.1f}% 官方长度)")

# 公共距离网格
s_end = min(su[-1], ss[-1])
s_grid = np.arange(0, s_end, 10.0)
v_u_g = np.interp(s_grid, su, vu)
v_s_g = np.interp(s_grid, ss, vs)
t_u_g = np.interp(s_grid, su, tu)
t_s_g = np.interp(s_grid, ss, ts)
dt_g = t_s_g - t_u_g      # SU7 比 U9X 慢多少秒 (正=U9X领先)
dt_g = dt_g - dt_g[0]     # 起点归零 (修正 U9X 视频0s在过线前~0.6s的偏移)

# ---- 弯心检测 (距离域局部最小, 合并200m内) ----
def find_valleys(v, s):
    idx = []
    for i in range(2, len(v)-2):
        if v[i] <= v[i-1] and v[i] <= v[i-2] and v[i] <= v[i+1] and v[i] <= v[i+2] and v[i] < 300:
            if idx and s[i] - s[idx[-1]] < 200:
                if v[i] < v[idx[-1]]:
                    idx[-1] = i
            else:
                idx.append(i)
    return idx

iv_u = find_valleys(v_u_g, s_grid)
iv_s = find_valleys(v_s_g, s_grid)
print(f"\n弯心数: U9X {len(iv_u)} 个, SU7 {len(iv_s)} 个")

# ---- 弯心配对 (距离差<80m) ----
pairs = []
used_s = set()
for iu in iv_u:
    best = None
    for is_ in iv_s:
        if abs(s_grid[iu] - s_grid[is_]) < 80:
            if best is None or abs(s_grid[iu] - s_grid[is_]) < abs(s_grid[iu] - s_grid[best]):
                best = is_
    if best is not None:
        pairs.append((iu, best))
        used_s.add(best)

print(f"配对弯道: {len(pairs)} 个")
unpaired_s = [i for i in iv_s if i not in used_s]
print(f"SU7 未配对弯心: {len(unpaired_s)} 个 (距离 {[f'{s_grid[i]:.0f}m' for i in unpaired_s]})")

# ---- 逐弯对比表 ----
print(f"\n{'距离':>7} | {'U9X弯心':>8} | {'SU7弯心':>8} | {'差(SU7-U9X)':>11} | 档位")
results = []
for iu, is_ in pairs:
    s_c = s_grid[iu]
    vu_c = v_u_g[iu]
    vs_c = v_s_g[is_]
    d = vs_c - vu_c
    if vu_c < 100:
        band = "低速(<100)"
    elif vu_c < 150:
        band = "中速(100-150)"
    elif vu_c < 200:
        band = "高速(150-200)"
    else:
        band = "极高速(>200)"
    results.append((s_c, vu_c, vs_c, d, band))
    print(f"{s_c:7.0f} | {vu_c:8.0f} | {vs_c:8.0f} | {d:+11.0f} | {band}")

# ---- 分档统计 ----
print("\n" + "=" * 50)
print("分档统计 (正差=SU7 弯心更快):")
bands = ["低速(<100)", "中速(100-150)", "高速(150-200)", "极高速(>200)"]
for b in bands:
    rs = [r for r in results if r[4] == b]
    if rs:
        dmean = np.mean([r[3] for r in rs])
        n_su7 = sum(1 for r in rs if r[3] > 2)   # SU7快(>2km/h)
        n_u9 = sum(1 for r in rs if r[3] < -2)   # U9X快(<-2km/h)
        n_eq = len(rs) - n_su7 - n_u9
        print(f"  {b:14s}: {len(rs):2d}弯  平均差 {dmean:+6.1f} km/h  SU7优 {n_su7} / 平 {n_eq} / U9X优 {n_u9}")

# ---- 时间差剖面: 哪些弯道段 U9X 在赚/还时间 ----
# 弯道段 = 弯心±150m; 段内 dt 变化
print("\n" + "=" * 50)
print("弯道段时间变化 dt(段末)-dt(段始) (负=U9X在弯中扩大领先):")
corner_dt = []
for iu, is_ in pairs:
    s_c = s_grid[iu]
    i0 = max(0, int((s_c - 150) / 10))
    i1 = min(len(s_grid)-1, int((s_c + 150) / 10))
    d_dt = dt_g[i1] - dt_g[i0]
    vu_c = v_u_g[iu]
    band = "低速" if vu_c < 100 else ("中速" if vu_c < 150 else ("高速" if vu_c < 200 else "极高速"))
    corner_dt.append((band, d_dt))
    print(f"  {s_c:6.0f}m  {band:3s}弯: 弯前dt={dt_g[i0]:.2f}s -> 弯后dt={dt_g[i1]:.2f}s  变化 {d_dt:+.2f}s")

print("\n按档汇总弯道段净时间变化 (正=U9X在该档弯段净赚):")
for b in ["低速", "中速", "高速", "极高速"]:
    ds = [d for band, d in corner_dt if band == b]
    if ds:
        print(f"  {b}弯: {len(ds)}个, 平均 {np.mean(ds):+.2f}s/弯, 合计 {np.sum(ds):+.2f}s")

# ---- 直道段检测: 弯间 dt 总变化 ----
print("\n" + "=" * 50)
print("弯间直道段时间变化 (正=U9X在直道扩大领先):")
for k in range(len(pairs)-1):
    s_a = s_grid[pairs[k][0]]
    s_b = s_grid[pairs[k+1][0]]
    i0 = int(s_a/10); i1 = int(s_b/10)
    d_dt = dt_g[i1] - dt_g[i0]
    vmax_u = np.max(v_u_g[i0:i1+1])
    if d_dt > 0.3 or d_dt < -0.3:
        tag = "直道/加速段" if vmax_u > 240 else "短衔接段"
        print(f"  {s_a:6.0f}m -> {s_b:6.0f}m  ({tag}, vmax_U9X={vmax_u:.0f}): dt {dt_g[i0]:.2f} -> {dt_g[i1]:.2f}  +{d_dt:.2f}s")

# 保存对齐后曲线
out = r'D:\Project\dsh_rally_cars\track\corner_comparison.csv'
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['s_m', 'v_u9x', 'v_su7', 't_u9x', 't_su7', 'dt_s'])
    for i in range(len(s_grid)):
        w.writerow([f"{s_grid[i]:.0f}", f"{v_u_g[i]:.1f}", f"{v_s_g[i]:.1f}", f"{t_u_g[i]:.2f}", f"{t_s_g[i]:.2f}", f"{dt_g[i]:.2f}"])
print(f"\n对齐曲线已保存: {out}")
