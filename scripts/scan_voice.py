# -*- coding: utf-8 -*-
"""验证假设：篇5"好很多"是不是因为「人（第一人称）在场」+「给了入口」。

指标：
  - 第一人称密度（每千字"我/自己"）
  - 首屏字数（正文前两段）——决定 B 类读者会不会划走
  - 是否有长求总/摘要入口
  - 总体量（字数/小节数）
"""
import os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PUB = r"D:\Project\dsh_rally_cars\publish"
FILES = [
    ('篇1  越野篇',   '篇1-3400公里之后谁还在-环塔架构重量与动力边界.md'),
    ('篇1s 悬架篇',   '篇1s-悬架选型铁三角-规则场景强度故障容忍度.md'),
    ('篇2  纽北回归', '篇2-2977马力的真相-纽北回归与U9X功率反推.md'),
    ('篇2s 全圈账本', '篇2s-同一套1548马力两个重量-SU7与U9X纽北全圈账本.md'),
    ('篇3  爬坡两副面孔', '篇3-爬坡的两副面孔-沙地陡坡与派克峰.md'),
    ('篇4  布局重量', '篇4-布局、重量和其他-腾势Z你嘛时候纽北纯电量产车第一.md'),
    ('篇5  终极越野车', '篇5-如果我来造一台终极越野车-把发动机搬到车尾的后置四驱布局纸上推演.md'),
    ('篇6  家用选车', '篇6-买车之前先问自己五个问题-家用选车需求自知.md'),
    ('篇6s 营销费用', '篇6s-营销费用的三层读法-总量单车费用率.md'),
]


def cn(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))


rows = []
for label, fn in FILES:
    p = os.path.join(PUB, fn)
    if not os.path.exists(p):
        print(f'[缺] {fn}')
        continue
    raw = open(p, encoding='utf-8', errors='replace').read()
    body = re.sub(r'```.*?```', '', raw, flags=re.S)
    body = re.sub(r'\[quote\].*?\[/quote\]', '', body, flags=re.S)
    body = re.sub(r'\[img\].*?\[/img\]|\[img\]\S+', '', body)
    total = cn(body)
    k = max(total / 1000, .001)
    me = len(re.findall(r'我(?!们)', body)) + len(re.findall(r'咱们', body))
    paras = [x.strip() for x in re.split(r'\n\s*\n', body)
             if cn(x) >= 15 and not x.strip().startswith(('#', '|', '-', '>', '!'))]
    first = cn(paras[0]) if paras else 0
    second = cn(paras[1]) if len(paras) > 1 else 0
    has_tldr = bool(re.search(r'长求总|太长不看|摘要|结论先行|一句话(?:总结|版本)', body))
    sections = len(re.findall(r'^\s*(?:#|\[size=)', body, flags=re.M))
    rows.append((label, total, k, me, me / k, first, first + second,
                 len(paras), sections, has_tldr))

print(f'{"篇目":<18}{"字数":>7}{"段数":>6}{"小节":>6}{"我":>5}{"我/千字":>8}{"首段":>6}{"首屏":>6}{"入口":>5}')
for r in rows:
    print(f'{r[0]:<18}{r[1]:>7}{r[7]:>6}{r[8]:>6}{r[3]:>5}{r[4]:>8.1f}{r[5]:>6}{r[6]:>6}{"有" if r[9] else "—":>5}')
print('\n首屏 = 正文前两段合计字数（B 类读者要不要划走的第一个门槛）')
print('入口 = 是否有"长求总/太长不看/摘要/结论先行"这类显式入口')
