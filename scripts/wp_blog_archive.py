# -*- coding: utf-8 -*-
"""抓取 aegishe.wordpress.com 全部文章，生成可读存档 + 日期可靠性分析。

用法：
  python wp_blog_archive.py fetch    抓取并保存 raw-posts.json
  python wp_blog_archive.py build    由 raw 生成 by-year/*.md 与 index.md
  python wp_blog_archive.py analyze  日期可靠性分析
"""
import json, os, re, sys, io, html, time, urllib.request
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SITE = 'aegishe.wordpress.com'
BASE = f'https://public-api.wordpress.com/rest/v1.1/sites/{SITE}/posts/'
FIELDS = 'ID,date,modified,title,URL,content,categories,tags'
OUT = r'D:\Project\dsh_chat\knowledge\My\2007-2011-blog'
RAW = os.path.join(OUT, 'raw-posts.json')


def fetch(page, number=100):
    url = f'{BASE}?number={number}&page={page}&fields={FIELDS}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode('utf-8'))


def cmd_fetch():
    os.makedirs(OUT, exist_ok=True)
    posts, page, found = [], 1, None
    while True:
        d = fetch(page)
        found = d.get('found')
        batch = d.get('posts', [])
        if not batch:
            break
        posts += batch
        print(f'page {page}: +{len(batch)}  total {len(posts)}/{found}')
        if found and len(posts) >= found:
            break
        page += 1
        time.sleep(0.6)
    json.dump(posts, open(RAW, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\nsaved {len(posts)} posts -> {RAW}')


def to_text(h):
    h = re.sub(r'<br\s*/?>', '\n', h or '')
    h = re.sub(r'</p\s*>', '\n\n', h)
    h = re.sub(r'<blockquote[^>]*>', '\n> ', h)
    h = re.sub(r'<li[^>]*>', '\n- ', h)
    h = re.sub(r'<[^>]+>', '', h)
    h = html.unescape(h)
    h = re.sub(r'[ \t]+\n', '\n', h)
    h = re.sub(r'\n{3,}', '\n\n', h)
    return h.strip()


def load():
    return json.load(open(RAW, encoding='utf-8'))


def cmd_build():
    posts = load()
    posts.sort(key=lambda p: p.get('date') or '', reverse=True)
    byyear = defaultdict(list)
    for p in posts:
        y = (p.get('date') or '?')[:4]
        byyear[y].append(p)
    os.makedirs(os.path.join(OUT, 'by-year'), exist_ok=True)
    total_cn = 0
    for y in sorted(byyear, reverse=True):
        lines = [f'# {y} 年（{len(byyear[y])} 篇）', '',
                 '> 存档自 aegishe.wordpress.com。**日期为 WordPress 标注值，未经校准**——'
                 '早期文章来自 Windows Live Spaces 迁移，时间戳可能被更新，详见 `../index.md` 的日期分析。', '']
        for p in byyear[y]:
            body = to_text(p.get('content') or '')
            cn = len(re.findall(r'[\u4e00-\u9fff]', body))
            total_cn += cn
            cats = p.get('categories') or {}
            tags = p.get('tags') or {}
            lines += [f'## {html.unescape(p.get("title") or "(无标题)")}', '',
                      f'- 日期：{p.get("date","")[:10]}　修订：{(p.get("modified") or "")[:10]}　ID：{p.get("ID")}　中文字数：{cn}',
                      f'- 分类：{"、".join(cats.keys()) if cats else "—"}　标签：{"、".join(tags.keys()) if tags else "—"}',
                      f'- 原文：{p.get("URL","")}', '', body, '', '---', '']
        open(os.path.join(OUT, 'by-year', f'{y}.md'), 'w', encoding='utf-8').write('\n'.join(lines))
        print(f'{y}.md  {len(byyear[y])} 篇')
    print(f'\n合计中文 {total_cn} 字')


def cmd_analyze():
    posts = load()
    posts.sort(key=lambda p: p.get('ID') or 0)
    print('=== ID 与日期关系（按 ID 升序，抽样）===')
    prev = None
    jumps = []
    for p in posts:
        d = (p.get('date') or '')[:10]
        if prev and d > prev:
            jumps.append((p.get('ID'), prev, d, html.unescape(p.get('title') or '')))
        prev = d
    print(f'总 {len(posts)} 篇；ID 升序中日期上升（时间倒挂）的点 {len(jumps)} 处')
    for j in jumps[:12]:
        print(f'  ID={j[0]}  {j[1]} -> {j[2]}  {j[3][:34]}')
    print('\n=== 按年分布 ===')
    byyear = defaultdict(int)
    for p in posts:
        byyear[(p.get('date') or '?')[:4]] += 1
    for y in sorted(byyear):
        print(f'  {y}: {byyear[y]:>4} 篇  {"█"*min(byyear[y]//3,60)}')
    print('\n=== 修订日期 vs 发布日期的差异 ===')
    same = diff = 0
    big = []
    for p in posts:
        a, b = (p.get('date') or '')[:10], (p.get('modified') or '')[:10]
        if a == b:
            same += 1
        else:
            diff += 1
            big.append((a, b, (p.get('ID'))))
    print(f'  相同 {same} 篇，不同 {diff} 篇')
    for a, b, i in sorted(big)[:8]:
        print(f'    {a} -> 修订 {b}  (ID={i})')
    print('\n=== 同一天发布多篇的情况 ===')
    byday = defaultdict(list)
    for p in posts:
        byday[(p.get('date') or '')[:10]].append(p.get('ID'))
    multi = {k: v for k, v in byday.items() if len(v) > 1}
    print(f'  有 {len(multi)} 天发布了 2 篇以上')
    for k in sorted(multi, reverse=True)[:8]:
        print(f'    {k}: {len(multi[k])} 篇  IDs={multi[k]}')


if __name__ == '__main__':
    a = sys.argv[1:] or ['fetch']
    {'fetch': cmd_fetch, 'build': cmd_build, 'analyze': cmd_analyze}[a[0]]()
