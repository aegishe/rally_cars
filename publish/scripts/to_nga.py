# -*- coding: utf-8 -*-
"""
Markdown → NGA BBCode 发布转换器

用途：把 publish/篇*.md 转成 NGA 车版可直接粘贴的 BBCode 文本。
NGA 格式：BBCode（[b][/b]、[table][tr][td]、[quote]、[url]、[img]、[collapse]、[code] 等）。
虎扑：无 BBCode 手写通道，用浏览器渲染后复制粘贴富文本即可（本脚本不处理）。

用法：
    python publish/scripts/to_nga.py 篇1-3400公里之后谁还在-环塔架构重量与动力边界.md
    python publish/scripts/to_nga.py 篇*.md            # 批量

输出：publish/nga/<原名>-nga.txt

注意事项：
- 图片 ![alt](path) 转 [img]path[/img]——NGA 需要外链图床（本地 PNG 需先传图床）。
- 数学公式 $$...$$ 无 LaTeX 支持，转为 Unicode 纯文本（β、·、×、≈、下标连写）。
- 代码块 ``` 转 [code] 包裹。
"""

import re
import sys
import os
import glob

ROOT = r'D:\Project\dsh_rally_cars'
SRC_DIR = os.path.join(ROOT, 'publish')
OUT_DIR = os.path.join(ROOT, 'publish', 'nga')

# ---------- LaTeX → Unicode 纯文本 ----------
LATEX_SUBS = [
    (r'\\ln', 'ln'), (r'\\log', 'log'), (r'\\sin', 'sin'), (r'\\cos', 'cos'),
    (r'\\tan', 'tan'), (r'\\cdot', '·'), (r'\\times', '×'), (r'\\div', '÷'),
    (r'\\approx', '≈'), (r'\\pm', '±'), (r'\\le', '≤'), (r'\\ge', '≥'),
    (r'\\neq', '≠'), (r'\\propto', '∝'), (r'\\to', '→'), (r'\\rightarrow', '→'),
    (r'\\alpha', 'α'), (r'\\beta', 'β'), (r'\\gamma', 'γ'), (r'\\delta', 'δ'),
    (r'\\theta', 'θ'), (r'\\mu', 'μ'), (r'\\sigma', 'σ'), (r'\\pi', 'π'),
    (r'\\Delta', 'Δ'),
    # 下标/上标花括号先剥离（避免嵌套花括号破坏 \frac 正则）
    (r'_\{([^}]*)\}', r'_\1'),
    (r'\^\{([^}]*)\}', r'^\1'),
    (r'\\text\{([^}]*)\}', r'\1'),
    (r'\\frac\{([^}]*)\}\{([^}]*)\}', r'(\1/\2)'),
    (r'\\quad', '  '), (r'\\qquad', '    '), (r'\\;', ' '), (r'\\,', ' '), (r'\\!', ''),
    (r'\\left', ''), (r'\\right', ''),
    (r'\$\$', ''), (r'\$', ''),
    (r'\{', ''), (r'\}', ''),
    (r'\_', '_'),
]

def latex_to_text(s):
    for pat, rep in LATEX_SUBS:
        s = re.sub(pat, rep, s)
    return s

