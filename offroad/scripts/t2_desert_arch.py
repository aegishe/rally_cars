# -*- coding: utf-8 -*-
"""
T2 大组内部：沙漠赛段的架构分野（短沙 vs 长沙）——双口径

口径 A（比赛成绩）：全部有效样本（剔除 >20h 罚时封顶/缺席）
口径 B（纯行驶能力）：在 A 基础上，再剔除"车辆自身跨段异常"样本
    判据：某车在纯沙漠某段用时 > 该车自身其他纯沙漠段用时中位数 × 1.3
          → 判该段异常（含罚时/故障嫌疑）
    用"车辆自身跨段一致性"而非"组内排名"判异常，避免把"车手慢"误判为"车有问题"

输出：组平均用时 / 平均速度 / 组内最快 / 相对最快组 / 异常样本清单

用法：
    python offroad/scripts/t2_desert_arch.py
"""
import sys, io, csv, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CSV_PATH = r'D:\Project\dsh_rally_cars\offroad\环塔2026_总成绩.csv'

# 纯沙漠三段（长度阶梯）
DESERT = {10: ('短沙 N39（纯沙漠·最短）', 214.35),
          8:  ('中沙 克里雅河（纯沙漠）', 288.10),
          9:  ('长沙 红白山（纯沙漠·最长）', 353.66)}
# 混合地形（参考）
MIXED = {2: ('混合 库木塔格（60%沙+40%戈壁）', 293.08),
         5: ('混合 英吾斯塘魔鬼段', 281.32)}

CLASS = {
    '燃油 V6 火炮（T2.1）': ['257', '258', '259'],
    '混动 P2 3.0T（坦克700系）': ['251', '252', '253', '260', '261'],
    '混动 P2 2.0T（坦克300系）': ['256', '262', '263'],
    '电四驱（猛士 M817）': ['270', '271', '272', '273'],
    '电四驱（纵横 F700）': ['275', '276', '277'],
    '电四驱（纵横 G700）': ['278', '279', '280'],
    '燃油其他（212/D-MAX/火炮2.0等）': ['265', '266', '267', '268', '269', '282', '283', '285', '291', '293'],
}
PENALTY_CUT = 20 * 3600   # >20h 视为罚时封顶/缺席
ABNORMAL_RATIO = 1.3      # 自身其他段中位数的 1.3 倍以上 → 异常


def to_sec(t):
    if not t:
        return None
    p = t.strip().split(':')
    try:
        return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
    except ValueError:
        return None


def hm(s):
    s = int(round(s))
    return f'{s//3600}:{s%3600//60:02d}:{s%60:02d}'


def main():
    rows = list(csv.reader(open(CSV_PATH, encoding='utf-8-sig')))
    D = {r[0]: r for r in rows[1:]}

    # 收集每车在纯沙漠段的用时
    car_t = {}
    for ss in DESERT:
        for bibs in CLASS.values():
            for b in bibs:
                r = D.get(b)
                t = to_sec(r[5 + ss - 1]) if r else None
                if t and t < PENALTY_CUT:
                    car_t.setdefault(b, {})[ss] = t

    # 判定异常样本
    abnormal = {}
    for b, d in car_t.items():
        if len(d) < 2:
            continue
        for ss, t in d.items():
            med = st.median([v for k, v in d.items() if k != ss])
            if t > med * ABNORMAL_RATIO:
                abnormal[(b, ss)] = t / med

    print('=== 异常样本（含罚时/故障嫌疑，口径 B 剔除）===')
    if abnormal:
        for (b, ss), k in sorted(abnormal.items()):
            print(f'  #{b} {D[b][2][:12]:12s} SS{ss} {D[b][5+ss-1]:>10s}  {k:.2f}×自身其他段')
    else:
        print('  无')
    print()

    def speeds(ss, clean=False):
        km = DESERT[ss][1] if ss in DESERT else MIXED[ss][1]
        res = {}
        for g, bibs in CLASS.items():
            vals = [(b, car_t.get(b, {}).get(ss)) for b in bibs]
            vals = [(b, t) for b, t in vals if t]
            if clean:
                vals = [(b, t) for b, t in vals if (b, ss) not in abnormal]
            if vals:
                mt = st.mean([t for _, t in vals])
                res[g] = (km / (mt / 3600), mt, len(vals))
        return res

    for ss in sorted(DESERT):
        label, km = DESERT[ss]
        print(f'=== SS{ss} {label} · {km} km ===')
        a, b = speeds(ss), speeds(ss, clean=True)
        print(f'{"架构组":<30}{"A平均用时":>11}{"A速度":>8}{"nA":>4}{"B平均用时":>12}{"B速度":>8}{"nB":>4}')
        for g in CLASS:
            ra, rb = a.get(g), b.get(g)
            sa = f'{hm(ra[1]):>11}{ra[0]:>8.1f}{ra[2]:>4}' if ra else f'{"—":>11}{"—":>8}{0:>4}'
            sb = f'{hm(rb[1]):>12}{rb[0]:>8.1f}{rb[2]:>4}' if rb else f'{"—":>12}{"—":>8}{0:>4}'
            print(f'{g:<30}{sa}{sb}')
        if a:
            va = [v[0] for v in a.values()]
            print(f'  → 极差：口径A {max(va)-min(va):.1f} km/h', end='')
            if b:
                vb = [v[0] for v in b.values()]
                print(f'  |  口径B {max(vb)-min(vb):.1f} km/h')
                print(f'  → 相对最快组 口径B：' + '  '.join(f'{g.split("（")[0]}={v[0]/max(vb)*100:.0f}%' for g, v in b.items()))
            else:
                print()
        print()

    # 混合地形参考（仅口径 A）
    for ss in sorted(MIXED):
        label, km = MIXED[ss]
        a = speeds(ss)
        if not a:
            continue
        print(f'=== SS{ss} {label} · {km} km（口径 A）===')
        for g, (v, mt, n) in sorted(a.items(), key=lambda x: -x[1][0]):
            print(f'  {v:>6.1f} km/h  平均用时 {hm(mt)}  (n{n})  {g}')
        print()


if __name__ == '__main__':
    main()
