# -*- coding: utf-8 -*-
"""
考虑车重差异的平均功率对照 + 负荷率（T2 内部三架构 vs T1+ 鹿丙龙）

模型：P_轮端 = ( m·g·cr + 0.5·ρ·Cd·A·v² ) · v
三个派生指标：
  1. 需求功率 kW      —— 维持该平均速度所需的轮端功率
  2. 单位质量功率 W/kg —— 去掉车重影响的功率密度需求（主要反映速度）
  3. 负荷率 = 需求 ÷ 该架构"持续可用功率"  ← 真正判断"谁吃力"的指标
     需求功率高低本身不说明问题，要看它相对该架构的持续供给上限

车重口径（估算，±10%，逐条标注来源）：
  · T1+ 鹿丙龙 JJ3       ~2000kg  估值（T1+ 典型 1.8–2.1t），待官方
  · T2.E P2 坦克700       ~3000kg  官方队 <3t（不含燃油，项目口径）
  · T2.E P2 坦克300       ~2600kg  项目文档"约2.6吨"
  · T2.1 燃油 火炮V6      ~2500kg  估值（火炮皮卡量产+赛车装备）
  · T2.E 电驱 猛士M817    ~2900kg  项目表格 2.8–3.0t
  · T2.E 电驱 纵横G700    ~3100kg  量产 3063–3303kg
  · T2.E 电驱 纵横F700    ~3000kg  估值

持续可用功率口径：
  · T1+ 原型             ~280kW  估值（大排量原型，待官方）
  · 3.0T V6 直驱          ~190kW  项目口径（坦克700 3.0T 持续 190kW）
  · 电驱（P1+P3+P4）      ~110kW  项目口径（M817 官方"持续 110kW"；区间 100–118kW）

用法：
    python offroad/scripts/power_mass.py
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

G, RHO, CDA = 9.81, 1.225, 1.5
T2_CSV = r'D:\Project\dsh_rally_cars\offroad\环塔2026_总成绩.csv'
T1_CSV = r'D:\Project\dsh_rally_cars\offroad\环塔2026_T1+_逐车逐赛段成绩.csv'

OBJS = [
    ('T1+ 鹿丙龙 JJ3', '104', 2000, 280, 'T1+ 原型'),
    ('P2混动 坦克700 Hi4-T', '251', 3000, 190, 'P2 3.0T'),
    ('P2混动 坦克300 Hi4-T', '262', 2600, 190, 'P2 2.0T'),
    ('燃油 V6 火炮', '257', 2500, 190, '燃油 V6 直驱'),
    ('电驱 猛士M817', '270', 2900, 110, '电四驱'),
    ('电驱 纵横G700', '278', 3100, 110, '电四驱'),
    ('电驱 纵横F700', '275', 3000, 110, '电四驱'),
]
DIST = {10: ('SS10 短沙 214.35km', 214.35, 0.240),
        8:  ('SS8 中沙 288.10km', 288.10, 0.180),
        9:  ('SS9 长沙 353.66km', 353.66, 0.276),
        3:  ('SS3 戈壁 468.95km', 468.95, 0.035)}


def to_sec(t):
    if not t:
        return None
    p = t.strip().split(':')
    try:
        return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
    except ValueError:
        return None


def p_kw(m, cr, v):
    return (m * G * cr + 0.5 * RHO * CDA * v * v) * v / 1000.0


def solve_v(p_w, m, cr):
    lo, hi = 1.0, 60.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if p_kw(m, cr, mid) * 1000 < p_w:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    t2 = {r[0]: r for r in list(csv.reader(open(T2_CSV, encoding='utf-8-sig')))[1:]}
    t1 = {r[0]: r for r in list(csv.reader(open(T1_CSV, encoding='utf-8-sig')))[1:]}

    for ss in (10, 8, 9, 3):
        label, km, cr = DIST[ss]
        print(f'--- {label}  (cr={cr}) ---')
        print(f'{"对象":<22}{"质量kg":>7}{"用时":>10}{"速度":>8}{"需求kW":>8}{"W/kg":>7}{"持续kW":>8}{"负荷率":>8}')
        for name, bib, m, cont, arch in OBJS:
            r = t1.get(bib) or t2.get(bib)
            t = to_sec(r[5 + ss - 1]) if r else None
            if not t:
                print(f'{name:<22}{m:>7}{"缺席":>10}')
                continue
            v = km * 1000 / t
            p = p_kw(m, cr, v)
            flag = '  ← 超载' if p > cont else ''
            print(f'{name:<22}{m:>7}{r[5+ss-1]:>10}{v*3.6:>7.1f} {p:>7.1f}{p*1000/m:>7.1f}{cont:>8}{p/cont*100:>7.0f}%{flag}')
        print()

    print('--- 减重推演：坦克700 同功率下减重能快多少（SS9）---')
    km, cr = DIST[9][1], DIST[9][2]
    t = to_sec(t2['251'][5 + 8])
    v0 = km * 1000 / t
    p0 = p_kw(3000, cr, v0)
    print(f'  现状 3000kg @ {v0*3.6:.1f} km/h，需求 {p0:.1f} kW')
    for mm in (3000, 2600, 2000):
        v = solve_v(p0 * 1000, mm, cr)
        print(f'  同功率 {p0:.0f}kW @ {mm}kg → {v*3.6:.1f} km/h ({(v/v0-1)*100:+.0f}%)')
    print()
    print('--- 对照：T1+ 鹿丙龙同段功率与速度 ---')
    t = to_sec(t1['104'][5 + 8])
    v = km * 1000 / t
    p = p_kw(2000, cr, v)
    print(f'  2000kg @ {v*3.6:.1f} km/h，需求 {p:.1f} kW，负荷率 {p/280*100:.0f}%')
    print(f'  → 比坦克700 快 {(v/v0-1)*100:+.0f}%，需求功率还低 {(1-p/p0)*100:.0f}%')


if __name__ == '__main__':
    main()
