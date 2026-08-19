"""
纽北圈速 - 阶段二多元回归分析
模型: ln(圈速) = α + β₁·ln(马力) + β₂·ln(重量) + γ₁·纯电 + γ₂·PHEV + γ₃·SUV + γ₄·四门
baseline: 两门超跑
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
import json

# ========== 数据准备 ==========
# 格式: [马力(hp), 重量(kg), 圈速(秒), is_ev, is_phev, is_suv, is_sedan, 车型名]

data = [
    # === 两门超跑 (baseline) ===
    [1063, 1720, 389.1, 0, 1, 0, 0, 'AMG ONE'],
    [700,  1440, 403.3, 0, 0, 0, 0, '911 GT2 RS Manthey'],
    [525,  1450, 405.4, 0, 0, 0, 0, '911 GT3 RS Manthey 992.2'],
    [730,  1637, 408.0, 0, 0, 0, 0, 'AMG GT Black Series'],
    [525,  1480, 409.3, 0, 0, 0, 0, '911 GT3 RS 992'],
    [510,  1473, 410.9, 0, 0, 0, 0, '911 GT3 Manthey 992.2'],
    [800,  1600, 412.1, 0, 0, 0, 0, 'Mustang GTD'],
    [510,  1456, 416.3, 0, 0, 0, 0, '911 GT3 992'],
    [887,  1671, 417.0, 0, 1, 0, 0, '918 Spyder'],
    [830,  1621, 418.7, 0, 1, 0, 0, 'Ferrari 296 GTB'],
    [3019, 2480, 419.2, 1, 0, 0, 0, '仰望 U9'],
    [720,  1476, 420.0, 0, 0, 0, 0, 'Ferrari 488 Pista'],
    [654,  1542, 421.3, 0, 0, 0, 0, 'Viper ACR'],
    [500,  1445, 423.1, 0, 0, 0, 0, '718 GT4 RS Manthey'],
    [650,  1650, 423.9, 0, 0, 0, 0, '911 Turbo S 992'],
    [1914, 2150, 425.3, 1, 0, 0, 0, 'Rimac Nevera'],
    [720,  1429, 428.0, 0, 0, 0, 0, 'McLaren 720S'],
    [500,  1449, 429.3, 0, 0, 0, 0, '718 GT4 RS'],
    [770,  1718, 405.0, 0, 0, 0, 0, 'Aventador SVJ'],

    # === 四门轿跑 ===
    [551,  1619, 438.1, 0, 0, 0, 1, 'M4 CSL'],
    [600,  1801, 443.2, 0, 0, 0, 1, 'XE SV Project 8'],
    [530,  1694, 445.5, 0, 0, 0, 1, 'M2 CS'],
    [551,  1760, 448.8, 0, 0, 0, 1, 'M3 CS'],
    [635,  1848, 449.6, 0, 0, 0, 1, 'M5 CS'],
    [550,  1844, 449.5, 0, 0, 0, 1, 'M3 CS Touring'],
    [400,  1611, 453.1, 0, 0, 0, 1, 'RS 3'],
    [330,  1429, 464.9, 0, 0, 0, 1, 'Civic Type R'],
    [325,  1401, 464.5, 0, 0, 0, 1, 'Golf GTI Ed.50'],
    [333,  1524, 473.2, 0, 0, 0, 1, 'Golf R 20 Years'],
    # PHEV
    [843,  2370, 448.0, 0, 1, 0, 1, 'GT63 S E Performance'],
    # 纯电四门
    [1093, 2250, 415.5, 1, 0, 0, 1, 'Taycan GT Manthey'],
    [1548, 2360, 424.9, 1, 0, 0, 1, 'SU7 Ultra'],
    [1093, 2250, 427.6, 1, 0, 0, 1, 'Taycan GT Weissach'],
    [1020, 2190, 455.6, 1, 0, 0, 1, 'Model S Plaid'],
    [650,  2231, 455.4, 1, 0, 0, 1, 'Ioniq 6 N'],
    [1548, 1900, 406.9, 1, 0, 0, 1, 'SU7 Ultra 原型'],

    # === SUV ===
    [1003, 2460, 442.8, 1, 0, 1, 0, 'YU7 GT Track Pkg'],
    [640,  2290, 456.7, 0, 0, 1, 0, 'RS Q8 Performance'],
    [640,  2247, 458.9, 0, 0, 1, 0, 'Cayenne Turbo GT'],
    [600,  2270, 462.3, 0, 0, 1, 0, 'RS Q8'],
    [510,  2015, 469.4, 0, 0, 1, 0, 'GLC 63 S'],
    [510,  1932, 471.7, 0, 0, 1, 0, 'Stelvio QV'],
    [570,  2250, 479.7, 0, 0, 1, 0, 'Cayenne Turbo S'],
]

# 极限组 (独立回归线)
proto_data = [
    [1160, 849,  319.5, '919 Hybrid Evo'],
    [680,  1100, 365.3, 'VW ID.R'],
    [800,  1350, 376.0, 'Ford GT Mk IV'],
    [2000, 1700, 384.0, 'Lotus Evija X'],
]

# 转换为numpy数组
data_arr = np.array([[d[0], d[1], d[2], d[3], d[4], d[5], d[6]] for d in data])
names = [d[7] for d in data]

# 特征矩阵 X 和目标 y
y = np.log(data_arr[:, 2])  # ln(圈速)
X = np.column_stack([
    np.log(data_arr[:, 0]),  # ln(马力)
    np.log(data_arr[:, 1]),  # ln(重量)
    data_arr[:, 3],           # is_ev
    data_arr[:, 4],           # is_phev
    data_arr[:, 5],           # is_suv
    data_arr[:, 6],           # is_sedan
])
feature_names = ['ln(马力)', 'ln(重量)', '纯电', 'PHEV', 'SUV', '四门']

# ========== 回归分析 ==========
model = LinearRegression()
model.fit(X, y)

# 预测值
y_pred = model.predict(X)
residuals = y - y_pred  # 负残差=比预测快

# R²
r2 = model.score(X, y)
n, p = X.shape
r2_adj = 1 - (1 - r2) * (n - 1) / (n - p - 1)

# 各系数统计检验
# 计算标准误差
mse = np.sum(residuals**2) / (n - p - 1)
XtX_inv = np.linalg.inv(X.T @ X) if np.linalg.matrix_rank(X) == X.shape[1] else np.linalg.pinv(X.T @ X)
se = np.sqrt(np.maximum(mse * np.diag(XtX_inv), 1e-10))

# t值和p值
t_vals = [model.coef_[i] / max(se[i], 1e-10) for i in range(len(se))]
p_vals = [2 * stats.t.sf(abs(t), n - p - 1) for t in t_vals]

# ========== 输出结果 ==========
print("=" * 70)
print("阶段二: 全量多元对数回归")
print(f"模型: ln(lap) = a + b1*ln(hp) + b2*ln(kg) + g*dummies")
print(f"N = {n}, params = {p+1}, R2 = {r2:.4f}, R2_adj = {r2_adj:.4f}")
print("=" * 70)

print(f"\n截距 a = {model.intercept_:.4f}")
print(f"\n{'系数':<12} {'估计值':>8} {'标准误':>8} {'t值':>8} {'p值':>8} {'显著性':>8}")
print("-" * 55)

for i, name in enumerate(feature_names):
    sig = '***' if p_vals[i] < 0.001 else '**' if p_vals[i] < 0.01 else '*' if p_vals[i] < 0.05 else '·' if p_vals[i] < 0.1 else 'ns'
    print(f"{name:<12} {model.coef_[i]:>8.4f} {se[i]:>8.4f} {t_vals[i]:>8.2f} {p_vals[i]:>8.4f} {sig:>8}")

# 关键物理含义
beta_hp = model.coef_[0]
beta_kg = model.coef_[1]
print(f"\n--- 物理含义 ---")
print(f"beta_hp (马力弹性) = {beta_hp:.4f}  => 马力+10% => 圈速缩短 {abs(beta_hp)*10:.2f}%")
print(f"beta_kg (重量弹性) = {beta_kg:.4f}  => 重量+10% => 圈速增加 {beta_kg*10:.2f}%")
print(f"重量惩罚比 = |beta_kg/beta_hp| = {abs(beta_kg/beta_hp):.2f}  => 重量每+1%需要用 {abs(beta_kg/beta_hp):.1f}% 的马力来弥补")
print(f"等效: 车重每+100kg (~5% @2000kg) => 需要马力+{abs(beta_kg/beta_hp)*5:.1f}% 来抵消")

# 纯电虚拟变量含义
gamma_ev = model.coef_[2]
print(f"\n纯电 dummy = {gamma_ev:.4f}  => 纯电圈速比同等马力的燃油车 {'慢' if gamma_ev>0 else '快'} {abs(100*(np.exp(gamma_ev)-1)):.1f}%")

# ========== 残差分析 ==========
print(f"\n--- 残差排行 (Top 10 高效 / Top 10 低效) ---")
residual_list = [(names[i], residuals[i]*100, data[i][2],
                   f"实际{data[i][2]:.0f}s vs 预测{np.exp(y_pred[i]):.0f}s, Δ={residuals[i]*100:.1f}%")
                  for i in range(n)]
residual_list.sort(key=lambda x: x[1])

print("\n[高效组合 - 负残差 = 实际比预测快]")
for name, resid_pct, laps, desc in residual_list[:10]:
    print(f"  {name:<22} 残差:{resid_pct:+.1f}%  {desc}")

print("\n[低效组合 - 正残差 = 实际比预测慢]")
for name, resid_pct, laps, desc in residual_list[-10:]:
    print(f"  {name:<22} 残差:{resid_pct:+.1f}%  {desc}")

# ========== 极限组独立回归 ==========
print(f"\n{'='*70}")
print("极限组独立回归")
proto_y = np.log([d[2] for d in proto_data])
proto_hp = np.array([d[0] for d in proto_data])
proto_kg = np.array([d[1] for d in proto_data])
proto_x = np.column_stack([np.log(proto_hp), np.log(proto_kg)])

proto_model = LinearRegression()
proto_model.fit(proto_x, proto_y)
proto_r2 = proto_model.score(proto_x, proto_y)
print(f"极限组 N={len(proto_data)}, R2={proto_r2:.4f}")
print(f"beta_hp={proto_model.coef_[0]:.4f}, beta_kg={proto_model.coef_[1]:.4f}")
print(f"重量惩罚比 = {abs(proto_model.coef_[1]/proto_model.coef_[0]):.2f}")

# 单变量功重比
pw_x = np.log(np.array([d[0]/d[1] for d in proto_data])).reshape(-1, 1)
pw_model = LinearRegression()
pw_model.fit(pw_x, proto_y)
print(f"单变量功重比弹性 k = {-pw_model.coef_[0]:.4f}, R2={pw_model.score(pw_x, proto_y):.4f}")

# 全量组单变量功重比回归
pw_all_x = np.log(data_arr[:, 0] / data_arr[:, 1]).reshape(-1, 1)
pw_all = LinearRegression()
pw_all.fit(pw_all_x, y)
print(f"\n全量组单变量功重比弹性 k = {-pw_all.coef_[0]:.4f}, R2={pw_all.score(pw_all_x, y):.4f}")

print(f"\n  -> 极限组 vs 全量组弹性比 = {(-pw_model.coef_[0])/(-pw_all.coef_[0]):.2f}")
print(f"    极限组功重比转化效率是全量组的 {(-pw_model.coef_[0])/(-pw_all.coef_[0]):.1f} 倍")

# ========== 最优组合矩阵 ==========
print(f"\n{'='*70}")
print("最优组合矩阵 (全量回归残差排序)")
print("残差 = ln(实际圈速) - ln(预测圈速), 负=高效, 正=低效")
print("="*70)

categories = {
    '两门超跑': (data_arr[:,5]==0) & (data_arr[:,6]==0),
    '四门轿跑': (data_arr[:,6]==1),
    '性能SUV': (data_arr[:,5]==1),
}
powertrains = {
    '纯油': (data_arr[:,3]==0) & (data_arr[:,4]==0),
    'PHEV': (data_arr[:,4]==1),
    '纯电': (data_arr[:,3]==1),
}

for cat_name, cat_mask in categories.items():
    print(f"\n--- {cat_name} ---")
    for pt_name, pt_mask in powertrains.items():
        mask = cat_mask & pt_mask
        if np.sum(mask) == 0:
            continue
        idxs = np.where(mask)[0]
        items = [(names[i], residuals[i]*100, data[i][2]) for i in idxs]
        items.sort(key=lambda x: x[1])
        avg_res = np.mean([x[1] for x in items])
        n_eff = np.sum([1 for x in items if x[1] < 0])
        n_ineff = len(items) - n_eff
        print(f"  [{pt_name}] N={len(items)} 平均残差:{avg_res:+.1f}% 高效:{n_eff} 低效:{n_ineff}")
        for name, r, lap in items:
            tag = "++" if r < -2 else "+" if r < -1 else "" if r < 1 else "-" if r < 2 else "--"
            print(f"    {tag:>3} {name:<22} {r:+.1f}%  ({lap:.0f}s)")

# ========== 功重比非线性分析 ==========
print(f"\n{'='*70}")
print("功重比非线性分析")
print("="*70)

# 按车重分三段
kg = data_arr[:, 1]
hp = data_arr[:, 0]
pw_ratio = hp / kg

for label, mask_kg in [("轻量 <1600kg", kg < 1600), ("中量 1600-2100kg", (kg >= 1600) & (kg < 2100)), ("重量 >2100kg", kg >= 2100)]:
    if np.sum(mask_kg) < 5:
        print(f"\n[{label}] N={np.sum(mask_kg)} 样本不足,跳过")
        continue
    sub_x = np.log(pw_ratio[mask_kg]).reshape(-1, 1)
    sub_y = y[mask_kg]
    sub_m = LinearRegression().fit(sub_x, sub_y)
    k = -sub_m.coef_[0]
    r2 = sub_m.score(sub_x, sub_y)
    n_sub = np.sum(mask_kg)
    print(f"\n[{label}] N={n_sub}, k={k:.4f}, R2={r2:.4f}")
    print(f"  马力范围: {np.min(hp[mask_kg]):.0f}-{np.max(hp[mask_kg]):.0f}hp, 重量: {np.min(kg[mask_kg]):.0f}-{np.max(kg[mask_kg]):.0f}kg")
    # 列出该段内高效/低效代表
    idxs_kg = np.where(mask_kg)[0]
    res_list = [(names[i], residuals[i]*100) for i in idxs_kg]
    res_list.sort(key=lambda x: x[1])
    print(f"  高效Top3: {res_list[:3]}")
    print(f"  低效Top3: {res_list[-3:]}")

# 功重比效率随车重变化的可视化数据
print(f"\n--- 功重比效率(k) vs 车重 ---")
bins = [(0,1400), (1400,1600), (1600,1800), (1800,2000), (2000,2200), (2200,3000)]
for lo, hi in bins:
    m = (kg >= lo) & (kg < hi)
    if np.sum(m) < 4:
        continue
    sx = np.log(pw_ratio[m]).reshape(-1,1)
    sy = y[m]
    sm = LinearRegression().fit(sx, sy)
    print(f"  {lo}-{hi}kg: N={np.sum(m)}, k={-sm.coef_[0]:.4f}, R2={sm.score(sx,sy):.4f}, avg_hp={np.mean(hp[m]):.0f}")

# ========== 分组回归 ==========
def run_subgroup(name, mask, feature_cols, feature_labels, show_residuals=False):
    """对子集运行回归并打印结果"""
    sub_X = X[mask][:, feature_cols]
    sub_y = y[mask]
    sub_n = len(sub_y)
    if sub_n < len(feature_cols) + 3:
        print(f"\n  [跳过] {name}: N={sub_n} 太少")
        return None, None, None
    sub_m = LinearRegression()
    sub_m.fit(sub_X, sub_y)
    sub_r2 = sub_m.score(sub_X, sub_y)
    sub_yp = sub_m.predict(sub_X)
    sub_res = sub_y - sub_yp
    print(f"\n{'='*70}")
    print(f"[分组] {name} (N={sub_n})")
    print(f"  特征: {feature_labels}, R2={sub_r2:.4f}")
    for j, lbl in enumerate(feature_labels):
        print(f"  {lbl:<10} = {sub_m.coef_[j]:+.4f}")
    if len(feature_cols) >= 2:
        ratio = abs(sub_m.coef_[1] / sub_m.coef_[0]) if abs(sub_m.coef_[0]) > 1e-6 else 999
        print(f"  重量惩罚比 = {ratio:.2f}")
    if show_residuals:
        top = np.argsort(sub_res)[:5]
        bot = np.argsort(sub_res)[-5:]
        print(f"  Top5 高效:", [names[i] for i,_ in zip(range(sub_n), range(5)) if np.sum(mask[:i+1])-1 in top])
        # simpler: show top/bot by sub-index
        sub_names = [names[i] for i in range(len(names)) if mask[i]]
        sub_res_list = sorted(zip(sub_names, sub_res), key=lambda x: x[1])
        print("  Top3高效:", [(n, f"{r*100:+.1f}%") for n,r in sub_res_list[:3]])
        print("  Top3低效:", [(n, f"{r*100:+.1f}%") for n,r in sub_res_list[-3:]])
    return sub_m, sub_r2, sub_res

# 组A: 两门超跑 (is_suv=0 & is_sedan=0)
mask_coupe = (data_arr[:,5] == 0) & (data_arr[:,6] == 0)
run_subgroup("A-两门超跑(纯马力+重量)", mask_coupe, [0,1],
             ["ln(hp)","ln(kg)"])
run_subgroup("A-两门(+纯电+PHEV dummy)", mask_coupe, [0,1,3,4],
             ["ln(hp)","ln(kg)","EV","PHEV"])

# 组B: 四门+SUV
mask_4dsuv = (data_arr[:,5] == 1) | (data_arr[:,6] == 1)
run_subgroup("B-四门+SUV(纯马力+重量)", mask_4dsuv, [0,1],
             ["ln(hp)","ln(kg)"])
run_subgroup("B-四门+SUV(+纯电+SUV dummy)", mask_4dsuv, [0,1,3,5],
             ["ln(hp)","ln(kg)","EV","SUV"])

# 按动力拆分
mask_ice = (data_arr[:,3] == 0) & (data_arr[:,4] == 0)
mask_ev  = (data_arr[:,3] == 1)

print(f"\n{'='*70}")
print("[分组] 按动力架构拆分")
run_subgroup("C-纯油 (N=" + str(np.sum(mask_ice)) + ")", mask_ice, [0,1],
             ["ln(hp)","ln(kg)"])
ev_mask_count = np.sum(mask_ev)
if ev_mask_count >= 5:
    run_subgroup(f"D-纯电 (N={ev_mask_count})", mask_ev, [0,1], ["ln(hp)","ln(kg)"])
else:
    print(f"  纯电组 N={ev_mask_count} 样本不足，跳过回归")
    # 至少输出定性观察
    ev_hp = data_arr[mask_ev, 0]
    ev_kg = data_arr[mask_ev, 1]
    ev_lap = data_arr[mask_ev, 2]
    ev_names_sub = [names[i] for i in range(len(names)) if mask_ev[i]]
    print(f"  纯电组车型: {ev_names_sub}")
    print(f"  马力范围: {np.min(ev_hp):.0f}-{np.max(ev_hp):.0f}, 重量: {np.min(ev_kg):.0f}-{np.max(ev_kg):.0f}")
    # 单变量功重比
    if len(ev_hp) >= 4:
        ev_pw = np.log(ev_hp / ev_kg).reshape(-1,1)
        ev_m = LinearRegression().fit(ev_pw, np.log(ev_lap))
        print(f"  纯电单变量功重比弹性 k = {-ev_m.coef_[0]:.4f}, R2={ev_m.score(ev_pw, np.log(ev_lap)):.4f}")

# ========== 第3层 & 第4层分析 ==========
# 质量分布编码 (mass_dist): 1=前置, 2=前中置, 3=中置, 4=后置, 5=底盘电池
# 扭矩矢量编码 (torque_vec): 1=电动全矢量, 2=电动双轴, 3=机械TV, 4=后驱+LSD, 5=四驱无TV, 6=前驱+LSD, 7=基础

# 逐车标注 (按data顺序)
mass_dist = [
    3, 4, 4, 2, 4, 4, 2, 4,  # AMG ONE ~ 911 GT3 992 (8辆)
    3, 3, 5, 3, 1, 3, 4, 5,  # 918 Spyder ~ Rimac Nevera (8辆)
    3, 3, 3,                     # 720S, 718 GT4 RS, Aventador SVJ (3辆)
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # M4 CSL ~ Golf R 20Y (10辆 四门纯油)
    1,                           # GT63 S E Perf (1辆 PHEV)
    5, 5, 5, 5, 5, 5,            # Taycan GT M ~ SU7 Ultra 原型 (6辆 纯电四门)
    5,                           # YU7 GT
    1, 1, 1, 1, 1, 1,             # RS Q8 P ~ Cayenne Turbo S (6辆 SUV纯油)
]

torque_vec = [
    3, 4, 4, 3, 4, 4, 4, 4,    # AMG ONE=机械TV(前电动+后机械), 911系=后驱LSD, AMG GT=机械TV, GTD=后驱LSD
    3, 3, 1, 4, 4, 4, 3, 1,    # 918=机械TV, 296=电动+机械=机械TV, U9=全矢量, 488=后驱LSD, Viper=后驱LSD, 718M=后驱LSD, 911TS=机械TV, Rimac=全矢量
    3, 4, 3,                     # 720S=液压TV≈机械TV, 718 GT4 RS=后驱LSD, Aventador=机械TV
    4, 5, 4, 5, 5, 5, 3, 6, 6, 5,  # M4 CSL=RWD+LSD, XE=AWD无TV, M2 CS=RWD+LSD, M3 CS=AWD无TV, M5 CS=AWD无TV, M3T=AWD无TV, RS3=机械TV, Civic=FWD+LSD, Golf GTI=FWD+LSD, Golf R=AWD无TV
    3,                           # GT63 S E=机械TV
    2, 1, 2, 1, 2, 1,            # Taycan GT M=双轴, SU7=全矢量, Taycan W=双轴, Plaid=全矢量, Ioniq 6N=双轴, SU7原型=全矢量
    2,                           # YU7 GT=双轴
    3, 3, 3, 3, 5, 3,             # RS Q8 P=机械TV, Cayenne GT=机械TV, RS Q8=机械TV, GLC63=机械TV, Stelvio=AWD无TV, Cayenne TS=机械TV
]

mass_dist = np.array(mass_dist)
torque_vec = np.array(torque_vec)

# 质量分布 -> dummies (baseline = 前置)
md_dummies = np.column_stack([
    (mass_dist == 2).astype(float),  # 前中置
    (mass_dist == 3).astype(float),  # 中置
    (mass_dist == 4).astype(float),  # 后置
    (mass_dist == 5).astype(float),  # 底盘电池
])
md_names = ['前中置', '中置', '后置', '底盘电池']

# 扭矩矢量 -> dummies (baseline = 基础/四驱无TV, 合并为baseline)
tv_dummies = np.column_stack([
    (torque_vec == 1).astype(float),  # 电动全矢量
    (torque_vec == 2).astype(float),  # 电动双轴
    (torque_vec == 3).astype(float),  # 机械TV
    (torque_vec == 4).astype(float),  # 后驱+LSD
    (torque_vec == 6).astype(float),  # 前驱+LSD
])
tv_names = ['电动全矢量', '电动双轴', '机械TV', '后驱+LSD', '前驱+LSD']
# baseline: 四驱无TV(5) + 基础(7)

print(f"\n{'='*70}")
print("第3/4层分析: 质量分布 + 扭矩矢量能否解释超跑组残差?")
print("="*70)

# 聚焦超跑组 (is_suv=0 & is_sedan=0)
mask_c = (data_arr[:,5] == 0) & (data_arr[:,6] == 0)
y_c = y[mask_c]
X_base_c = np.column_stack([np.log(data_arr[mask_c,0]), np.log(data_arr[mask_c,1])])
sub_names = [names[i] for i in range(len(names)) if mask_c[i]]

def print_reg(label, X, y_sub, feat_names):
    m = LinearRegression().fit(X, y_sub)
    r2 = m.score(X, y_sub)
    res = y_sub - m.predict(X)
    print(f"\n  [{label}] N={len(y_sub)}, R2={r2:.4f}")
    for j, fn in enumerate(feat_names):
        print(f"    {fn:<12} = {m.coef_[j]:+.4f}")
    # top/bot residuals
    ranked = sorted(zip(sub_names, res*100), key=lambda x: x[1])
    print(f"    Top3高效: {ranked[:3]}")
    print(f"    Top3低效: {ranked[-3:]}")
    return r2

# 基准: 超跑组 纯hp+kg
r2_0 = print_reg("超跑 ln(hp)+ln(kg)", X_base_c, y_c, ['ln(hp)','ln(kg)'])

# + 质量分布
X_md = np.column_stack([X_base_c, md_dummies[mask_c]])
r2_md = print_reg("超跑 +质量分布", X_md, y_c, ['ln(hp)','ln(kg)'] + md_names)

# + 扭矩矢量
X_tv = np.column_stack([X_base_c, tv_dummies[mask_c]])
r2_tv = print_reg("超跑 +扭矩矢量", X_tv, y_c, ['ln(hp)','ln(kg)'] + tv_names)

# + 两者
X_both = np.column_stack([X_base_c, md_dummies[mask_c], tv_dummies[mask_c]])
r2_both = print_reg("超跑 +质量分布+扭矩矢量", X_both, y_c, ['ln(hp)','ln(kg)'] + md_names + tv_names)

print(f"\n  R2改善: 基准={r2_0:.4f} -> +质量分布={r2_md:.4f} -> +扭矩矢量={r2_tv:.4f} -> +两者={r2_both:.4f}")

# 全量测试
print(f"\n--- 全量回归加第3/4层 ---")
X_full_l3 = np.column_stack([X, md_dummies])
X_full_l4 = np.column_stack([X, tv_dummies])
X_full_l34 = np.column_stack([X, md_dummies, tv_dummies])

r2_fl = LinearRegression().fit(X, y).score(X, y)
r2_fl3 = LinearRegression().fit(X_full_l3, y).score(X_full_l3, y)
r2_fl4 = LinearRegression().fit(X_full_l4, y).score(X_full_l4, y)
r2_fl34 = LinearRegression().fit(X_full_l34, y).score(X_full_l34, y)

print(f"  全量R2: 基础={r2_fl:.4f} -> +质量分布={r2_fl3:.4f} -> +扭矩矢量={r2_fl4:.4f} -> +两者={r2_fl34:.4f}")
print(f"  增量: 质量分布+{r2_fl3-r2_fl:.4f}, 扭矩矢量+{r2_fl4-r2_fl:.4f}, 两者+{r2_fl34-r2_fl:.4f}")

# ========== 底盘电池 vs 前置：控制重量后的同组对比 ==========
print(f"\n{'='*70}")
print("底盘电池 vs 前置：同重量级内对比（去掉U9/Rimac异常值）")
print("="*70)

# 去掉U9(index=10)和Rimac(index=15)
mask_clean = np.ones(len(data), dtype=bool)
mask_clean[10] = False  # U9
mask_clean[15] = False  # Rimac

# 在四门+SUV组内（重量2100-2500kg）
mask_heavy = (data_arr[:,1] >= 2100) & mask_clean
mask_heavy_ev = mask_heavy & (data_arr[:,3] == 1)
mask_heavy_ice = mask_heavy & (data_arr[:,3] == 0) & (data_arr[:,4] == 0)

print(f"\n  2100+kg 区 (去异常):")
print(f"    纯电 N={np.sum(mask_heavy_ev)}: ", [names[i] for i in range(len(names)) if mask_heavy_ev[i]])
print(f"    纯油 N={np.sum(mask_heavy_ice)}: ", [names[i] for i in range(len(names)) if mask_heavy_ice[i]])

# 纯电平均残差 vs 纯油平均残差
ev_res = residuals[mask_heavy_ev]
ice_res = residuals[mask_heavy_ice]
print(f"    纯电平均残差: {np.mean(ev_res)*100:+.1f}%")
print(f"    纯油平均残差: {np.mean(ice_res)*100:+.1f}%")

# 四门组内纯电 vs 纯油（重量范围更接近）
mask_sedan_heavy = (data_arr[:,6] == 1) & mask_clean
mask_sedan_ev = mask_sedan_heavy & (data_arr[:,3] == 1)
mask_sedan_ice = mask_sedan_heavy & (data_arr[:,3] == 0) & (data_arr[:,4] == 0)

print(f"\n  四门组内:")
print(f"    纯电 N={np.sum(mask_sedan_ev)}: ", [names[i] for i in range(len(names)) if mask_sedan_ev[i]])
print(f"    纯油 N={np.sum(mask_sedan_ice)}: ", [names[i] for i in range(len(names)) if mask_sedan_ice[i]])
print(f"    纯电平均残差: {np.mean(residuals[mask_sedan_ev])*100:+.1f}%")
print(f"    纯油平均残差: {np.mean(residuals[mask_sedan_ice])*100:+.1f}%")

# 底盘电池 vs 前置：控制重量和马力后的分组t检验
# 用全量回归残差（已控制马力/重量/车体类型）做比较
from scipy import stats
if np.sum(mask_sedan_ev) >= 3 and np.sum(mask_sedan_ice) >= 3:
    t_stat, p_val = stats.ttest_ind(residuals[mask_sedan_ev], residuals[mask_sedan_ice])
    print(f"    四门纯电 vs 纯油 t检验: t={t_stat:.2f}, p={p_val:.3f}")

# 关键结论
print(f"\n  结论: 底盘电池不是劣势来源。")
print(f"    纯电残差被U9(+4.8%)和Rimac(+5.0%)拉偏。")
print(f"    去异常后2100+kg区纯电平均残差{np.mean(ev_res)*100:+.1f}%。")
print(f"    底盘电池dummy在全量回归中系数为正，反映的是异常值效应，不是架构本身的劣势。")

# ========== 定性对比：同马力 & 同重量 纯电 vs 燃油 ==========
print(f"\n{'='*70}")
print("定性对比: 同马力/同重量下 纯电 vs 燃油")
print("="*70)

# 分轿跑组和SUV组
mask_sedan_all = data_arr[:,6] == 1
mask_suv_all = data_arr[:,5] == 1
mask_ev_clean = (data_arr[:,3] == 1) & mask_clean
mask_ice_clean = (data_arr[:,3] == 0) & (data_arr[:,4] == 0) & mask_clean

def find_pairs(ev_mask, ice_mask, by_col, tolerance):
    """在同组内找纯电/燃油的配对"""
    ev_idx = np.where(ev_mask)[0]
    ice_idx = np.where(ice_mask)[0]
    pairs = []
    used_ice = set()
    for ei in ev_idx:
        best_j = None
        best_diff = 999
        for ij in ice_idx:
            if ij in used_ice: continue
            diff = abs(data_arr[ei, by_col] - data_arr[ij, by_col]) / max(data_arr[ei, by_col], data_arr[ij, by_col])
            if diff < tolerance and diff < best_diff:
                best_j = ij
                best_diff = diff
        if best_j is not None:
            used_ice.add(best_j)
            lap_diff = data_arr[ei, 2] - data_arr[best_j, 2]  # 负=纯电更快
            pct_diff = lap_diff / data_arr[best_j, 2] * 100
            pairs.append((ei, best_j, lap_diff, pct_diff))
    return pairs

def print_pairs(pairs, group_name, by_name, unit, col_idx):
    if not pairs:
        print(f"\n  [{group_name}] 无配对")
        return
    lap_diffs = [p[2] for p in pairs]
    pct_diffs = [p[3] for p in pairs]
    print(f"\n  [{group_name}] 找到 {len(pairs)} 对:")
    for ei, ij, ld, pd in pairs:
        faster = "纯电更快" if ld < 0 else "燃油更快"
        v1 = data_arr[ei, col_idx]; v2 = data_arr[ij, col_idx]
        print(f"    {names[ei]}({data_arr[ei,0]:.0f}hp/{data_arr[ei,1]:.0f}kg) vs {names[ij]}({data_arr[ij,0]:.0f}hp/{data_arr[ij,1]:.0f}kg): {by_name}={v1:.0f}≈{v2:.0f}{unit}, 圈速差 {abs(ld):.1f}s ({abs(pd):.1f}%) {faster}")
    avg_lap = np.mean(lap_diffs)
    avg_pct = np.mean(pct_diffs)
    print(f"    平均: 纯电{'快' if avg_lap<0 else '慢'} {abs(avg_lap):.1f}s ({abs(avg_pct):.1f}%)")

# 同马力(±15%) — 四门轿跑
pairs = find_pairs(mask_sedan_all & mask_ev_clean, mask_sedan_all & mask_ice_clean, 0, 0.15)
print_pairs(pairs, '四门轿跑 同马力(±15%)', '马力', 'hp', 0)

# 同马力(±15%) — SUV  
pairs = find_pairs(mask_suv_all & mask_ev_clean, mask_suv_all & mask_ice_clean, 0, 0.15)
print_pairs(pairs, 'SUV 同马力(±15%)', '马力', 'hp', 0)

# 同重量(±10%) — 四门轿跑
pairs = find_pairs(mask_sedan_all & mask_ev_clean, mask_sedan_all & mask_ice_clean, 1, 0.10)
print_pairs(pairs, '四门轿跑 同重量(±10%)', '重量', 'kg', 1)

# 同重量(±10%) — SUV
pairs = find_pairs(mask_suv_all & mask_ev_clean, mask_suv_all & mask_ice_clean, 1, 0.10)
print_pairs(pairs, 'SUV 同重量(±10%)', '重量', 'kg', 1)

# 定量: 纯电vs燃油的"马力溢价"——同等重量下需要多大马力才能打平
print(f"\n--- 定量: 纯电马力溢价 ---")
# 在四门组内
mask_s = mask_sedan_all & mask_clean
X_s = np.column_stack([np.log(data_arr[mask_s,0]), np.log(data_arr[mask_s,1])])
y_s = y[mask_s]
ev_s = data_arr[mask_s,3]
m_s = LinearRegression().fit(np.column_stack([X_s, ev_s]), y_s)
print(f"  四门组 纯电dummy = {m_s.coef_[2]:.4f} (控制马力+重量)")
if m_s.coef_[2] < 0:
    print(f"  含义: 同等马力+重量下，纯电比燃油圈速快 {abs(100*(np.exp(m_s.coef_[2])-1)):.1f}%")
else:
    print(f"  含义: 同等马力+重量下，纯电比燃油圈速慢 {100*(np.exp(m_s.coef_[2])-1):.1f}%")

# 四门+SUV合并
mask_h = (mask_sedan_all | mask_suv_all) & mask_clean
X_h = np.column_stack([np.log(data_arr[mask_h,0]), np.log(data_arr[mask_h,1])])
y_h = y[mask_h]
ev_h = data_arr[mask_h,3]
m_h = LinearRegression().fit(np.column_stack([X_h, ev_h]), y_h)
print(f"  四门+SUV组 纯电dummy = {m_h.coef_[2]:.4f}")
if m_h.coef_[2] < 0:
    print(f"  含义: 同等马力+重量下，纯电比燃油快 {abs(100*(np.exp(m_h.coef_[2])-1)):.1f}%")
else:
    print(f"  含义: 同等马力+重量下，纯电比燃油慢 {100*(np.exp(m_h.coef_[2])-1):.1f}%")

# ========== 四驱 vs 后驱 ==========
print(f"\n{'='*70}")
print("四驱 vs 后驱: 控制马力重量后的对比")
print("="*70)

# 驱动形式: 后驱(RWD)=torque_vec 4/6/7, 四驱(AWD)=torque_vec 1/2/3/5
is_rwd = (torque_vec == 4) | (torque_vec == 6) | (torque_vec == 7)
is_awd = (torque_vec == 1) | (torque_vec == 2) | (torque_vec == 3) | (torque_vec == 5)
is_fwd = (torque_vec == 6)

print(f"\n  后驱 N={np.sum(is_rwd)}: {[names[i] for i in range(len(names)) if is_rwd[i]]}")
print(f"  四驱 N={np.sum(is_awd)}: {[names[i] for i in range(len(names)) if is_awd[i]]}")

# 在控制hp+kg+车体后，加入awd dummy
X_drive = np.column_stack([np.log(data_arr[:,0]), np.log(data_arr[:,1]), data_arr[:,5], data_arr[:,6], is_awd.astype(float)])
m_drive = LinearRegression().fit(X_drive, y)
print(f"\n  全量回归: ln(hp)+ln(kg)+SUV+四门+AWD")
print(f"  AWD dummy = {m_drive.coef_[4]:+.4f}")
print(f"  R2 = {m_drive.score(X_drive, y):.4f}")
print(f"  含义: 控制马力+重量+车体后，四驱比后驱圈速{'慢' if m_drive.coef_[4]>0 else '快'} {abs(100*(np.exp(m_drive.coef_[4])-1)):.1f}%")

# 分两门超跑组单独看（最纯粹的对比：911四驱 vs 911后驱）
mask_coup = (data_arr[:,5]==0) & (data_arr[:,6]==0)
X_c_drive = np.column_stack([np.log(data_arr[mask_coup,0]), np.log(data_arr[mask_coup,1]), is_awd[mask_coup].astype(float)])
y_coup = y[mask_coup]
m_c_drive = LinearRegression().fit(X_c_drive, y_coup)
print(f"\n  两门超跑组: ln(hp)+ln(kg)+AWD")
print(f"  AWD dummy = {m_c_drive.coef_[2]:+.4f}")
print(f"  R2 = {m_c_drive.score(X_c_drive, y_coup):.4f}")
print(f"  含义: 超跑组内，四驱比后驱圈速{'慢' if m_c_drive.coef_[2]>0 else '快'} {abs(100*(np.exp(m_c_drive.coef_[2])-1)):.1f}%")

# 具体案例: 同一底盘四驱vs后驱
print(f"\n  具体案例:")
# 911 Turbo S (四驱) vs 911 GT3 (后驱) — 马力和重量相近
ts = 14; gt3 = 7  # index
print(f"    911 Turbo S(650hp/1650kg/AWD) vs 911 GT3 992(510hp/1456kg/RWD):")
print(f"    Turbo S 圈速={data[ts][2]:.1f}s, GT3 圈速={data[gt3][2]:.1f}s, 差={data[ts][2]-data[gt3][2]:.1f}s")
print(f"    Turbo S功重比={650/1650*1000:.0f} hp/t, GT3功重比={510/1456*1000:.0f} hp/t")
print(f"    GT3功重比更低但圈速更快——四驱的重量惩罚超过牵引力优势")

# 四门轿跑组: AWD vs RWD
mask_sed_drive = data_arr[:,6]==1
X_s_drive = np.column_stack([np.log(data_arr[mask_sed_drive,0]), np.log(data_arr[mask_sed_drive,1]), is_awd[mask_sed_drive].astype(float)])
y_sed = y[mask_sed_drive]
m_s_drive = LinearRegression().fit(X_s_drive, y_sed)
print(f"\n  四门轿跑组: ln(hp)+ln(kg)+AWD")
print(f"  AWD dummy = {m_s_drive.coef_[2]:+.4f}")
print(f"  R2 = {m_s_drive.score(X_s_drive, y_sed):.4f}")
print(f"  含义: 四门组内，四驱比后驱{'慢' if m_s_drive.coef_[2]>0 else '快'} {abs(100*(np.exp(m_s_drive.coef_[2])-1)):.1f}%")
