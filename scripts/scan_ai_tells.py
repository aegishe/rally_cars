# -*- coding: utf-8 -*-
"""按 Writing-DNA + lieflat-less-ai-tone 的口径，扫描系列文稿的 AI 痕迹。

用法：python scan_ai_tells.py [文件或目录 ...]
默认扫描 publish/ 下的系列正文。
"""
import os, re, sys, io, glob, html

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

# ① 元叙事：指代文本自身结构（最硬签名，零容忍）
META = [r'这就是本文', r'这正是本文', r'本文(?:要|将|会|只)', r'的下一棒', r'的钥匙',
        r'的落点', r'最有说服力的', r'接下来(?:我们)?(?:看|说)', r'我们不妨', r'让我们',
        r'真正的问题(?:是|在于)', r'值得展开的是', r'下一篇(?:将|会)']
# ② 修辞套路词（禁口语账，留"账面参数/账面马力"）
CLICHE = [r'算账', r'这笔账', r'那一笔账', r'能量账', r'账面好看', r'的账(?![面])',
          r'货币', r'尺子', r'锚点', r'底层逻辑', r'三笔', r'三种账']
# ③ 句子级 AI 腔
AISENT = [r'不仅[^。]{0,24}更', r'与其说', r'换言之', r'这意味着', r'值得注意的是',
          r'综上所述', r'不可否认', r'与此同时', r'更进一步', r'在某种程度上']
# ④ 翻案腔
FANAN = [r'不是[^，。；]{2,24}[，,]\s*而是', r'并非[^，。；]{2,24}[，,]\s*而是',
         r'不在于[^，。；]{2,24}[，,]\s*而在于', r'看似[^，。；]{2,20}[，,]\s*实则',
         r'表面[^，。；]{2,20}[，,]\s*实际', r'你以为[^，。；]{2,24}[，,]\s*其实',
         r'说到底', r'恰恰相反', r'不重要[，,]\s*重要的是', r'这不是[^。]{2,20}。这是']
# ⑤ 冒号滥用（提示语引出）
COLON = [r'(?:一句话总结|核心是|关键在于|原因(?:如下|有两个)|本质上|换句话说|简单说|直白地说)\s*[:：]']
# ⑥ 禁用起手式
OPEN = [r'说白了', r'说穿了', r'先说结论']
# ⑦ 段首零主语评论
ZERO = [r'^\s*(?:听起来|看起来|说白了|值得注意的是|更重要的是|问题在于|这意味着|不难看出)[^，。]{0,20}[，,]']


def clean(t):
    t = re.sub(r'```.*?```', '', t, flags=re.S)
    t = re.sub(r'\[quote\].*?\[/quote\]', '', t, flags=re.S)
    t = re.sub(r'^\[img\].*$', '', t, flags=re.M)
    return t


def count(body, pats):
    n, hits = 0, []
    for p in pats:
        for m in re.finditer(p, body, flags=re.M):
            n += 1
            s = max(0, m.start() - 22)
            hits.append(body[s:m.end() + 26].replace('\n', ' '))
    return n, hits


def scan(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    body = clean(raw)
    cn = len(re.findall(r'[\u4e00-\u9fff]', body))
    k = max(cn / 1000, 0.001)
    groups = {}
    for name, pats in (('元叙事', META), ('套路词', CLICHE), ('AI句腔', AISENT),
                       ('翻案腔', FANAN), ('冒号', COLON), ('起手式', OPEN)):
        n, hits = count(body, pats)
        groups[name] = (n, hits)
    zero = 0
    para = [p for p in re.split(r'\n\s*\n', body) if p.strip()]
    for p in para[1:]:
        if any(re.match(z, p.strip()) for z in ZERO):
            zero += 1
    groups['零主语'] = (zero, [])
    style = {
        '破折号': len(re.findall(r'(?<!—)—{2}(?!—)', raw)),
        '加粗': len(re.findall(r'\*\*', raw)) // 2,
        '表格': len(re.findall(r'^\|', raw, flags=re.M)),
    }
    score = sum(v[0] for kk, v in groups.items() if kk not in ('AI句腔',)) + groups['AI句腔'][0] * 2
    return {'file': os.path.basename(path), 'cn': cn, 'k': k, 'groups': groups,
            'style': style, 'score': score}


rows = []
targets = []
for a in (sys.argv[1:] or DEFAULT):
    p = a if os.path.isabs(a) else os.path.join(PUB, a)
    if os.path.isdir(p):
        targets += sorted(glob.glob(os.path.join(p, '*.md')))
    elif os.path.exists(p):
        targets.append(p)
    else:
        print(f'[缺失] {os.path.basename(p)}')

for p in targets:
    rows.append(scan(p))

rows.sort(key=lambda r: -r['score'])
print(f'{"文稿":<50}{"千字":>6}{"元叙":>5}{"套路":>5}{"句腔":>5}{"翻案":>5}{"冒号":>5}{"起手":>5}{"零主":>5}{"分":>5}')
for r in rows:
    g = r['groups']
    print(f'{r["file"][:48]:<50}{r["k"]:>6.1f}{g["元叙事"][0]:>5}{g["套路词"][0]:>5}{g["AI句腔"][0]:>5}'
          f'{g["翻案腔"][0]:>5}{g["冒号"][0]:>5}{g["起手式"][0]:>5}{g["零主语"][0]:>5}{r["score"]:>5}')

print('\n==== 命中详情（按分数排序，每类最多 6 例）====')
for r in rows:
    print(f'\n########## {r["file"]}  ({r["k"]:.1f} 千字, 分 {r["score"]}) ##########')
    print(f'  排版（本人风格，不改）：破折号 {r["style"]["破折号"]} · 加粗 {r["style"]["加粗"]} · 表格行 {r["style"]["表格"]}')
    for name in ('元叙事', '套路词', 'AI句腔', '翻案腔', '冒号', '起手式'):
        n, hits = r['groups'][name]
        if n:
            print(f'  【{name}】{n} 处')
            for h in hits[:6]:
                print(f'      · {h}')
    if r['groups']['零主语'][0]:
        print(f'  【零主语】{r["groups"]["零主语"][0]} 处')
