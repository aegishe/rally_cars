# -*- coding: utf-8 -*-
"""
成绩反推平均轮端功率（环塔 2026 / 达喀尔 2026）

模型（沿用项目 2026-08 SS9 软沙反推口径）：
    P = ( m·g·cr + 0.5·ρ·Cd·A·v² ) · v
其中：
    v   = 特殊赛段里程 ÷ 单段净计时（来自官方成绩 CSV）
    cr  = 地形等效滚动阻力系数（本脚本按赛段地形赋值，见 TERRAIN_CR）
    CdA = 迎风面积×风阻系数（越野赛车粗估 1.5）
    m   = 整车质量（含车手/油料，粗估）

标定锚点（项目已有结论）：
    3 吨级电驱车在环塔 SS9 纯沙漠 平均 45 km/h → 轮上约 100 kW
    → 反标定 软沙 cr ≈ 0.276（见 calibrate()）

用法：
    python offroad/scripts/power_est.py            # 打印标定 + 环塔 + 达喀尔表
    python offroad/scripts/power_est.py --sensitivity   # 追加 cr 敏感性

口径纪律（引用前必读）：
  1. 绝对 kW 误差 ±30~50%（cr 为地形粗估、CdA 为估值、速度为段平均）——只用于量级与相对关系；
  2. 段平均速度抹掉了沙丘冲刺瞬态峰值（爬沙丘瞬时可能 200-300 kW）；
  3. 跨地形类型的对比（沙地 ≫ 戈壁）可靠；同一地形内的段间差部分由 cr 赋值决定；
  4. 里程来源见 docs/成绩反推平均功率与散热死区-环塔达喀尔推演.md §二。
"""
import sys, io, csv, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

G = 9.81
RHO = 1.225
CDA = 1.5

# ---- 里程（特殊赛段 km）与地形 cr ----
# 环塔：SS1 245.8(新华网) SS2 293.08 SS3 468.95 SS4 91.03 SS5 281.32 SS7 285.87(新华网)
#       SS8 288.10 SS9 353.66 SS10 214.35 SS11 21.88(捷途官方) SS12 334 SS13 159.32；SS6 待补
HT_DIST = {1: 245.8, 2: 293.08, 3: 468.95, 4: 91.03, 5: 281.32, 7: 285.87,
           8: 288.10, 9: 353.66, 10: 214.35, 11: 21.88}
HT_TERRAIN = {1: '戈壁/砂石', 2: '混合(沙+戈壁)', 3: '戈壁长耐力', 4: '戈壁峡谷',
              5: '魔鬼(沙+戈壁)', 7: '沙海老兵', 8: '克里雅河沙漠', 9: '纯沙漠', 10: 'N39纯沙漠', 11: '短冲刺'}
TERRAIN_CR = {'戈壁/砂石': 0.040, '混合(沙+戈壁)': 0.100, '戈壁长耐力': 0.035, '戈壁峡谷': 0.050,
              '魔鬼(沙+戈壁)': 0.150, '沙海老兵': 0.120, '克里雅河沙漠': 0.180,
              '纯沙漠': 0.276, 'N39纯沙漠': 0.240, '短冲刺': 0.060}
# 达喀尔：Special 里程（racetrackmasters，SS7=462km 与视频口播一致；玛拉松段 SS4/5/9/10）
DK_DIST = {1: 305, 2: 400, 3: 422, 4: 451, 5: 356, 6: 331, 7: 462,
           8: 481, 9: 418, 10: 371, 11: 347, 12: 310, 13: 105}

# ---- 车辆质量（kg，粗估口径）----
M_LU_T1P = 2000    # 鹿丙龙 JJ-Sport JJ3 (T1+ 原型，待官方口径)
M_HANWEI = 2000    # 韩魏 HWM T1+ (T1+ 原型，待官方口径)
M_TANK700 = 3000   # 坦克700 Hi4-T 环塔赛车（官方队 <3t 口径）
M_DEFENDER = 2485  # Defender Dakar D7X-R（达喀尔官网 competitor 页口径）


def v_ms(km, sec):
    return (km * 1000.0) / sec


def power_kw(m, cr, v):
    return (m * G * cr + 0.5 * RHO * CDA * v * v) * v / 1000.0


def sec(t):
    p = t.strip().split(':')
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def calibrate():
    """用项目 SS9 锚点反标定软沙 cr"""
    m, kmh, pkw = 2900, 45.0, 100.0
    v = kmh / 3.6
    f_total = pkw * 1000 / v
    f_air = 0.5 * RHO * CDA * v * v
    cr = (f_total - f_air) / (m * G)
    return cr, v, f_air, f_total


def load_ht(path):
    """环塔 CSV：第0列=车号"""
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    return {r[0]: r for r in rows[1:]}