# ---------- 图床链接映射（上传后回填，key=assets 文件名，value=NGA 图床路径） ----------
IMG_URL_MAP = {
    # 篇1 越野
    'chapter1-1-soc-collapse.png': './mon_202608/21/-7da9Q54-j5wqK1lT3cSsg-h2.jpg',
    'chapter1-2-p1-generator.png': './mon_202608/21/-7da9Q68-12gjK1nT3cSsg-h2.jpg',
    'chapter1-3-scene-matrix.png': './mon_202608/21/-7da9Q54-4vq9K1eT3cSsg-if.jpg',
    # 篇1s 悬架
    'chapter1s-1-bilstein-zonecontrol-bypass.png': './mon_202608/21/-7da9Q70-6cxK1qT3cSsg-ja.jpg',
    'chapter1s-2-amg-one-suspension.jpg': './mon_202608/21/-7da9Q70-25riK22T3cSsg-fz.jpg',
    'chapter1s-3-koenigsegg-triplex.jpg': './mon_202608/21/-7da9Q70-f6ruK2jT3cSk8-8c.jpg',
    'chapter1s-4-mclaren-interconnected.jpg': './mon_202608/21/-7da9Q70-l1eqK15T1kS9n-go.jpg',
    'chapter1s-5-mason-trophy-truck.jpg': './mon_202608/21/-7da9Q70-l34qK1cT3cSsg-cr.jpg',
    # 篇2 赛道
    'chapter2-1-pw-laptime.png': './mon_202608/24/-7da9Q66-32j9K1eT3cSsg-ih.jpg',
    'chapter2-2-k-value.png': './mon_202608/24/-7da9Q66-k2kiK1qT3cSxc-ku.jpg',
    'chapter2-3-u9x-power.png': './mon_202608/24/-7da9Q66-fqx9K24T3cSsg-e8.jpg',
    'chapter2-4-residual.png': './mon_202608/24/-7da9Q66-85ksK1hT3cSsg-hd.jpg',
    # 篇2s 弯道截图对比 + 三车速度曲线
    'chapter2s-c1-kesselchen.png': './mon_202608/25/-7da9Q51-dljfK1pT3cSsg-bd.jpg',
    'chapter2s-4-speed-profiles.png': './mon_202608/25/-7da9Q51-g37dZcT3cSsg-ds.jpg',
    # 篇3 派克峰/沙坡（8 张，按正文顺序）
    'chapter3-1-g700-baiwanpo.jpg': './mon_202608/28/-7da9Q42-6u8oZcT3cSjo-n8.jpg',
    'chapter3-2-paddle-tire.jpg': './mon_202608/28/-7da9Q42-6zngZdT1kShc-jy.jpg',
    'chapter3-3-zeekr7x-moreeb.jpg': './mon_202608/28/-7da9Q42-6b0pK1vT3cSo9-hs.jpg',
    'chapter3-4-uphill-sand-race.jpg': './mon_202608/28/-7da9Q42-fscuK1qT3cSig-af.jpg',
    'chapter3-5-uphill-sand-fail.jpg': './mon_202608/28/-7da9Q42-6zb6K15T1kSa3-hs.jpg',
    'chapter3-6-pw-laptime.png': './mon_202608/28/-7da9Q42-edz7KvT3cSku-dj.jpg',
    'chapter3-7-weight-laptime.png': './mon_202608/28/-7da9Q42-4itiKzT3cSku-dj.jpg',
    'chapter3-8-cross-scene.png': './mon_202608/28/-7da9Q42-590kKrT1kSci-a0.jpg',
    # 篇4 布局、重量和其他
    'chapter4-1-denza-z-announce.jpg': './mon_202608/28/-7da9Q50-kbsuK1rT1kSbe-on.jpg',
    'chapter4-2-denza-z-special-edition-wing.jpg': './mon_202608/28/-7da9Q50-7fggK1mT1kSe8-9h.jpg',
    'chapter4-3-great-wall-v8.jpg': './mon_202608/28/-7da9Q50-k32yZaT3cSj5-ar.jpg',
    'chapter4-4-geely-lotus.jpg': './mon_202608/28/-7da9Q50-g5y7KyT1kSeg-a0.jpg',
    # 篇5 后置四驱（按正文出现顺序）
    'chapter5-1-audi-rsq-etron.jpg': './mon_202608/31/-7da9Q46-hwryZbT3cSos-dy.jpg',
    'chapter5-2-amg-one-cutaway.jpg': './mon_202608/31/-7da9Q46-a0u4K2pT3cSos-dy.jpg',
    'chapter5-3-rsq-etron-cutaway.jpg': './mon_202608/31/-7da9Q46-5irkZbT3cSqo-iv.jpg',
    'chapter5-4-993-aircooled.jpg': './mon_202608/31/-7da9Q46-gyqaK1sT1kSh8-b0.jpg',
    'chapter5-5-991-watercooled.jpg': './mon_202608/31/-7da9Q46-brzxK21T1kSh8-cx.jpg',
    'chapter5-6-959-paris-dakar.jpg': './mon_202608/31/-7da9Q46-3j85K11T3cSsg-g0.jpg',
    'chapter5-7-perfect-e-offroad-engine.jpg': './mon_202608/31/-7da9Q46-k150K1tT3cSqh-e7.jpg',
    'chapter5-8-perfect-e-offroad.jpg': './mon_202608/31/-7da9Q46-7rveK1vT3cSsg-g0.jpg',
}

# ---------- 发布强调配置 ----------
# NGA 表格表头无底色可用 → 表头行统一 [size=130%] + 加粗（所有表格生效）。
# 关键行/关键句标红（[color=red]）：发布前按篇按需增删（篇5 指定两处）。
RED_ROW_MARKERS = ['后置对调方案']          # 表格行第一格包含该词 → 整行每个单元格标红
RED_HIGHLIGHTS = ['911 用半个世纪验证过的 RR，配上 959 用达喀尔双冠验证过的后置四驱，如今以混动硬派越野车的形式出击']  # 段落内子句 → 标红

# ---------- 行内格式 ----------
def inline_to_bbcode(s):
    s = latex_to_text(s)
    # 链接 [text](url) —— 先于加粗处理，避免 ** 干扰
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'[url=\2]\1[/url]', s)
    # 图片 ![alt](path) —— 有图床映射用映射，否则原路径（提示待上传）
    def img_repl(m):
        alt = m.group(1)
        path = m.group(2)
        name = os.path.basename(path)
        url = IMG_URL_MAP.get(name, path)
        return f'[img]{url}[/img]'
    s = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', img_repl, s)
    # 加粗 **x** / __x__
    s = re.sub(r'\*\*(.+?)\*\*', r'[b]\1[/b]', s)
    s = re.sub(r'__(.+?)__', r'[b]\1[/b]', s)
    # 斜体 *x*（单个星号，避免吃掉已处理的）
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'[i]\1[/i]', s)
    # 删除线 ~~x~~
    s = re.sub(r'~~(.+?)~~', r'[s]\1[/s]', s)
    # 行内代码 `x`
    s = re.sub(r'`([^`]+)`', r'[font=monospace]\1[/font]', s)
    # NGA 平台适配：★ 与 ● 均被论坛内容过滤吞掉（2026-08 PC 端实测），星号记法改为文字"n星"
    s = re.sub(r'★+', lambda m: f'{len(m.group())}星', s)
    s = re.sub(r'●+', lambda m: f'{len(m.group())}星', s)
    # 发布强调：关键子句标红（在加粗等转换之后，嵌套 [b][color=red]…[/color][/b]）
    for h in RED_HIGHLIGHTS:
        s = s.replace(h, f'[color=red]{h}[/color]')
    return s

