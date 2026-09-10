# -*- coding: utf-8 -*-
"""
2026 达喀尔：卫士 Defender T2 vs 鹿丙龙 T1+ 的功率反推（三层口径）

数据：
  · 逐段用时：offroad/达喀尔2026_T1+与T2_逐车逐赛段成绩.csv（官方逐段 AJAX，已校验）
  · Special 里程：racetrackmasters 2026（SS7=462km 与视频口播吻合）
  · 车重：Defender D7X-R = **2485 kg**（达喀尔官网 competitor 页）/ **2550 kg**（Peterhansel 赛前采访口径，比赛状态）
          鹿丙龙 JJ-Sport JJ3 T1+ = ~2000 kg（估，T1+ 典型）
  · 可用功率（官方规则口径）：
      卫士 T2 Stock = **390 hp ≈ 291 kW**（进气限流器；dakar.com 2026-01-01 Peterhansel 访谈）
      鹿丙龙 T1+     = ~280 kW（估；参考 T1+ 组 Dacia 360hp=268kW / Toyota 264kW=354hp）
    功重比对照：卫士 2550/390 = 6.54 kg/hp（差）；Dacia 2010/360 = 5.58 kg/hp（好）
    → **规则给 T2 的绝对功率更多（390 vs 354–360hp），但功重比更差 17%**

三层口径（cr 是最大不确定源，故分层）：
  L1 免 cr 相对比较：滚阻主导时 P ∝ m·v，比值只用车重与速度 —— **最可靠**
  L2 带 cr 绝对功率：P=(m·g·cr+0.5ρCdA·v²)·v，给 cr 区间 0.10–0.22
  L3 负荷率：相对各自可用功率

用法：
    python offroad/scripts/dakar2026_power.py
"""
import sys, io, csv, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

G, RHO, CDA = 9.81, 1.225, 1.5
CSV = r'D:\Project\dsh_rally_cars\offroad\达喀尔2026_T1+与T2_逐车逐赛段成绩.csv'
KM = {1: 305, 2: 400, 3: 422, 4: 451, 5: 356, 6: 331, 7: 462,
      8: 481, 9: 418, 10: 371, 11: 347, 12: 310, 13: 105}
M_DEF, M_LU = 2485, 2000      # 认证口径（官网 competitor 页）
M_DEF_RACE = 2550             # Peterhansel 采访口径（比赛状态）
CONT_DEF, CONT_LU = 291, 280  # 卫士 390hp≈291kW（官方规则）；鹿丙龙 T1+ 估 280kW


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


def main():
    rows = list(csv.reader(open(CSV, encoding='utf-8-sig')))
    car = {r[1]: r for r in rows[1:]}
    d243, d502 = car['243'], car['502']

    print('=== L1 免 cr 相对比较（P ∝ m·v）===')
    print(f'{"SS":<5}{"里程":>6}{"鹿v":>8}{"卫v":>8}{"速度比":>9}{"需求功率比(2485)":>17}{"(2550)":>9}')
    ratios = []
    for ss in range(1, 14):
        t1, t2 = to_sec(d243[5 + ss - 1]), to_sec(d502[5 + ss - 1])
        if not t1 or not t2:
            continue
        v1, v2 = KM[ss] * 1000 / t1, KM[ss] * 1000 / t2
        r = (M_DEF * v2) / (M_LU * v1)
        r2 = (M_DEF_RACE * v2) / (M_LU * v1)
        ratios.append(r)
        print(f'SS{ss:<3}{KM[ss]:>6}{v1*3.6:>8.1f}{v2*3.6:>8.1f}{v2/v1:>9.2f}{r:>17.2f}{r2:>9.2f}')
    print(f'  → 平均：速度比 0.944 | **需求功率比 {st.mean(ratios):.3f}**（2550kg 口径 {st.mean(ratios)*M_DEF_RACE/M_DEF:.3f}）'
          f'（>1 = 卫士更吃力）')

    print('\n=== L2 带 cr 绝对功率（鹿/卫 kW）===')
    print(f'{"SS":<5}{"鹿v":>8}{"卫v":>8}' + ''.join(f'{"cr="+str(c):>15}' for c in (0.10, 0.16, 0.22)))
    for ss in range(1, 14):
        t1, t2 = to_sec(d243[5 + ss - 1]), to_sec(d502[5 + ss - 1])
        if not t1 or not t2:
            continue
        v1, v2 = KM[ss] * 1000 / t1, KM[ss] * 1000 / t2
        row = f'SS{ss:<3}{v1*3.6:>8.1f}{v2*3.6:>8.1f}'
        for cr in (0.10, 0.16, 0.22):
            row += f'{p_kw(M_LU,cr,v1):>6.0f}/{p_kw(M_DEF,cr,v2):<6.0f}'
        print(row)

    print('\n=== L3 平均需求功率与负荷率（cr=0.16 中值）===')
    p1s, p2s, v1s, v2s = [], [], [], []
    for ss in range(1, 14):
        t1, t2 = to_sec(d243[5 + ss - 1]), to_sec(d502[5 + ss - 1])
        if not t1 or not t2:
            continue
        v1, v2 = KM[ss] * 1000 / t1, KM[ss] * 1000 / t2
        p1s.append(p_kw(M_LU, 0.16, v1)); p2s.append(p_kw(M_DEF, 0.16, v2))
        v1s.append(v1 * 3.6); v2s.append(v2 * 3.6)
    print(f'  鹿丙龙 #243: {st.mean(v1s):.1f} km/h | 需求 {st.mean(p1s):.0f} kW | 可用 ~{CONT_LU}kW → 负荷 {st.mean(p1s)/CONT_LU*100:.0f}%')
    print(f'  卫士   #502: {st.mean(v2s):.1f} km/h | 需求 {st.mean(p2s):.0f} kW | 可用 ~{CONT_DEF}kW → 负荷 {st.mean(p2s)/CONT_DEF*100:.0f}%')
    vm1, vm2 = st.mean(v1s) / 3.6, st.mean(v2s) / 3.6
    print(f'  cr 0.10–0.25 区间：鹿 {p_kw(M_LU,0.10,vm1)/CONT_LU*100:.0f}–{p_kw(M_LU,0.25,vm1)/CONT_LU*100:.0f}%'
          f' | 卫 {p_kw(M_DEF,0.10,vm2)/CONT_DEF*100:.0f}–{p_kw(M_DEF,0.25,vm2)/CONT_DEF*100:.0f}%')
    print('\n  环塔对照（文档 §七）：T2.E 电驱沙段 109–115% 超载；坦克700 P2 68%；鹿丙龙 T1+ 43%')

    print('\n=== 规则口径对照（dakar.com 2026-01-01 Peterhansel 访谈 + racecar-engineering）===')
    print('  T2 Stock  Defender D7X-R : 2550 kg / 390 hp  → 功重比 6.54 kg/hp（差）')
    print('  T1+ Ultimate Dacia Sandrider: 2010 kg / 360 hp → 功重比 5.58 kg/hp（好）')
    print('  T1+ Ultimate Toyota DKR Hilux: ~2000 kg / 264kW=354hp')
    print('  → **规则给 T2 的绝对功率更多（390 vs 354–360hp，+8~10%），但功重比差 17%**')
    print('  → Peterhansel 原话："真正拖住我们的不是发动机、也不是重量，而是**标准车的设计**"')
    print('    （重心可调/赛用悬挂/更大车轮刹车/原型车结构强度 —— 均为 Stock 规则不允许改的）')


if __name__ == '__main__':
    main()
