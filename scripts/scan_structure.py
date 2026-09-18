# -*- coding: utf-8 -*-
"""扫描结构层 AI 痕迹：段尾节拍（金句节拍器）+ 相邻句结构同款。

用法：python scan_structure.py [文件 ...]
"""
import os, re, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PUB = r"D:\Project\dsh_rally_cars\publish"
DEFAULT = [
    '篇1-3400公里之后谁还在-环塔架构重量与动力边界.md',
    '篇1s-悬架选型铁三角-规则场景强度故障容忍度.md',
    '篇2-2977马力的真相-纽北回归与U9X功率反推.md',
    '篇2s-同一套1548马力两个重量-SU7与U9X纽北全圈账本.md',
    '篇3-爬坡的两副面孔-沙地陡坡与派克峰.md',
    '篇4-布局、重量和其他-腾势Z你嘛时候纽北纯电量产车第一.md',
    '篇5-如果我来造一台终极越野车-把发动机搬到车尾的后置四驱布局纸上推演.md',
    '篇6-买车之前先问自己五个问题-家用选车需求自知.md',
    '篇6s-营销费用的三层读法-总量单车费用率.md',
]

SKIP = re.compile(r'^\s*(#|\||>|!\[|\[img|```|-\s|\d+\.\s|\*|\*\*)')


def paras(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    out = []
    for p in re.split(r'\n\s*\n', text):
        s = p.strip()
        if not s or SKIP.match(s):
            continue
        if len(re.findall(r'[\u4e00-\u9fff]', s)) < 20:
            continue
        out.append(s)
    return out


def sents(p):
    return [x.strip() for x in re.split(r'(?<=[。！？])', p) if x.strip()]


def scan(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    ps = paras(raw)
    tails, heads, lens, pair_same = [], [], [], 0
    for p in ps:
        ss = sents(p)
        if not ss:
            continue
        last = ss[-1]
        n = len(re.findall(r'[\u4e00-\u9fff]', last))
        tails.append(last)
        lens.append(n)
        heads.append(last[:2])
    # 相邻句结构同款：同段内相邻两句 逗号数相同 且 长度接近
    for p in ps:
        ss = sents(p)
        for a, b in zip(ss, ss[1:]):
            ca, cb = a.count('，'), b.count('，')
            la, lb = len(a), len(b)
            if ca == cb and ca >= 1 and abs(la - lb) <= max(la, lb) * 0.3:
                pair_same += 1
    short = [t for t, n in zip(tails, lens) if n <= 25 and '，' not in t]
    from collections import Counter
    hc = Counter(heads)
    near = 0
    for i in range(len(lens) - 2):
        w = lens[i:i + 3]
        m = sum(w) / 3
        if m and all(abs(x - m) <= m * 0.35 for x in w):
            near += 1
    return {
        'file': os.path.basename(path), 'paras': len(ps),
        'tail_avg': sum(lens) / max(len(lens), 1),
        'short_rate': len(short) / max(len(ps), 1),
        'heads': hc.most_common(4),
        'near3': near, 'pair_same': pair_same,
        'para_words': sum(len(re.findall(r'[\u4e00-\u9fff]', p)) for p in ps),
    }


targets = []
for a in (sys.argv[1:] or DEFAULT):
    p = a if os.path.isabs(a) else os.path.join(PUB, a)
    targets += sorted(glob.glob(os.path.join(p, '*.md'))) if os.path.isdir(p) else ([p] if os.path.exists(p) else [])

rows = sorted([scan(p) for p in targets], key=lambda r: -r['short_rate'])
print(f'{"文稿":<46}{"段数":>5}{"尾句均长":>8}{"短断言率":>9}{"3段近长":>8}{"相邻同款":>9}')
for r in rows:
    print(f'{r["file"][:44]:<46}{r["paras"]:>5}{r["tail_avg"]:>8.1f}{r["short_rate"]*100:>8.0f}%{r["near3"]:>8}{r["pair_same"]:>9}')
print('\n注：短断言率 = 段尾句 ≤25 字且不含逗号的比例（高 = 每段都以短金句收尾 = 节拍器）')
print('    相邻同款 = 同段内相邻两句逗号数相同且长度接近的次数（规则3的近似口径）')
print('\n==== 段尾句首二字分布（重复 = 收尾方式单一）====')
for r in rows:
    print(f'{r["file"][:40]:<42} ' + ' · '.join(f'{w}×{c}' for w, c in r['heads']))
