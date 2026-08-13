# -*- coding: utf-8 -*-
"""
派克峰圈速 - 多元对数回归分析
模型: ln(圈速) = alpha + beta1*ln(马力) + beta2*ln(重量) + dummies
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ========== 数据准备 ==========
# [马力hp, 重量kg, 圈速s, is_ev, is_phev, is_suv, is_sedan, is_aero_mod, is_aero_race, 车型名, 发动机类型]

data = [
    # 两门超跑 - 改装空力
    [700,  1390, 558.053, 0, 0, 0, 0, 1, 0, 'Porsche GT2 RS Clubsport', '涡轮'],
    [1250, 1884, 570.104, 0, 1, 0, 0, 1, 0, 'Corvette ZR1X', '涡轮+电机'],
    [573,  1725, 601.913, 0, 1, 0, 0, 1, 0, 'Acura NSX', '涡轮+电机'],
    # 两门超跑 - 原厂空力
    [650,  1650, 593.740, 0, 0, 0, 0, 0, 0, 'Porsche 911 Turbo S', '涡轮'],
    [1079, 1735, 611.018, 0, 0, 0, 0, 0, 0, 'Corvette ZR1 (Hartford)', '涡轮'],
    # 四门轿跑 - 改装空力
    [1020, 2200, 594.901, 1, 0, 0, 1, 1, 0, 'Tesla Model S Plaid改', '电动'],
    # 四门轿跑 - 原厂空力
    [625,  1965, 612.024, 0, 0, 0, 1, 0, 0, 'BMW M8', '涡轮'],
    [635,  2244, 618.488, 0, 0, 0, 1, 0, 0, 'Bentley Continental GT', '涡轮'],
    [450,  1850, 662.802, 1, 0, 0, 1, 0, 0, 'Tesla Model 3 Performance', '电动'],
    # SUV - 改装空力
    [641,  2100, 570.852, 1, 0, 1, 0, 1, 0, 'Hyundai Ioniq 5 N TA', '电动'],
    # SUV - 原厂空力
    [666,  2150, 632.064, 0, 0, 1, 0, 0, 0, 'Lamborghini Urus Perf', '涡轮'],
    [641,  2200, 649.267, 1, 0, 1, 0, 0, 0, 'Hyundai Ioniq 5 N', '电动'],
    [635,  2440, 649.902, 0, 0, 1, 0, 0, 0, 'Bentley Bentayga W12', '涡轮'],
]

# 皮卡参照（不参与回归 — 越野悬架+皮卡空力+重量螺旋，系统性偏差）
truck_ref = [
    [1025, 3250, 653.883, 1, 0, 'Rivian R1T Quad', '电动'],
]

proto_data = [
    [680,  1100, 477.148, 1, 0, 'VW I.D. R', '电动'],
    [875,  875,  493.878, 0, 0, 'Peugeot 208 T16', '涡轮'],
    [1400, 1500, 498.202, 1, 0, 'Ford Super Mustang Mach-E', '电动'],
    [1600, 1700, 533.563, 1, 0, 'Ford F-150 Lightning SuperTruck', '电动'],
]

data_arr = np.array([[d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8]] for d in data])
names = [d[9] for d in data]
engine_types = [d[10] for d in data]

y = np.log(data_arr[:, 2])
X = np.column_stack([
    np.log(data_arr[:, 0]),
    np.log(data_arr[:, 1]),
    data_arr[:, 3],
    data_arr[:, 4],
    data_arr[:, 5],
    data_arr[:, 6],
    data_arr[:, 7],
])
feature_names = ['ln(hp)', 'ln(kg)', 'EV', 'PHEV', 'SUV', 'Sedan', 'AeroMod']
n, p = X.shape

# ========== 回归 ==========
model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)
residuals = y - y_pred
r2 = model.score(X, y)
r2_adj = 1 - (1 - r2) * (n - 1) / (n - p - 1)

mse = np.sum(residuals**2) / (n - p - 1)
XtX_inv = np.linalg.inv(X.T @ X) if np.linalg.matrix_rank(X) == X.shape[1] else np.linalg.pinv(X.T @ X)
se = np.sqrt(np.maximum(mse * np.diag(XtX_inv), 1e-10))
t_vals = [model.coef_[i] / max(se[i], 1e-10) for i in range(len(se))]
p_vals = [2 * stats.t.sf(abs(t), n - p - 1) for t in t_vals]

print("=" * 70)
print("Pikes Peak - Multi-variable Log Regression")
print(f"Model: ln(lap) = a + b1*ln(hp) + b2*ln(kg) + dummies")
print(f"Track: 19.99km / 156 turns / 2862m->4302m / 7.2% avg grade")
print(f"N = {n}, params = {p+1}, R2 = {r2:.4f}, R2_adj = {r2_adj:.4f}")
print("=" * 70)

print(f"\nIntercept a = {model.intercept_:.4f}")
print(f"\n{'Coef':<12} {'Est':>8} {'SE':>8} {'t':>8} {'p':>8} {'Sig':>8}")
print("-" * 55)
for i, name in enumerate(feature_names):
    sig = '***' if p_vals[i] < 0.001 else '**' if p_vals[i] < 0.01 else '*' if p_vals[i] < 0.05 else '.' if p_vals[i] < 0.1 else 'ns'
    print(f"{name:<12} {model.coef_[i]:>8.4f} {se[i]:>8.4f} {t_vals[i]:>8.2f} {p_vals[i]:>8.4f} {sig:>8}")

beta_hp = model.coef_[0]
beta_kg = model.coef_[1]
print(f"\n{'='*55}")
print(f"Physics:")
print(f"  beta_hp = {beta_hp:.4f} -> hp +10% -> lap -{abs(beta_hp)*10:.2f}%")
print(f"  beta_kg = {beta_kg:.4f} -> kg +10% -> lap +{beta_kg*10:.2f}%")
if abs(beta_hp) > 1e-6:
    wpr = abs(beta_kg/beta_hp)
    print(f"  Weight Penalty Ratio = |beta_kg/beta_hp| = {wpr:.2f}")
    print(f"  -> Weight +1% needs hp +{wpr:.1f}% to compensate")
    print(f"  Compare NBR: full ~1.0, ICE ~1.6, Proto ~3.6")
else:
    wpr = None
    print(f"  WPR: hp coefficient near zero, cannot compute")

gamma_ev = model.coef_[2]
gamma_mod = model.coef_[6] if len(model.coef_) > 6 else 0
print(f"\n  EV dummy = {gamma_ev:.4f} -> EV {'slower' if gamma_ev>0 else 'faster'} {abs(100*(np.exp(gamma_ev)-1)):.1f}% (ctrl hp+kg+aero+body)")
print(f"  AeroMod dummy = {gamma_mod:.4f} -> mod aero {'slower' if gamma_mod>0 else 'faster'} {abs(100*(np.exp(gamma_mod)-1)):.1f}% (vs stock aero)")

# ========== 残差 ==========
print(f"\n{'='*70}")
print("Residuals (negative = faster than predicted)")
residual_list = [(names[i], residuals[i]*100, data[i][2], engine_types[i])
                 for i in range(n)]
residual_list.sort(key=lambda x: x[1])

print(f"\n{'Car':<30} {'Tag':<6} {'Resid':>8} {'Engine':>8}")
print("-" * 55)
for name, resid_pct, laps, eng in residual_list:
    tag = "FAST" if resid_pct < -1 else "EVEN" if resid_pct < 1 else "SLOW"
    print(f"{name:<30} {tag:<6} {resid_pct:+5.1f}%   {eng}")

# ========== 极限组 ==========
print(f"\n{'='*70}")
print("Proto Group (Unlimited / Race Aero)")
print("=" * 70)
proto_y = np.log([d[2] for d in proto_data])
proto_hp = np.array([d[0] for d in proto_data])
proto_kg = np.array([d[1] for d in proto_data])
proto_names = [d[5] for d in proto_data]
proto_x = np.column_stack([np.log(proto_hp), np.log(proto_kg)])
proto_model = LinearRegression().fit(proto_x, proto_y)
proto_r2 = proto_model.score(proto_x, proto_y)
print(f"Proto N={len(proto_data)}, R2={proto_r2:.4f}")
print(f"  beta_hp={proto_model.coef_[0]:.4f}, beta_kg={proto_model.coef_[1]:.4f}")
if abs(proto_model.coef_[0]) > 1e-6:
    print(f"  WPR = {abs(proto_model.coef_[1]/proto_model.coef_[0]):.2f}")
    print(f"  Compare NBR Proto WPR = 3.61")

pw_x = np.log(proto_hp / proto_kg).reshape(-1, 1)
pw_model = LinearRegression().fit(pw_x, proto_y)
print(f"  PW elasticity k = {-pw_model.coef_[0]:.4f}, R2={pw_model.score(pw_x, proto_y):.4f}")

# ========== 分组 ==========
print(f"\n{'='*70}")
print("Subgroup Analysis")
print("=" * 70)

for aero_label, aero_mask in [("Modified Aero", data_arr[:,7]==1), ("Stock Aero", data_arr[:,7]==0)]:
    if np.sum(aero_mask) < 3: continue
    sub_X = X[aero_mask][:, :2]
    sub_y = y[aero_mask]
    sub_m = LinearRegression().fit(sub_X, sub_y)
    sub_r2 = sub_m.score(sub_X, sub_y)
    sub_nms = [names[i] for i in range(len(names)) if aero_mask[i]]
    print(f"\n[{aero_label}] N={np.sum(aero_mask)}, R2={sub_r2:.4f}")
    print(f"  beta_hp={sub_m.coef_[0]:.4f}, beta_kg={sub_m.coef_[1]:.4f}")
    if abs(sub_m.coef_[0]) > 1e-6:
        print(f"  WPR = {abs(sub_m.coef_[1]/sub_m.coef_[0]):.2f}")
    print(f"  Cars: {sub_nms}")

for pt_label, pt_mask in [("ICE", (data_arr[:,3]==0)&(data_arr[:,4]==0)), ("EV", (data_arr[:,3]==1)), ("PHEV", (data_arr[:,4]==1))]:
    if np.sum(pt_mask) < 3:
        pt_nms = [names[i] for i in range(len(names)) if pt_mask[i]]
        if pt_nms: print(f"\n[{pt_label}] N={np.sum(pt_mask)} too few: {pt_nms}")
        continue
    sub_X = X[pt_mask][:, :2]
    sub_y = y[pt_mask]
    sub_m = LinearRegression().fit(sub_X, sub_y)
    sub_r2 = sub_m.score(sub_X, sub_y)
    sub_nms = [names[i] for i in range(len(names)) if pt_mask[i]]
    print(f"\n[{pt_label}] N={np.sum(pt_mask)}, R2={sub_r2:.4f}")
    print(f"  beta_hp={sub_m.coef_[0]:.4f}, beta_kg={sub_m.coef_[1]:.4f}")
    if abs(sub_m.coef_[0]) > 1e-6:
        print(f"  WPR = {abs(sub_m.coef_[1]/sub_m.coef_[0]):.2f}")

# ========== 功重比非线性 ==========
print(f"\n{'='*70}")
print("Power-to-Weight Nonlinearity")
print("=" * 70)
kg = data_arr[:, 1]
hp = data_arr[:, 0]
pw_ratio = hp / kg
for label, mask_kg in [("<1800kg", kg<1800), ("1800-2200kg", (kg>=1800)&(kg<2200)), (">2200kg", kg>=2200)]:
    if np.sum(mask_kg) < 4:
        print(f"\n[{label}] N={np.sum(mask_kg)} too few, skip")
        continue
    sub_x = np.log(pw_ratio[mask_kg]).reshape(-1,1)
    sub_y = y[mask_kg]
    sub_m = LinearRegression().fit(sub_x, sub_y)
    k = -sub_m.coef_[0]
    r2_sub = sub_m.score(sub_x, sub_y)
    sub_nms = [names[i] for i in range(len(names)) if mask_kg[i]]
    print(f"\n[{label}] N={np.sum(mask_kg)}, k={k:.4f}, R2={r2_sub:.4f}")
    print(f"  hp: {np.min(hp[mask_kg]):.0f}-{np.max(hp[mask_kg]):.0f}, kg: {np.min(kg[mask_kg]):.0f}-{np.max(kg[mask_kg]):.0f}")
    print(f"  Cars: {sub_nms}")

# ========== 高海拔 ==========
print(f"\n{'='*70}")
print("Altitude Effect (book hp vs actual performance)")
print("=" * 70)
print(f"\n{'Car':<30} {'PT':<8} {'Eng':<8} {'hp':>8} {'kg':>8} {'PW':>8} {'Lap(s)':>8} {'Altitude?'}")
print("-" * 85)
for i in range(n):
    pw = hp[i] / kg[i]
    eng = engine_types[i]
    if data_arr[i,3] == 1: pt = 'EV'; alt = 'immune'
    elif data_arr[i,4] == 1: pt = 'PHEV'; alt = 'motor helps'
    elif 'Turbo' in eng: pt = 'ICE'; alt = 'partial comp'
    else: pt = 'ICE'; alt = 'NA -35~40%'
    print(f"{names[i]:<30} {pt:<8} {eng:<8} {hp[i]:>8.0f} {kg[i]:>8.0f} {pw:>8.1f} {data[i][2]:>8.1f} {alt}")

# ========== EV vs ICE ==========
print(f"\n{'='*70}")
print("EV vs ICE Residuals")
print("=" * 70)
for label, mask in [("EV", data_arr[:,3]==1), ("ICE", (data_arr[:,3]==0)&(data_arr[:,4]==0)), ("PHEV", data_arr[:,4]==1)]:
    nms = [names[i] for i in range(len(names)) if mask[i]]
    res = residuals[mask]
    if len(nms) == 0: continue
    print(f"\n{label} N={len(nms)}: avg residual = {np.mean(res)*100:+.1f}%")
    for nm, r in zip(nms, res):
        print(f"  {nm:<30} {r*100:+.1f}%")

# ========== 单变量功重比 ==========
print(f"\n{'='*70}")
print("Single-var PW Regression")
print("=" * 70)
pw_all_x = np.log(data_arr[:, 0] / data_arr[:, 1]).reshape(-1, 1)
pw_all = LinearRegression().fit(pw_all_x, y)
k_all = -pw_all.coef_[0]
r2_all_pw = pw_all.score(pw_all_x, y)
print(f"All production: k = {k_all:.4f}, R2 = {r2_all_pw:.4f}")
print(f"  Compare NBR: full k~0.15, >2200kg k~0.08")
print(f"  Pikes Peak k {'>' if k_all>0.15 else '<'} NBR: {k_all:.4f} vs ~0.15")

# ========== 跨场景 ==========
print(f"\n{'='*70}")
print("Cross-scene: Pikes Peak vs NBR")
print("=" * 70)
print(f"\n{'Metric':<30} {'Pikes Peak':>12} {'NBR':>12}")
print("-" * 56)
print(f"{'Length':<30} {'19.99km':>12} {'20.83km':>12}")
print(f"{'Turns':<30} {'156':>12} {'~170':>12}")
print(f"{'Elevation':<30} {'2862->4302m':>12} {'~300m':>12}")
print(f"{'N (production)':<30} {n:>12} {'42':>12}")
print(f"{'R2 (full)':<30} {r2:>12.4f} {'0.774->0.907':>12}")
print(f"{'PW elasticity k':<30} {k_all:>12.4f} {'0.15':>12}")
print(f"{'Weight Penalty':<30} {wpr if wpr else 'N/A':>12} {'1.0~3.6':>12}")

# ========== 输出JSON ==========
# 改装级别定义
mod_map = {
    'Porsche 911 Turbo S':       ('原厂', '仅安全改装(防滚架+座椅+灭火)'),
    'BMW M8':                    ('原厂', '仅安全改装'),
    'Bentley Continental GT':    ('原厂', '仅安全改装'),
    'Lamborghini Urus Perf':     ('原厂', '仅安全改装'),
    'Bentley Bentayga W12':      ('原厂', '仅安全改装'),
    'Tesla Model 3 Performance': ('原厂', '仅安全改装'),
    'Hyundai Ioniq 5 N':         ('原厂', '仅安全改装, 现代官方参赛'),
    'Corvette ZR1 (Hartford)':   ('原厂', '几乎原厂规格+原厂性能包, 私人车手'),
    'Hyundai Ioniq 5 N TA':      ('厂商改装', '现代N + WRC冠军Dani Sordo驾驶, ECU+空力+悬架+slick胎'),
    'Porsche GT2 RS Clubsport':  ('厂商改装', '保时捷Motorsport赛车部门出品, 大尾翼+全底盘'),
    'Corvette ZR1X':             ('厂商改装', '雪佛兰官方, 原厂性能包配套, 1250hp混动, 职业车手'),
    'Tesla Model S Plaid改':      ('私人改装', 'Unplugged Performance私人改装, 改装质量存疑'),
    'Acura NSX':                 ('私人改装', '私人车队参赛, 2020年混动组记录'),
}

results = {
    "track": {"name": "Pikes Peak", "length_km": 19.99, "turns": 156, "elev_start": 2862, "elev_end": 4302, "elev_gain": 1440, "avg_grade_pct": 7.2},
    "regression": {
        "n": n, "p": p+1, "r2": float(r2), "r2_adj": float(r2_adj),
        "intercept": float(model.intercept_),
        "coeffs": [{"name": feature_names[i], "value": float(model.coef_[i]), "se": float(se[i]), "p": float(p_vals[i])} for i in range(p)],
        "beta_hp": float(beta_hp), "beta_kg": float(beta_kg),
        "weight_penalty_ratio": float(wpr) if wpr else None,
        "pw_elasticity_k": float(k_all),
    },
    "cars": [
        {
            "name": names[i], "hp": int(data[i][0]), "weight": int(data[i][1]), "lap_s": float(data[i][2]),
            "powertrain": "EV" if data[i][3] else "PHEV" if data[i][4] else "ICE",
            "body": "Proto" if data[i][8] else ("Truck" if "Rivian" in data[i][9] else ("SUV" if data[i][5] else "Sedan" if data[i][6] else "Coupe")),
            "aero": "Race" if data[i][8] else "Modified" if data[i][7] else "Stock",
            "engine": data[i][10],
            "residual_pct": float(residuals[i] * 100),
            "predicted_lap_s": float(np.exp(y_pred[i])),
            "pw_ratio": float(data[i][0] / data[i][1]),
            "mod_level": mod_map.get(data[i][9], ('未知', ''))[0],
            "mod_detail": mod_map.get(data[i][9], ('未知', ''))[1],
        }
        for i in range(n)
    ],
    "protos": [
        {"name": proto_data[i][5], "hp": int(proto_data[i][0]), "weight": int(proto_data[i][1]),
         "lap_s": float(proto_data[i][2]), "powertrain": "EV" if proto_data[i][3] else "ICE",
         "pw_ratio": float(proto_data[i][0]/proto_data[i][1])}
        for i in range(len(proto_data))
    ],
    "truck_ref": [
        {"name": truck_ref[i][4], "hp": int(truck_ref[i][0]), "weight": int(truck_ref[i][1]),
         "lap_s": float(truck_ref[i][2]), "powertrain": "EV" if truck_ref[i][3] else "ICE",
         "pw_ratio": float(truck_ref[i][0]/truck_ref[i][1]), "note": "越野皮卡，不参与量产回归"}
        for i in range(len(truck_ref))
    ],
    "proto_regression": {
        "n": len(proto_data), "r2": float(proto_r2),
        "beta_hp": float(proto_model.coef_[0]), "beta_kg": float(proto_model.coef_[1]),
        "weight_penalty_ratio": float(abs(proto_model.coef_[1]/proto_model.coef_[0])) if abs(proto_model.coef_[0])>1e-6 else None,
        "pw_elasticity_k": float(-pw_model.coef_[0]),
    },
    "comparison_nbr": {
        "track": "NBR", "length_km": 20.83, "n": 42,
        "r2_adj": 0.735, "r2_full": 0.907,
        "pw_elasticity_k": 0.15, "weight_penalty_ratio": 1.0,
        "pw_elasticity_heavy": 0.08,
    }
}

with open('pikes-peak/charts/regression_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nResults exported to pikes-peak/charts/regression_results.json")
