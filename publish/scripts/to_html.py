# -*- coding: utf-8 -*-
"""
NGA BBCode → 虎扑粘贴用 HTML（降级版）

虎扑服务端只保留白名单标签（文本/br/a/img 手动上传），粘贴的 b/blockquote/font-size/table
全部被剥。本脚本按虎扑白名单降级：
- 加粗 [b] → 「」强调
- 章节标题（size+b）→ 段前 ━━━━ 分隔线 + 纯文字
- 引用 [quote] → 每行 ▍ 前缀
- 列表 → · / 1. 文字前缀
- 图片 [img] → 红色占位提示（虎扑编辑器手动上传）
- 表格 → 红色占位提示（上传 render_tables.py 生成的 PNG）
- 链接 <a> 保留

用法：
    python publish/scripts/to_html.py publish/nga/篇X-...-nga.txt
    python publish/scripts/to_hupu.py 篇X.md      # 分段版，内部调用本模块
"""

import re
import sys
import os

TABLE_COUNTER = [1]
PREFIX = ''


def bbcode_to_html(text):
    s = text

    # 章节标题（size+b 组合）：段前分隔线 + 纯文字
    s = re.sub(r'\[size=(\d+)%\]\[b\](.*?)\[/b\]\[/size\]',
               lambda m: '━━━━━━━━━━━━\n' + m.group(2), s, flags=re.S)
    # 其余 size 标签 → 纯文字
    s = re.sub(r'\[size=\d+%\](.*?)\[/size\]', r'\1', s, flags=re.S)

    # 加粗 → 「」
    s = re.sub(r'\[b\](.*?)\[/b\]', r'「\1」', s, flags=re.S)

    # 斜体 / 删除线 / 等宽 → 纯文字
    s = re.sub(r'\[i\](.*?)\[/i\]', r'\1', s, flags=re.S)
    s = re.sub(r'\[s\](.*?)\[/s\]', r'\1', s, flags=re.S)
    s = re.sub(r'\[font=monospace\](.*?)\[/font\]', r'\1', s, flags=re.S)

    # 链接（虎扑保留 a）
    s = re.sub(r'\[url=([^\]]+)\](.*?)\[/url\]', r'<a href="\1">\2</a>', s, flags=re.S)

    # 图片 → 占位提示（虎扑手动上传）
    def img_repl(m):
        return f'<p style="color:#c00">〔此处上传图片：{m.group(1)}〕</p>'
    s = re.sub(r'\[img\]([^\[]+)\[/img\]', img_repl, s)

    # 引用 → 每行 ▍ 前缀（嵌套 quote 逐层处理）
    def quote_repl(m):
        content = m.group(1).strip('\n')
        lines = ['▍ ' + ln if ln.strip() else '' for ln in content.split('\n')]
        return '\n'.join(lines)
    for _ in range(3):
        s = re.sub(r'\[quote\](.*?)\[/quote\]', quote_repl, s, flags=re.S)

    # 表格 → 占位提示
    def table_repl(m):
        idx = TABLE_COUNTER[0]
        TABLE_COUNTER[0] += 1
        return (f'<p style="color:#c00">〔表格 {idx}：此处上传表格截图，'
                f'文件 publish/nga/tables/{PREFIX}-t{idx}.png〕</p>')
    s = re.sub(r'\[table\].*?\[/table\]', table_repl, s, flags=re.S)

    # 有序列表
    def ol_repl(m):
        items = re.findall(r'\[\*\](.*?)(?=\[\*\]|$)', m.group(1), re.S)
        out = []
        for n, it in enumerate(items, 1):
            out.append(f'{n}. ' + it.strip())
        return '\n'.join(out)
    s = re.sub(r'\[list=1\](.*?)\[/list\]', ol_repl, s, flags=re.S)

    # 无序列表
    def ul_repl(m):
        items = re.findall(r'\[\*\](.*?)(?=\[\*\]|$)', m.group(1), re.S)
        return '\n'.join('· ' + it.strip() for it in items)
    s = re.sub(r'\[list\](.*?)\[/list\]', ul_repl, s, flags=re.S)

    # 代码块 → 纯文本
    s = re.sub(r'\[code\](.*?)\[/code\]', r'\1', s, flags=re.S)

    # 换行：显式 <br>，块边界清理
    s = s.replace('\r\n', '\n')
    s = s.replace('\n', '<br>')
    s = re.sub(r'<br>\s*(<p|<a|<br)', r'\1', s)
    s = re.sub(r'</(p|a)>\s*<br>', r'</\1>', s)
    s = re.sub(r'(<br>\s*){3,}', '<br><br>', s)
    return s


def wrap_html(body, title):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; max-width: 860px; margin: 24px auto; padding: 0 16px; line-height: 1.8; color: #222; }}
a {{ color: #3b6ea3; }}
</style>
</head>
<body>
{body}
</body>
</html>
'''


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/to_html.py <bbcode文件> [更多文件...]')
        sys.exit(1)
    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            print(f'[跳过] 不存在: {f}')
            continue
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        global PREFIX, TABLE_COUNTER
        m = re.search(r'(篇\d+s?)', os.path.basename(f))
        PREFIX = m.group(1) if m else '篇'
        TABLE_COUNTER = [1]
        body = bbcode_to_html(text)
        html = wrap_html(body, os.path.basename(f))
        out = os.path.splitext(f)[0] + '.html'
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(html)
        print(f'[完成] {f} -> {out}')


if __name__ == '__main__':
    main()
