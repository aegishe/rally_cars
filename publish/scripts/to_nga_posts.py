# -*- coding: utf-8 -*-
"""
Markdown → NGA 分楼发布版

NGA 长帖发布惯例：主楼 = 引言 + 声明 + 目录；正文各章从 1 楼起分楼发布。

用法：
    python publish/scripts/to_nga_posts.py 篇1-3400公里之后谁还在-环塔架构重量与动力边界.md

输出：publish/nga/posts/<篇名>/
    0-主楼.txt            （标题 + 引言 + 目录 + 边界声明 + 系列导航）
    1-<章节名>.txt ...    （每章一楼）
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from to_nga import inline_to_bbcode, convert  # 复用行内转换与块转换

ROOT = r'D:\Project\dsh_rally_cars'
SRC_DIR = os.path.join(ROOT, 'publish')
OUT_ROOT = os.path.join(ROOT, 'publish', 'nga', 'posts')

# 系列发布顺序（篇名前缀 → 标题），用于主楼系列导航
SERIES_ORDER = [
    ('篇1-',  '3400 公里之后，谁还在？——从 2026 环塔看越野车的架构、重量与动力边界'),
    ('篇1s-', '悬架选型铁三角：规则 × 场景强度 × 故障容忍度'),
    ('篇2-',  '2977 马力的真相：纽北圈速回归与 U9X 功率反推'),
    ('篇2s-', '同一套 1548 马力，两个重量：SU7 与 U9X 的纽北全圈账本'),
    ('篇3-',  '爬坡的两副面孔：沙地陡坡与派克峰'),
    ('篇5-',  '如果我来造一台终极越野车：从纯增程到功率分流的纸上推演'),
    ('篇6-',  '买车之前，先问自己五个问题：家用选车的需求自知'),
    ('篇4-',  '不存在一种架构统治所有场景（收官）'),
]

# 首发帖链接（发帖后回填，空=输出占位提示）
SERIES_HOME_URL = ''


def parse_md(text):
    """解析 md：标题 / 引言 / 章节列表（名称+内容）/ 系列导航"""
    lines = text.split('\n')
    title = None
    intro = []
    chapters = []  # [(标题, 内容文本)]
    nav = None

    i = 0
    # 标题（首个 # 行）
    while i < len(lines):
        m = re.match(r'^#\s+(.*)$', lines[i])
        if m:
            title = m.group(1).strip()
            i += 1
            break
        i += 1
    # 引言（连续 > 行，跳过空行）
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('>'):
            intro.append(line.lstrip('>').strip())
            i += 1
        elif line == '':
            i += 1  # 跳过空行，继续寻找 >
        else:
            break

    # 章节（^## 切分）
    cur_title = None
    cur_lines = []
    for j in range(i, len(lines)):
        m = re.match(r'^##\s+(.*)$', lines[j])
        if m:
            if cur_title is not None:
                chapters.append((cur_title, '\n'.join(cur_lines)))
            cur_title = m.group(1).strip()
            cur_lines = []
        else:
            cur_lines.append(lines[j])
    if cur_title is not None:
        chapters.append((cur_title, '\n'.join(cur_lines)))

    # 系列导航（文末 *...* 行，从最后章节内容里抽出来）
    last_title, last_content = chapters[-1]
    nav_match = re.search(r'(\*系列导航.*?\*)\s*$', last_content, re.S)
    if nav_match:
        nav = nav_match.group(1).strip()
        last_content = last_content[:nav_match.start()].rstrip()
        chapters[-1] = (last_title, last_content)

    return title, intro, chapters, nav


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/to_nga_posts.py <篇*.md>')
        sys.exit(1)

    f = sys.argv[1]
    src = f if os.path.isabs(f) else os.path.join(SRC_DIR, f)
    with open(src, encoding='utf-8') as fh:
        text = fh.read()

    title, intro, chapters, nav = parse_md(text)
    base = os.path.splitext(os.path.basename(src))[0]
    out_dir = os.path.join(OUT_ROOT, base)
    os.makedirs(out_dir, exist_ok=True)

    # 每篇专属引言（publish/nga/intros/<篇名前缀>-intro.txt，用户手写，若存在则置于标题之前）
    intro_text = ''
    prefix = next((p for p, _ in SERIES_ORDER if base.startswith(p)), base[:3])
    intro_file = os.path.join(os.path.dirname(OUT_ROOT), 'intros', prefix.rstrip('-') + '-intro.txt')
    if os.path.exists(intro_file):
        with open(intro_file, encoding='utf-8') as pf:
            intro_text = pf.read().rstrip()

    decl_chapters = [c for c in chapters if '边界声明' in c[0]]
    body_chapters = [c for c in chapters if '边界声明' not in c[0]]

    def head_block():
        """标题 + 目录（引言与边界声明不进主楼，归入正文首末楼）"""
        lines = [f'[size=150%][b]{inline_to_bbcode(title)}[/b][/size]', '']
        lines.append('[quote][b]目录[/b]')
        for idx, (ch_title, _) in enumerate(body_chapters, 1):
            lines.append(f'{idx}. {inline_to_bbcode(ch_title)}')
        lines.append('[/quote]')
        lines.append('')
        return lines

    def intro_block():
        """引言块（数据源+系列定位，并入正文第 1 楼开头）"""
        if not intro:
            return []
        return ['[quote]' + '\n'.join(inline_to_bbcode(x) for x in intro) + '[/quote]', '']

    def decl_block():
        """边界声明块（并入正文最后一楼末尾）"""
        lines = []
        for ch_title, ch_content in decl_chapters:
            ch_content = '\n'.join(x for x in ch_content.split('\n') if x.strip() != '---')
            lines.append('[quote][b]边界声明[/b]')
            lines.append(convert(ch_content))
            lines.append('[/quote]')
            lines.append('')
        return lines

    def series_nav_block():
        """系列导航区：回总帖（篇0）+ 上一篇 + 下一篇（链接发布后回填）"""
        lines = ['[quote][b]系列导航[/b]']
        home = f'[url={SERIES_HOME_URL}]{SERIES_HOME_URL}[/url]' if SERIES_HOME_URL else '（链接后补）'
        lines.append(f'系列总帖（前言/声明/全部文章目录）：{home}')
        idx = next((i for i, (p, _) in enumerate(SERIES_ORDER) if base.startswith(p)), -1)
        if idx > 0:
            lines.append(f'上一篇：《{SERIES_ORDER[idx-1][1]}》（链接后补）')
        if 0 <= idx < len(SERIES_ORDER) - 1:
            lines.append(f'下一篇：《{SERIES_ORDER[idx+1][1]}》（链接后补）')
        lines.append('[/quote]')
        lines.append('')
        return lines

    # ===== 主楼（分楼版）：[篇X前言] + 标题 + 目录 + 系列导航 =====
    main_lines = []
    if intro_text:
        main_lines.append(intro_text)
        main_lines.append('')
        main_lines.append('')
    main_lines += head_block()
    main_lines += series_nav_block()
    main_text = '\n'.join(main_lines)

    out_main = os.path.join(out_dir, '0-主楼.txt')
    with open(out_main, 'w', encoding='utf-8') as fh:
        fh.write(main_text)
    print(f'[主楼] {out_main} ({len(chapters)} 章)')

    # ===== 单文件完整版（nga.txt）：[篇X前言] + 标题 + 目录 + 引言 + 正文 + 边界声明 + 原文导航 + 系列导航 =====
    single_lines = []
    if intro_text:
        single_lines.append(intro_text)
        single_lines.append('')
        single_lines.append('')
    single_lines += head_block()
    single_lines += intro_block()
    for ch_title, ch_content in body_chapters:
        single_lines.append(convert(f'## {ch_title}\n' + ch_content))
        single_lines.append('')
    single_lines += decl_block()
    if nav:
        single_lines.append(inline_to_bbcode(nav))
        single_lines.append('')
    single_lines += series_nav_block()
    single_text = '\n'.join(single_lines)

    single_path = os.path.join(os.path.dirname(OUT_ROOT), base + '-nga.txt')
    with open(single_path, 'w', encoding='utf-8') as fh:
        fh.write(single_text)
    print(f'[完整版] {single_path} ({len(single_text)} 字符)')

    # 正文各章（引言并入第 1 楼开头，边界声明并入最后一楼末尾）
    for idx, (ch_title, ch_content) in enumerate(body_chapters, 1):
        safe = re.sub(r'[^\w\u4e00-\u9fff-]', '', ch_title)[:20]
        out_ch = os.path.join(out_dir, f'{idx}-{safe}.txt')
        parts = []
        if idx == 1:
            parts += intro_block()
        parts.append(convert(f'## {ch_title}\n' + ch_content))
        if idx == len(body_chapters):
            parts += decl_block()
        ch_bb = '\n'.join(parts)
        with open(out_ch, 'w', encoding='utf-8') as fh:
            fh.write(ch_bb)
        print(f'[{idx}楼] {out_ch} ({len(ch_bb)} 字符)')

    # 边界声明若是唯一末尾章（无正文）也输出（备用）
    for ch_title, ch_content in decl_chapters:
        if not body_chapters:
            break
    print('完成')


if __name__ == '__main__':
    main()
