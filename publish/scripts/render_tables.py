# -*- coding: utf-8 -*-
"""
Markdown 表格 → PNG（虎扑发布用）

虎扑编辑器原生不支持表格，正文表格渲染为图片上传。
用法：
    python publish/scripts/render_tables.py 篇1-3400公里之后谁还在-环塔架构重量与动力边界.md

输出：publish/nga/tables/<篇名前缀>-t<N>.png（按文章出现顺序编号）
"""

import re
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r'D:\Project\dsh_rally_cars'
OUT_ROOT = os.path.join(ROOT, 'publish', 'nga', 'tables')


def cell_text(s):
    """清理单元格内 md 语法与缺字形符号"""
    s = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    s = re.sub(r'\*\*', '', s)
    s = re.sub(r'`', '', s)
    # 微软雅黑缺字形的符号 → 文字
    s = s.replace('✅', '有').replace('⚠️', '部分')
    return s.strip()


def char_width(s):
    """估算文本显示宽度：中文/全角=1，ASCII=0.55"""
    w = 0.0
    for ch in s:
        w += 1.0 if ord(ch) > 0x2E80 else 0.55
    return w


def parse_tables(text):
    tables = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('|') and not lines[i].strip().startswith('||'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = lines[i].strip().strip('|')
                cells = [cell_text(c) for c in row.split('|')]
                rows.append(cells)
                i += 1
            # 去掉分隔行（形如 --- | ---）
            data = [r for r in rows if not all(re.match(r'^:?-{2,}:?$', c) for c in r if c != '')]
            if data and len(data) >= 2:
                tables.append(data)
        else:
            i += 1
    return tables


def render_table(rows, out_path):
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    # 补齐列数
    rows = [r + [''] * (n_cols - len(r)) for r in rows]

    # 列宽（每列取最长内容，上限 24 字符宽）
    col_w = []
    for c in range(n_cols):
        m = max(char_width(r[c]) for r in rows)
        col_w.append(min(m, 24))
    total_w = sum(col_w)
    max_w = 11.0  # 英寸上限
    scale = min(1.0, max_w / max(total_w, 1))

    fig, ax = plt.subplots(figsize=(total_w * scale + 0.5, n_rows * 0.42 + 0.8))
    ax.axis('off')

    table = ax.table(
        cellText=rows,
        colWidths=[w / total_w for w in col_w],
        cellLoc='left',
        loc='center',
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.5)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor('#999999')
        cell.set_linewidth(0.5)
        cell.PAD = 0.06
        if r == 0:
            cell.set_facecolor('#eeeeee')
            cell.get_text().set_fontweight('bold')
        cell.get_text().set_wrap(True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return len(rows)


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/render_tables.py <篇*.md>')
        sys.exit(1)
    os.makedirs(OUT_ROOT, exist_ok=True)
    for f in sys.argv[1:]:
        src = f if os.path.isabs(f) else os.path.join(ROOT, 'publish', f)
        if not os.path.isfile(src):
            print(f'[跳过] 不存在: {src}')
            continue
        with open(src, encoding='utf-8') as fh:
            text = fh.read()
        tables = parse_tables(text)
        base = os.path.basename(src)
        prefix = re.match(r'(篇\d+s?)', base).group(1)
        for idx, rows in enumerate(tables, 1):
            out = os.path.join(OUT_ROOT, f'{prefix}-t{idx}.png')
            n = render_table(rows, out)
            print(f'[表{idx}] {out} ({n} 行)')
        print(f'{base}: 共 {len(tables)} 张表格')


if __name__ == '__main__':
    main()
