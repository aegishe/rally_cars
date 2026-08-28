# -*- coding: utf-8 -*-
"""
NGA 回帖抓取器

用法：
    python publish/scripts/nga_replies.py 47456620
    python publish/scripts/nga_replies.py 47412917 -o D:/tmp/xxx.txt
    python publish/scripts/nga_replies.py 47412917 --max-pages 10

反爬说明：NGA 对无 guestJs 的请求返回 403"访客不能直接访问"，
而 guestJs 的值硬编码在 403 页面的一段 JS 里（guestJs=<时间戳>_<随机串>）。
流程：先触发一次 403 → 正则提取 guestJs → 带 cookie 重试 API。
输出：按楼层排序的纯文本（UTF-8），含用户名（游客态下为匿名"?"）。

限制：
- 游客态抓取，作者用户名被 NGA 匿名化；
- 需要登录态用户名时，把浏览器 cookie 串传给 --cookie。
"""

import requests
import re
import json
import html
import argparse
import sys
import os
import time
import random

NGA_BASE = 'https://bbs.nga.cn'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
    'Referer': NGA_BASE + '/',
}


def get_guestjs(session: requests.Session, tid: str) -> str:
    """触发一次请求，从 403 页面 JS 里提取 guestJs；登录态直接 200 则返回空串"""
    r = session.get(f'{NGA_BASE}/read.php?tid={tid}', timeout=15)
    if r.status_code == 200:
        return ''  # 登录态，无需 guestJs
    t = r.content.decode('gbk', errors='ignore')
    m = re.search(r'guestJs=([\w]+)', t)
    if not m:
        raise RuntimeError(f'guestJs 提取失败（status={r.status_code}）')
    return m.group(1)


def load_cookie_file(session: requests.Session, path: str):
    """Netscape cookies.txt → session（domain 统一给 bbs.nga.cn）"""
    if not os.path.exists(path):
        raise FileNotFoundError(f'cookie 文件不存在：{path}')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7 and parts[5] and parts[6]:
                session.cookies.set(parts[5], parts[6], domain='bbs.nga.cn', path='/')


def fetch_replies(tid: str, max_pages: int = 100, cookie_str: str = '', authorid: str = ''):
    """逐页抓取回帖，返回 {楼层: 回帖dict} 和总回帖数
    authorid 非空时用 read.php 的 authorid 过滤：只抓该用户回帖，
    页数按过滤后总数走（大帖按 uid 拔取时省 95% 请求）。
    过滤模式下 lou 无效（重排为 0），楼层以 postdate/内容为准。"""
    s = requests.Session()
    s.headers.update(HEADERS)
    if cookie_str:
        for kv in cookie_str.split(';'):
            kv = kv.strip()
            if '=' in kv:
                k, v = kv.split('=', 1)
                s.cookies.set(k, v, domain='bbs.nga.cn', path='/')

    guestjs = get_guestjs(s, tid)
    if guestjs:
        s.cookies.set('guestJs', guestjs, domain='bbs.nga.cn', path='/')

    all_rows = {}
    total = None
    page = 1
    while page <= max_pages:
        url = f'{NGA_BASE}/read.php?tid={tid}&page={page}&__output=8'
        if authorid:
            url += f'&authorid={authorid}'
        r = s.get(url, timeout=20)
        if r.status_code != 200:
            print(f'[page {page}] status {r.status_code}，停止')
            break
        try:
            d = decode_nga_json(r.content)
        except json.JSONDecodeError:
            print(f'[page {page}] JSON 解析失败，停止')
            break
        data = d.get('data', {})
        rows = data.get('__R', {})
        if not rows:
            break
        per_page = data.get('__R__ROWS_PAGE') or 20  # 每页条数
        new_count = 0
        for idx, row in rows.items():
            # 楼层：row 自带 lou 用 lou（过滤模式下 lou 无效，按页内索引推算）
            lou = row.get('lou')
            if not authorid and (lou is None or str(lou).strip() == ''):
                lou = (page - 1) * int(per_page) + int(idx)
            key = lou if not authorid else (page - 1) * int(per_page) + int(idx)
            if int(key) not in all_rows:
                all_rows[int(key)] = row
                new_count += 1
        # 总数：__ROWS 才是总回帖数（__R__ROWS 是每页条数）
        total = data.get('__ROWS') or (data.get('__T') or {}).get('replies') or 0
        print(f'[page {page}] 本页 {len(rows)} 条（新增 {new_count}），累计 {len(all_rows)} / 总 {total}')
        if new_count == 0:
            break  # 重复页（超范围翻页），停止
        if total and len(all_rows) >= int(total):
            break
        page += 1
        time.sleep(random.uniform(1.5, 2.5))  # 保守节流：页间隔 1.5-2.5s 随机
    return all_rows, total


