# -*- coding: utf-8 -*-
"""
NGA 用户回帖历史抓取器（登录态）

用法：
    python publish/scripts/nga_user_posts.py 64417325 --cookie-file "G:/Program Files/bbs.nga.cn_cookies.txt"
    python publish/scripts/nga_user_posts.py 64417325 -c "ngaPassportUid=xxx; ngaPassportUrlToken=yyy"
    python publish/scripts/nga_user_posts.py 64417325 --cookie-file ... -o D:/tmp/u.txt

接口：thread.php?authorid=X&searchpost=1&__output=8
返回结构：data.__T = 该用户参与过的主题列表（每条含 __P = 他在该主题的最新回帖），
          翻页按 __T__ROWS（主题总数）计数。注意：只给每主题最新一条回帖，非全部回帖。

反爬纪律：
- 页间隔 1.5-2.5s 随机（deep 模式：主题间再歇 2-3s 随机）；
- 非 200 退避重试（5s/15s），连败 3 次停止；不并行、不重跑已抓页面。
- 需要登录态（游客态返回 2048"你必须登录"），cookie 文件用 Netscape 格式
  （Get cookies.txt LOCALLY 导出）。
- deep 模式（--deep）用 read.php 的 authorid 直过滤抓该用户全部回帖：
  不翻全楼，大帖也只需 1-2 页；远古占位主题自动跳过。一次只跑一个 uid。
"""

import requests
import re
import argparse
import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nga_replies import (decode_nga_json, NGA_BASE, HEADERS,
                         load_cookie_file, fetch_replies)

MAX_PAGES = 20      # thread.php 分页有漂移，20 页硬顶
MAX_FAILS = 3
DEEP_MAX_PAGES = 30  # 单主题翻页上限（authorid 过滤后通常 1 页）

# thread.php 返回的远古占位主题（NGA 老数据），无内容、翻楼浪费请求
PLACEHOLDER_RE = re.compile(r'帖子发布或回复时间超过限制|帐号权限不足')
PLACEHOLDER_TID_MAX = 100000  # 正常帖子 tid 为 8 位数，远古占位为 3-5 位


def apply_cookie_str(session: requests.Session, cookie_str: str):
    for kv in cookie_str.split(';'):
        kv = kv.strip()
        if '=' in kv:
            k, v = kv.split('=', 1)
            session.cookies.set(k, v, domain='bbs.nga.cn', path='/')


def fetch_user_topics(session: requests.Session, authorid: str, out_file):
    """逐页抓取用户参与的主题，每主题附其最新回帖，边抓边写文件"""
    all_topics = {}
    total = None
    page = 1
    fails = 0
    zero_new_pages = 0
    skipped_placeholder = 0
    while page <= MAX_PAGES:
        url = f'{NGA_BASE}/thread.php?authorid={authorid}&searchpost=1&__output=8&page={page}'
        try:
            r = session.get(url, timeout=20)
        except requests.RequestException as e:
            fails += 1
            print(f'[page {page}] 网络错误 {e}（{fails}/{MAX_FAILS}）')
            if fails >= MAX_FAILS:
                break
            time.sleep(random.uniform(5, 15))
            continue

        if r.status_code != 200:
            fails += 1
            print(f'[page {page}] status {r.status_code}（{fails}/{MAX_FAILS}）')
            if fails >= MAX_FAILS:
                break
            time.sleep(random.uniform(5, 15))
            continue
        fails = 0

        d = decode_nga_json(r.content)
        data = d.get('data', {})
        topics = data.get('__T') or {}
        total = data.get('__T__ROWS') or total
        new = 0
        for idx, t in topics.items():
            tid = t.get('tid')
            subject = t.get('subject') or ''
            # 远古占位主题（"时间超过限制"/"权限不足"或 tid 异常小）不入库
            if PLACEHOLDER_RE.search(subject) or (tid and int(tid) < PLACEHOLDER_TID_MAX):
                skipped_placeholder += 1
                continue
            if tid and tid not in all_topics:
                all_topics[tid] = t
                new += 1
        print(f'[page {page}] 本页 {len(topics)} 主题（新增 {new}，跳过占位 {skipped_placeholder}），'
              f'累计 {len(all_topics)} / 总 {total}')

        # 边抓边写：中断也能保留已抓部分
        write_output(out_file, all_topics, authorid)

        if not topics:
            break
        if new == 0:
            zero_new_pages += 1
            if zero_new_pages >= 2:
                break  # 连续 2 页无新增（thread.php 分页漂移），停止
        else:
            zero_new_pages = 0
        page += 1
        time.sleep(random.uniform(2.5, 4))  # thread.php 老接口敏感，页间隔放宽
    return all_topics


