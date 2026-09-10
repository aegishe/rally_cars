# -*- coding: utf-8 -*-
"""
奥迪 RS Q e-tron（T1U 增程）达喀尔功率反推 —— 含 2024 逐段数据

数据来源与口径：
  · 2024 达喀尔 Sainz/Cruz 总成绩 48:15:18（汽车组冠军）
  · 逐段用时：由 Wikipedia 的 GC（General Classification）累计时间差分得到
      gc = {SS1:04:37:43 ... SS12:48:15:18}，差分段用时合计 = 总成绩（首尾闭合）
      校验：SS6 7:23:57 / SS9 4:21:47 / SS11 4:48:35 与 Wikipedia 直接给出的赛段成绩逐秒吻合
  · Special 里程：redbull.com 2024 route（Sainz 段合计 4,648 km；官方 4,727 km，差 79 km 为 prologue/口径边界）
  · 重量：**2,100 kg 是 FIA T1U 组最低重量要求（规则下限、不含燃油），非奥迪实际车重**
          —— 媒体："The RS Q e-tron weighs more than this target"
    油箱 340 L（2024 版）→ 满油约 +255 kg；本脚本主用含半油 2,330 kg
  · 持续能力：增程器最大发电 220 kW；规则前后轴功率上限 286 kW；峰值合计 419 kW；电池 52 kWh

用法：
    python offroad/scripts/audi_power.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

G, RHO, CDA = 9.81, 1.225, 1.5
M_HALF_FUEL = 2330     # 含半油（估）
CONT_KW = 220          # 增程器持续发电

GC = {1: '04:37:43', 2: '08:49:38', 3: '13:07:58', 4: '15:49:08', 5: '17:35:35',
      6: '24:59:32', 7: '30:06:42', 8: '33:29:10', 9: '37:50:57', 10: '41:36:12',
      11: '46:24:47', 12: '48:15:18'}
DIRECT = {6: '07:23:57', 9: '04:21:47', 11: '04:48:35'}   # Wikipedia 直接给出的段成绩（校验用）
KM = {1: 405, 2: 470, 3: 440, 4: 299, 5: 118, 6: 532, 7: 483, 8: 458, 9: 417, 10: 371, 11: 480, 12: 175}
CR = {1: 0.06, 2: 0.08, 3: 0.10, 4: 0.06, 5: 0.25, 6: 0.20, 7: 0.10, 8: 0.10, 9: 0.07, 10: 0.09, 11: 0.08, 12: 0.07}
TERR = {1: '岩石/火山', 2: '快速+30km沙丘', 3: '马拉松碎石+沙', 4: '快速', 5: '沙丘(空白区)',
        6: '48h Chrono 沙丘', 7: '峡谷+沙丘', 8: '软沙转硬地(含中立区)', 9: '岩石',
        10: '山地技术', 11: '崎岖荒芜', 12: '岩石冲刺'}


def s(t):
    h, m, sec = t.split(':')
    return int(h) * 3600 + int(m) * 60 + int(sec)


def p_kw(m, cr, v):
    return (m * G * cr + 0.5 * RHO * CDA * v * v) * v / 1000.0


def main():
    print('=== 奥迪 RS Q e-tron 2024 达喀尔逐段（Sainz，冠军）===')
    print(f'{"SS":<4}{"Special":>8}{"地形":<22}{"段用时":>10}{"校验":>6}{"速度km/h":>9}{"需求kW":>8}{"负荷率":>8}')
    prev, total = 0, 0
    vals = []
    for ss in range(1, 13):
        cum = s(GC[ss])
        seg = cum - prev
        prev = cum
        total += seg
        v = KM[ss] * 1000 / seg
        p = p_kw(M_HALF_FUEL, CR[ss], v)
        chk = ''
        if ss in DIRECT:
            chk = '✓' if s(DIRECT[ss]) == seg else '✗'
        warn = ' ⚠' if ss == 8 else ''
        print(f'SS{ss:<2}{KM[ss]:>8}{TERR[ss]:<22}{seg//3600}:{seg%3600//60:02d}:{seg%60:02d}'
              f'{chk:>6}{v*3.6:>9.1f}{p:>8.1f}{p/CONT_KW*100:>7.0f}%{warn}')
        if ss != 8:
            vals.append((ss, p, v * 3.6))
    print(f'\n  段用时合计 {total//3600}:{total%3600//60:02d}:{total%60:02d}（= 总成绩 48:15:18，首尾闭合 ✓）')
    print(f'  里程合计 {sum(KM.values())} km（官方 4,727 km，差 79 km 为 prologue/口径边界）')
    print(f'  功率区间（剔除 SS8 中立区伪高值）：{min(v[1] for v in vals):.0f}–{max(v[1] for v in vals):.0f} kW'
          f'，负荷率 {min(v[1] for v in vals)/CONT_KW*100:.0f}–{max(v[1] for v in vals)/CONT_KW*100:.0f}%')
    print('  ⚠ SS8 含中立区(neutralisation zone)，458km 含非计时段 → 速度/功率为伪高值，不参与结论')
    print()

    print('=== 沙地段对照（奥迪 SS5/SS6 vs 环塔 SS9）===')
    for name, m, cr, kmh, cont in [('奥迪 SS5 (66.5km/h)', 2330, 0.25, 66.5, 220),
                                   ('奥迪 SS6 (71.9km/h)', 2330, 0.20, 71.9, 220),
                                   ('奥迪 若换 110kW 增程器(SS5)', 2330, 0.25, 66.5, 110),
                                   ('鹿丙龙 T1+ 环塔 SS9', 2000, 0.276, 74.5, 280),
                                   ('坦克700 P2 环塔 SS9', 3000, 0.276, 55.4, 190),
                                   ('猛士M817 环塔 SS9', 2900, 0.276, 53.5, 110),
                                   ('纵横G700 环塔 SS9', 3100, 0.276, 52.8, 110)]:
        v = kmh / 3.6
        p = p_kw(m, cr, v)
        flag = '  ← 超载' if p > cont else ''
        print(f'  {name:<28}{m:>5}kg @ {kmh:>5.1f} → {p:>6.1f} kW / {cont:>3} kW = {p/cont*100:>4.0f}%{flag}')


if __name__ == '__main__':
    main()
