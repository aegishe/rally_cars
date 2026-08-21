# -*- coding: utf-8 -*-
"""
虎扑分段发布版生成器

虎扑单帖限制 1 万字：按章节自动切分，每段生成独立 HTML（粘贴源）。
段 1 = 篇X前言 + 标题 + 引言 + 若干章（+ 目录占位）
末段末尾 = 边界声明 + 原文导航 + 系列导航
表格一律占位提示（上传 render_tables.py 生成的 PNG）。

用法：
    python publish/scripts/to_hupu.py 篇1-3400公里之后谁还在-环塔架构重量与动力边界.md
    python publish/scripts/to_hupu.py 篇*.md

输出：publish/nga/hupu/<篇名>-1.html、-2.html ...
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import to_nga
import to_nga_posts as tnp
import to_html as th

ROOT = r'D:\Project\dsh_rally_cars'
OUT_DIR = os.path.join(ROOT, 'publish', 'nga', 'hupu')
LIMIT = 9000  # 单段可见字符上限（1 万字限制留 10% 余量）


def visible_len(bbcode):
    """剥离标签后的可见字符数"""
    s = re.sub(r'\[[^\]]+\]', '', bbcode)
    s = s.replace('\u200b', '')
    return len(s)


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/to_hupu.py <篇*.md>')
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    for f in sys.argv[1:]:
        src = f if os.path.isabs(f) else os.path.join(ROOT, 'publish', f)
        if not os.path.isfile(src):
            print(f'[跳过] 不存在: {src}')
            continue
        with open(src, encoding='utf-8') as fh:
            text = fh.read()

        title, intro, chapters, nav = tnp.parse_md(text)
        base = os.path.splitext(os.path.basename(src))[0]
        prefix = re.match(r'(篇\d+s?)', base).group(1)

        decl = [c for c in chapters if '边界声明' in c[0]]
        body = [c for c in chapters if '边界声明' not in c[0]]

        # 篇X专属引言
        intro_text = ''
        intro_file = os.path.join(ROOT, 'publish', 'nga', 'intros', prefix + '-intro.txt')
        if os.path.exists(intro_file):
            with open(intro_file, encoding='utf-8') as pf:
                intro_text = pf.read().rstrip()

        # 头部块（标题 + 数据源引言）
        head_bb = f'[size=150%][b]{tnp.inline_to_bbcode(title)}[/b][/size]\n\n'
        if intro:
            head_bb += '[quote]' + '\n'.join(tnp.inline_to_bbcode(x) for x in intro) + '[/quote]\n\n'

        # 声明与导航块
        tail_bb = ''
        for ch_title, ch_content in decl:
            ch_content = '\n'.join(x for x in ch_content.split('\n') if x.strip() != '---')
            tail_bb += '[quote][b]边界声明[/b]\n' + to_nga.convert(ch_content) + '[/quote]\n\n'
        if nav:
            tail_bb += tnp.inline_to_bbcode(nav) + '\n\n'

        # 按可见字符数切分章节
        seg_heads = [head_bb]  # 每段开头内容
        segs = [[]]            # 每段章节 BBCode 列表
        seg_len = [visible_len(head_bb)]
        for ch_title, ch_content in body:
            ch_bb = to_nga.convert(f'## {ch_title}\n' + ch_content)
            l = visible_len(ch_bb)
            if segs[-1] and seg_len[-1] + l > LIMIT:
                seg_heads.append('')
                segs.append([])
                seg_len.append(0)
            segs[-1].append(ch_bb)
            seg_len[-1] += l

        # 输出各段 HTML
        n = len(segs)
        for i in range(n):
            seg_bb = ''
            if i == 0 and intro_text:
                seg_bb += intro_text + '\n\n'
            seg_bb += seg_heads[i]
            seg_bb += '\n\n'.join(segs[i]) + '\n\n'
            if i == n - 1:
                seg_bb += tail_bb
            th.PREFIX = prefix
            th.TABLE_COUNTER = [1]
            html = th.wrap_html(th.bbcode_to_html(seg_bb), f'{base} 段{i+1}')
            out = os.path.join(OUT_DIR, f'{base}-{i+1}.html')
            with open(out, 'w', encoding='utf-8') as fh:
                fh.write(html)
            print(f'[段{i+1}/{n}] {out} (可见约 {seg_len[i]} 字)')

        print(f'{base}: {len(body)} 章 → {n} 段')


if __name__ == '__main__':
    main()