def _utf8_bad_ratio(raw: bytes) -> float:
    """统计不符合 UTF-8 结构的字节占比（GBK 老帖的中文在 UTF-8 下全是非法字节）"""
    try:
        raw.decode('utf-8')
        return 0.0
    except UnicodeDecodeError:
        pass
    bad = 0
    i, n = 0, len(raw)
    while i < n:
        b = raw[i]
        if b < 0x80:
            i += 1
        elif 0xC2 <= b < 0xE0:
            if i + 1 < n and 0x80 <= raw[i + 1] < 0xC0:
                i += 2
            else:
                bad += 1
                i += 1
        elif 0xE0 <= b < 0xF0:
            if i + 2 < n and 0x80 <= raw[i + 1] < 0xC0 and 0x80 <= raw[i + 2] < 0xC0:
                i += 3
            else:
                bad += 1
                i += 1
        elif 0xF0 <= b < 0xF5:
            if i + 3 < n and all(0x80 <= raw[i + j] < 0xC0 for j in (1, 2, 3)):
                i += 4
            else:
                bad += 1
                i += 1
        else:
            bad += 1
            i += 1
    return bad / max(n, 1)


def decode_nga_json(raw: bytes):
    """NGA JSON 编码自适应：新帖 UTF-8（偶有 GBK 残留），老帖纯 GBK"""
    if _utf8_bad_ratio(raw) > 0.02:
        return json.loads(raw.decode('gbk', errors='ignore'), strict=False)
    return json.loads(raw.decode('utf-8', errors='ignore'), strict=False)


def clean_content(content: str) -> str:
    c = re.sub(r'<br\s*/?>', '\n', content)
    c = re.sub(r'<[^>]+>', '', c)
    return html.unescape(c).strip()


def format_replies(rows: dict, tid: str, only_author: str = '') -> str:
    if only_author:
        rows = {lou: r for lou, r in rows.items()
                if str(r.get('authorid') or (r.get('author') or {}).get('uid') or '') == only_author}
    lines = [f'=== NGA tid={tid} 共 {len(rows)} 条（含主楼）'
             + (f'，仅 uid={only_author}' if only_author else '') + ' ===', '']
    for lou in sorted(rows.keys()):
        row = rows[lou]
        au = row.get('author', {}) or {}
        uname = au.get('username') or '?'
        uid = str(row.get('authorid') or au.get('uid') or '')
        content = clean_content(row.get('content') or '')
        subject = row.get('subject') or ''
        head = f'[{lou}楼] {uname}' + (f' (uid={uid})' if uid else '')
        if subject:
            head += f' | 标题: {subject}'
        lines.append(head)
        lines.append(content)
        lines.append('-' * 50)
    return '\n'.join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='NGA 回帖抓取器')
    ap.add_argument('tid', help='帖子 ID（read.php?tid=xxx）')
    ap.add_argument('-o', '--output', help='输出文件路径（默认 <cwd>/nga_tid<tid>_replies.txt）')
    ap.add_argument('--max-pages', type=int, default=100, help='最大翻页数（默认 100）')
    ap.add_argument('--cookie', help='登录态 Cookie 串（"name1=val1; name2=val2"），不传则游客态')
    ap.add_argument('--cookie-file', help='Netscape 格式 cookies.txt 路径（Get cookies.txt LOCALLY 导出）')
    ap.add_argument('--only-author', help='只输出指定 uid 的回帖（精确拔取某用户在本帖的全部回帖）')
    args = ap.parse_args()

    s_cookies = ''
    if args.cookie_file:
        _s = requests.Session()
        load_cookie_file(_s, args.cookie_file)
        s_cookies = '; '.join(f'{c.name}={c.value}' for c in _s.cookies)
    if args.cookie:
        s_cookies = args.cookie

    rows, total = fetch_replies(args.tid, args.max_pages, s_cookies)
    if not rows:
        print('未抓到任何内容')
        sys.exit(1)

    text = format_replies(rows, args.tid, args.only_author or '')
    out = args.output or os.path.join(os.getcwd(), f'nga_tid{args.tid}_replies.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'完成：{len(rows)} 条 -> {out}')


if __name__ == '__main__':
    main()