def fetch_user_deep(session: requests.Session, authorid: str, all_topics: dict, out_file):
    """精确拔取：进每个主题按 authorid 直过滤抓全部回帖（不翻全楼）
    过滤模式下无真实楼层，以 postdate 标注。"""
    tids = sorted(all_topics.keys(), key=lambda x: int(x))
    lines = [f'=== NGA 用户 uid={authorid} 精确拔取（{len(tids)} 个主题，authorid 直过滤）===\n']
    cookie_str = '; '.join(f'{c.name}={c.value}' for c in session.cookies)
    for i, tid in enumerate(tids):
        t = all_topics[tid]
        rows, _ = fetch_replies(tid, DEEP_MAX_PAGES, cookie_str, authorid=authorid)
        lines.append(f"=== 主题 tid={tid} | {t.get('subject','')}（该用户 {len(rows)} 条回帖）===")
        for idx in sorted(rows.keys()):
            r = rows[idx]
            lines.append(f"[{r.get('postdate','')}] :")
            lines.append(clean(r.get('content')))
            lines.append('-' * 60)
        print(f'[{i+1}/{len(tids)}] tid={tid}: {len(rows)} 条')
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        time.sleep(random.uniform(2, 3))  # 主题间保守节流
    return out_file


def clean(c):
    c = re.sub(r'<br\s*/?>', '\n', c or '')
    c = re.sub(r'<[^>]+>', '', c)
    return c.replace('&nbsp;', ' ').strip()


def write_output(path, all_topics, authorid):
    lines = [f'=== NGA 用户 uid={authorid} 回帖历史（thread.php searchpost 口径：每主题仅最新一条回帖，共 {len(all_topics)} 个主题）===\n']
    for tid in sorted(all_topics.keys(), key=lambda x: int(x)):
        t = all_topics[tid]
        p = t.get('__P') or {}
        lines.append(f"=== 主题 tid={tid} | {t.get('subject','')} ===")
        lines.append(f"主题作者: {t.get('author','?')} (uid={t.get('authorid','')}) | 回帖数 {t.get('replies','')}")
        lines.append(f"该用户最新回帖 (pid={p.get('pid','')}, {p.get('postdate','')}):")
        lines.append(clean(p.get('content')))
        lines.append('-' * 60)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='NGA 用户回帖历史抓取器（需登录态 cookie）')
    ap.add_argument('authorid', help='用户 uid（read.php 里的 authorid）')
    ap.add_argument('-c', '--cookie', help='登录态 Cookie 串（"name1=val1; name2=val2"）')
    ap.add_argument('--cookie-file', help='Netscape 格式 cookies.txt 路径（Get cookies.txt LOCALLY 导出）')
    ap.add_argument('-o', '--output', help='输出文件（默认 <cwd>/nga_user_<uid>_posts.txt）')
    ap.add_argument('--deep', action='store_true',
                    help='精确拔取：进每个主题翻全楼过滤该 uid 全部回帖（请求量大，按需开启）')
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update(HEADERS)
    if args.cookie_file:
        load_cookie_file(s, args.cookie_file)
    if args.cookie:
        apply_cookie_str(s, args.cookie)

    out = args.output or os.path.join(os.getcwd(), f'nga_user_{args.authorid}_posts.txt')
    topics = fetch_user_topics(s, args.authorid, out)
    if not topics:
        print('未抓到任何主题（检查 cookie 是否含登录态：ngaPassportUid）')
        sys.exit(1)
    if args.deep:
        fetch_user_deep(s, args.authorid, topics, out)
        print(f'deep 完成 -> {out}')
        return
    print(f'完成：{len(topics)} 个主题 -> {out}')


if __name__ == '__main__':
    main()
