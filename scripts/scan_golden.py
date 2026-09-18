# -*- coding: utf-8 -*-
"""测「金句节拍器」的直接形态：独立加粗短句的数量与分布。

篇3 清理实录显示，清理动作的核心之一是"拆金句加粗"——
即每段末尾那个 **[b]短断言[/b]**。这是可精确定位的节拍器指纹。
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
    'nga/篇3-4300米上马力是软通货-派克峰爬坡功率税-nga.txt',
    'nga/篇3-4300米上马力是软通货-派克峰爬坡功率税-优化版-nga.txt',
]


def cn(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))


rows = []
for a in (sys.argv[1:] or DEFAULT):
    p = a if os.path.isabs(a) else os.path.join(PUB, a)
    if not os.path.exists(p):
        continue
    raw = open(p, encoding='utf-8', errors='replace').read()
    total = cn(raw)
    # 收集所有加粗片段（md 与 bbcode 两种写法）
    bolds = re.findall(r'\*\*([^*\n]{2,60})\*\*', raw) + re.findall(r'\[b\]([^\[]+)\[/b\]', raw)
    short = [b for b in bolds if 4 <= cn(b) <= 28 and '：' not in b and ':' not in b]
    longb = [b for b in bolds if cn(b) > 28]
    # 段尾加粗：段落以加粗片段结尾
    paras = [x.strip() for x in re.split(r'\n\s*\n', raw) if cn(x) >= 20]
    tail_bold = 0
    for x in paras:
        if re.search(r'(\*\*[^*\n]{2,60}\*\*|\[b\][^\[]+\[/b\])\s*$', x):
            tail_bold += 1
    rows.append({'f': os.path.basename(p), 'cn': total, 'bold': len(bolds),
                 'short': len(short), 'long': len(longb), 'tail': tail_bold,
                 'paras': len(paras), 'k': max(total / 1000, .001)})

rows.sort(key=lambda r: -(r['short'] / r['k']))
print(f'{"文稿":<48}{"千字":>6}{"加粗总":>7}{"短加粗":>7}{"每千字":>7}{"长加粗":>7}{"段尾粗":>7}{"段数":>5}')
for r in rows:
    print(f'{r["f"][:46]:<48}{r["k"]:>6.1f}{r["bold"]:>7}{r["short"]:>7}'
          f'{r["short"]/r["k"]:>7.1f}{r["long"]:>7}{r["tail"]:>7}{r["paras"]:>5}')
print('\n短加粗 = 4–28 字、不含冒号的加粗片段（= 金句式断言）')
print('段尾粗 = 以加粗片段结尾的段落数（= "每段一发"的直接形态）')