def load_dakar(path):
    """达喀尔 CSV：第0列=组别, 第1列=车号"""
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    return {r[1]: r for r in rows[1:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sensitivity', action='store_true', help='打印 cr 敏感性')
    ap.add_argument('--offroad-csv', default=r'D:\Project\dsh_rally_cars\offroad\环塔2026_T1+_逐车逐赛段成绩.csv')
    ap.add_argument('--offroad-t2csv', default=r'D:\Project\dsh_rally_cars\offroad\环塔2026_总成绩.csv')
    ap.add_argument('--dakar-csv', default=r'D:\Project\dsh_rally_cars\offroad\达喀尔2026_T1+与T2_逐车逐赛段成绩.csv')
    args = ap.parse_args()

    cr_sand, v_a, f_air, f_tot = calibrate()
    print('=== 标定（项目 2026-08 SS9 纯沙漠锚点：3t 车 45km/h → 轮上 100kW）===')
    print(f'  v={v_a:.2f} m/s | 空阻={f_air:.0f} N | 总阻力={f_tot:.0f} N | 滚阻={f_tot-f_air:.0f} N')
    print(f'  → 软沙等效 cr ≈ {cr_sand:.3f}（公路 0.01-0.02 / 硬戈壁 0.03-0.05 / 松沙 ~0.28）\n')

    # ---- 环塔：鹿丙龙 vs 坦克700 ----
    ht_t1 = load_ht(args.offroad_csv)
    ht_t2 = load_ht(args.offroad_t2csv)
    d104, d251 = ht_t1['104'], ht_t2['251']
    print('=== 环塔 2026：鹿丙龙 #104 (JJ3 T1+ ~2t) vs 坦克700 #251 (T2.E ~3t) ===')
    print(f'{"SS":<4}{"里程km":>8}{"地形":>16}{"鹿km/h":>8}{"鹿kW":>8}{"坦km/h":>8}{"坦kW":>8}{"坦/鹿v":>8}{"坦/鹿kW":>9}')
    for ss, km in sorted(HT_DIST.items()):
        t1s, t2s = sec(d104[5 + ss - 1]), sec(d251[5 + ss - 1])
        v1, v2 = v_ms(km, t1s), v_ms(km, t2s)
        cr = TERRAIN_CR[HT_TERRAIN[ss]]
        p1, p2 = power_kw(M_LU_T1P, cr, v1), power_kw(M_TANK700, cr, v2)
        print(f'SS{ss:<2}{km:>8.1f}{HT_TERRAIN[ss]:>16}{v1*3.6:>8.1f}{p1:>8.1f}{v2*3.6:>8.1f}{p2:>8.1f}{v2/v1:>8.2f}{p2/p1:>9.2f}')

    # ---- 达喀尔：韩魏 vs 路虎 ----
    dk = load_dakar(args.dakar_csv)
    d220, d502 = dk['220'], dk['502']
    print('\n=== 达喀尔 2026：韩魏 #220 (T1+ ~2t) vs 路虎 D7X-R #502 (T2 2485kg) ===')
    print(f'{"SS":<4}{"Special":>8}{"韩km/h":>8}{"韩kW":>8}{"虎km/h":>8}{"虎kW":>8}{"虎/韩v":>8}{"虎/韩kW":>9}')
    for ss in range(1, 14):
        km = DK_DIST[ss]
        v1 = v_ms(km, sec(d220[5 + ss - 1]))
        v2 = v_ms(km, sec(d502[5 + ss - 1]))
        cr = 0.10  # 达喀尔混合地形粗估（沙+砾石+峡谷）
        p1, p2 = power_kw(M_HANWEI, cr, v1), power_kw(M_DEFENDER, cr, v2)
        print(f'SS{ss:<2}{km:>8}{v1*3.6:>8.1f}{p1:>8.1f}{v2*3.6:>8.1f}{p2:>8.1f}{v2/v1:>8.2f}{p2/p1:>9.2f}')

    # ---- 散热死区（坦克700 为准，SS3 归一）----
    print('\n=== 散热死区量化（坦克700；SS3 戈壁 = 1.00）===')
    ref_v = v_ms(HT_DIST[3], sec(d251[5 + 3 - 1]))
    ref_p = power_kw(M_TANK700, TERRAIN_CR[HT_TERRAIN[3]], ref_v)
    print(f'{"SS":<5}{"负荷kW":>9}{"速度km/h":>10}{"迎风(相对)":>11}{"负荷(相对)":>11}')
    for ss in (3, 1, 7, 8, 9):
        v = v_ms(HT_DIST[ss], sec(d251[5 + ss - 1]))
        p = power_kw(M_TANK700, TERRAIN_CR[HT_TERRAIN[ss]], v)
        print(f'SS{ss:<3}{p:>9.1f}{v*3.6:>10.1f}{v/ref_v:>11.2f}{p/ref_p:>11.2f}')

    if args.sensitivity:
        print('\n=== 敏感性：cr 假设 ±30%（鹿丙龙 SS9）===')
        km, ss = HT_DIST[9], 9
        v = v_ms(km, sec(d104[5 + ss - 1]))
        for f in (0.7, 0.85, 1.0, 1.15, 1.3):
            print(f'  cr={cr_sand*f:.3f}: {power_kw(M_LU_T1P, cr_sand*f, v):.0f} kW')


if __name__ == '__main__':
    main()
