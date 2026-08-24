# -*- coding: utf-8 -*-
"""
NGA BBCode → HTML 预览器

用途：把 publish/nga/篇X-...-nga.txt 转成浏览器可直接打开的 HTML，
完整保留 NGA 样式（b/i/s/color/size/table/list/quote/url/img/code），
尤其渲染 [color=red]（更新）[/color] 这种红标。

红标约定（已发布文章增量更新规范）：
- 已发布到 NGA 的文章，后续"重要更新"（新增段落/结论/关键修正）用 [color=red]（更新）…[/color] 包裹；
- 新增整段：整段包进 [color=red]（更新）…[/color]；仅改词：只包改动的词；
- 纯数字/措辞修正（改原有内容、非新增）不标红，直接改文本；
- 改完跑本脚本重新生成 HTML，核对红标处数与预期一致。

用法：
    python publish/scripts/preview_nga.py publish/nga/篇1-3400公里之后谁还在-环塔架构重量与动力边界-nga.txt
    python publish/scripts/preview_nga.py publish/nga/*-nga.txt   # 批量

输出：与输入同名的 .html 文件，双击在浏览器打开即可预览。
"""

import re
import sys
import os
import glob


def bbcode_to_html(text):
    s = text
    # 1. 转义 HTML 特殊字符（BBCode 用 []，不受影响）
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # 2. 链接 [url=...]text[/url]
    s = re.sub(r'\[url=([^\]]+)\](.*?)\[/url\]', r'<a href="\1">\2</a>', s, flags=re.S)

    # 3. 图片 [img]path[/img]
    s = re.sub(r'\[img\]([^\[\]]+)\[/img\]',
               r'<img src="\1" style="max-width:100%">', s)

    # 4. 代码块 [code]...[/code]
    s = re.sub(r'\[code\](.*?)\[/code\]',
               r'<pre style="background:#f6f6f6;padding:10px;overflow-x:auto">\1</pre>', s, flags=re.S)

    # 5. 折叠 [collapse]...[/collapse]
    s = re.sub(r'\[collapse(?:=[^\]]*)?\](.*?)\[/collapse\]',
               r'<details><summary>展开</summary>\1</details>', s, flags=re.S)

    # 6. 引用 [quote]...[/quote]（可能嵌套，循环处理，先内后外）
    for _ in range(6):
        s = re.sub(
            r'\[quote\](.*?)\[/quote\]',
            r'<blockquote style="margin:8px 0;padding:6px 12px;border-left:3px solid #ccc;background:#f7f7f7;color:#555">\1</blockquote>',
            s, flags=re.S)

    # 7. 表格 [table]...[tr][td]...
    def table_repl(m):
        inner = m.group(1)
        # tr 行
        inner = re.sub(r'\[tr\](.*?)\[/tr\]', r'<tr>\1</tr>', inner, flags=re.S)
        # td 单元格
        inner = re.sub(r'\[td\](.*?)\[/td\]', r'<td>\1</td>', inner, flags=re.S)
        return ('<table border="1" cellspacing="0" cellpadding="6" '
                'style="border-collapse:collapse;margin:8px 0;font-size:14px">'
                + inner + '</table>')
    s = re.sub(r'\[table\](.*?)\[/table\]', table_repl, s, flags=re.S)

    # 8. 有序列表 [list=1][*]...
    def ol_repl(m):
        items = re.findall(r'\[\*\](.*?)(?=\[\*\]|\[/list\])', m.group(1), re.S)
        return '<ol>' + ''.join(f'<li>{it.strip()}</li>' for it in items) + '</ol>'
    s = re.sub(r'\[list=1\](.*?)\[/list\]', ol_repl, s, flags=re.S)

    # 9. 无序列表 [list][*]...
    def ul_repl(m):
        items = re.findall(r'\[\*\](.*?)(?=\[\*\]|\[/list\])', m.group(1), re.S)
        return '<ul>' + ''.join(f'<li>{it.strip()}</li>' for it in items) + '</ul>'
    s = re.sub(r'\[list\](.*?)\[/list\]', ul_repl, s, flags=re.S)

    # 10. 章节标题 [size=130%][b]...[/b][/size]（组合）
    s = re.sub(r'\[size=(\d+)%\]\[b\](.*?)\[/b\]\[/size\]',
               r'<span style="font-size:\1%"><b>\2</b></span>', s, flags=re.S)

    # 11. 行内：size / color / font / b / i / s
    s = re.sub(r'\[size=(\d+)%\](.*?)\[/size\]',
               r'<span style="font-size:\1%">\2</span>', s, flags=re.S)
    s = re.sub(r'\[color=([^\]]+)\](.*?)\[/color\]',
               r'<span style="color:\1">\2</span>', s, flags=re.S)
    s = re.sub(r'\[font=([^\]]+)\](.*?)\[/font\]',
               r'<span style="font-family:\1">\2</span>', s, flags=re.S)
    s = re.sub(r'\[b\](.*?)\[/b\]', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'\[i\](.*?)\[/i\]', r'<i>\1</i>', s, flags=re.S)
    s = re.sub(r'\[s\](.*?)\[/s\]', r'<s>\1</s>', s, flags=re.S)

    # 12. 换行：\n → <br>（块级标签后的换行清理）
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = s.replace('\n', '<br>')
    # 块级元素后的多余 <br> 清理
    for tag in ('table', 'ul', 'ol', 'blockquote', 'pre', 'details', 'li', 'tr'):
        s = re.sub(rf'</{tag}>\s*<br>', rf'</{tag}>', s)
        s = re.sub(rf'<br>\s*<{tag}', rf'<{tag}', s)
    s = re.sub(r'(<br>\s*){3,}', '<br><br>', s)
    return s


def wrap_html(body, title):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; max-width: 860px; margin: 24px auto; padding: 0 16px; line-height: 1.8; color: #222; }}
a {{ color: #3b6ea3; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
h1,h2,h3 {{ line-height: 1.4; }}
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
{body}
</body>
</html>
'''


def main():
    if len(sys.argv) < 2:
        print('用法: python publish/scripts/preview_nga.py <nga.txt ...>')
        sys.exit(1)

    files = []
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            files.append(arg)
        else:
            files.extend(sorted(glob.glob(arg)))

    for f in files:
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        body = bbcode_to_html(text)
        html = wrap_html(body, os.path.basename(f))
        out = os.path.splitext(f)[0] + '.html'
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(html)
        print(f'[完成] {f} -> {out}')


if __name__ == '__main__':
    main()