# ---------- 块级转换 ----------
def convert(text):
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith('```'):
            out.append('[quote][code]')
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                out.append(lines[i].rstrip())
                i += 1
            i += 1  # 跳过结束 ```
            out.append('[/code][/quote]')
            continue

        # 表格块
        if line.strip().startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip())
                i += 1
            # 去掉分隔行（第二个元素形如 |---|---|）
            data_rows = [r for r in rows if not re.match(r'^\|[\s:|-]+\|$', r)]
            out.append('[table]')
            for ri, r in enumerate(data_rows):
                cells = [c.strip() for c in r.strip('|').split('|')]
                if ri == 0:
                    # 表头：无底色可用，130% 字号 + 加粗
                    cells = [f'[size=130%][b]{inline_to_bbcode(c)}[/b][/size]' for c in cells]
                elif any(marker in cells[0] for marker in RED_ROW_MARKERS):
                    # 关键行：整行每个单元格标红
                    cells = [f'[color=red]{inline_to_bbcode(c)}[/color]' for c in cells]
                else:
                    cells = [inline_to_bbcode(c) for c in cells]
                out.append('[tr]' + ''.join(f'[td]{c}[/td]' for c in cells) + '[/tr]')
            out.append('[/table]')
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            level = len(m.group(1))
            content = inline_to_bbcode(m.group(2))
            size = {1: '150%', 2: '130%', 3: '115%'}.get(level, '110%')
            out.append(f'[size={size}][b]{content}[/b][/size]')
            i += 1
            continue

        # 引用块（连续 > 行合并）
        if line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip().lstrip('>').strip())
                i += 1
            out.append('[quote]' + '\n'.join(inline_to_bbcode(q) for q in quote_lines) + '[/quote]')
            continue

        # 无序列表（连续 - 行合并）
        if re.match(r'^\s*[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]):
                items.append('[b]*[/b] ' + inline_to_bbcode(re.sub(r'^\s*[-*]\s+', '', lines[i])))
                i += 1
            out.append('[list]' + ''.join(f'[*]{it}' for it in items) + '[/list]')
            continue

        # 有序列表（连续 N. 行合并）
        if re.match(r'^\s*\d+[.、]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+[.、]\s+', lines[i]):
                items.append(inline_to_bbcode(re.sub(r'^\s*\d+[.、]\s+', '', lines[i])))
                i += 1
            out.append('[list=1]' + ''.join(f'[*]{it}' for it in items) + '[/list]')
            continue

        # 水平线
        if line.strip() in ('---', '***', '___'):
            out.append('[quote]————————————[/quote]')
            i += 1
            continue

        # 空行
        if line.strip() == '':
            out.append('')
            i += 1
            continue

        # 普通段落
        out.append(inline_to_bbcode(line))
        i += 1

    return '\n'.join(out)

def load_header(out_path: str) -> str:
    """NGA 发布前言合并：publish/nga/_headers/<篇名>.header.txt 存在时前置拼接。
    前言是发布时手写内容（吃瓜段、红字钩子等），不属于文章 md，
    抽到 header 文件后，to_nga 重跑不再覆盖它。"""
    header_dir = os.path.join(OUT_DIR, '_headers')
    base = os.path.basename(out_path).replace('-nga.txt', '.header.txt')
    hf = os.path.join(header_dir, base)
    if os.path.isfile(hf):
        with open(hf, encoding='utf-8') as fh:
            return fh.read().rstrip('\n') + '\n\n'
    return ''


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/to_nga.py <篇*.md ...>')
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    files = []
    for arg in sys.argv[1:]:
        if os.path.sep in arg or arg.startswith(('publish', '.')):
            files.append(arg if os.path.isabs(arg) else os.path.join(ROOT, arg))
        else:
            files.extend(sorted(glob.glob(os.path.join(SRC_DIR, arg))))

    for f in files:
        if not os.path.isfile(f):
            print(f'[跳过] 不存在: {f}')
            continue
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        bb = convert(text)
        base = os.path.splitext(os.path.basename(f))[0]
        out_path = os.path.join(OUT_DIR, base + '-nga.txt')
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(load_header(out_path) + bb)
        print(f'[完成] {os.path.basename(f)} -> {out_path} ({len(bb)} 字符)')

if __name__ == '__main__':
    main()
