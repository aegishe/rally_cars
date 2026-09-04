# -*- coding: utf-8 -*-
"""
NGA 版面热度定时扫描器

每小时抓取指定版面主题列表（thread.php?fid=xxx&__output=8），统计回帖数等热度指标，
追加一行到本机专属 CSV（文件名带机器名，双机各自写、git 同步不冲突）。

数据文件：
    data/nga_fid<fid>_heat_<machine>.csv   每机一份（随 git 同步）
    data/nga_fid<fid>_heat_merged.csv      merge.py 合并去重产物（本地，gitignore）

去重：按自然小时——扫描前检查 data 目录下所有本 fid 源 CSV 的最新一条，若已属于
本次采样的同一自然小时（YYYY-MM-DD HH 相同）则跳过写入。这样两机同小时同时采样、
任务延迟、手动补跑（--force 除外）都不会产生第二条同小时数据。merge.py 合并时同样
按自然小时去重，保留每小时第一条。

用法：
    python nga_fid_heat.py --fid -343809 --pages 2
    python nga_fid_heat.py --fid -343809 --force

反爬纪律（勿改小）：页间隔 1.5-2.5s 随机、单进程不并行、非 200 退避重试。
"""

import argparse
import csv
import html
import json
import os
import random
import re
import socket
import sys
import time

import requests

NGA_BASE = 'https://bbs.nga.cn'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
    'Referer': NGA_BASE + '/',
}

FIELDNAMES = [
    'ts', 'machine', 'fid',
    'total_threads', 'scanned',
    'replies_sum', 'replies_avg', 'replies_max',
    'top_tid', 'top_subject',
    'new_1h', 'active_5m', 'active_1h',
    'lastpost_ts',
]

MAX_FAILS = 3


def clean_subject(s):
    """NGA 标题清洗：去标签、反转义、压空白、截断。"""
    s = re.sub(r'<[^>]+>', '', s or '')
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:80]


def ensure_guestjs(session: requests.Session, fid: str):
    r = session.get(f'{NGA_BASE}/thread.php?fid={fid}&__output=8', timeout=15)
    if r.status_code == 200:
        return
    t = r.content.decode('gbk', errors='ignore')
    m = re.search(r'guestJs=([\w]+)', t)
    if not m:
        raise RuntimeError(f'guestJs 提取失败（status={r.status_code}）')
    session.cookies.set('guestJs', m.group(1), domain='bbs.nga.cn', path='/')
    print(f'[guestJs] 获取成功')


def decode_json(raw: bytes):
    try:
        return json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json.loads(raw.decode('gbk', errors='ignore'), strict=False)


def fetch_board(session: requests.Session, fid: str, pages: int):
    topics = []
    total_threads = None
    fails = 0
    for page in range(1, pages + 1):
        url = f'{NGA_BASE}/thread.php?fid={fid}&__output=8&page={page}'
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
        try:
            d = decode_json(r.content)
        except json.JSONDecodeError as e:
            print(f'[page {page}] JSON 解析失败 {e}，停止')
            break
        data = d.get('data', {})
        if page == 1:
            total_threads = data.get('__ROWS')
        rows = data.get('__T', {})
        if not rows:
            break
        for idx in sorted(rows.keys(), key=lambda x: int(x)):
            topics.append(rows[idx])
        print(f'[page {page}] 抓到 {len(rows)} 条，累计 {len(topics)}')
        if page < pages:
            time.sleep(random.uniform(1.5, 2.5))
    return topics, total_threads


def compute_metrics(topics, total_threads, fid, now):
    replies = [int(t.get('replies') or 0) for t in topics]
    postdates = [int(t.get('postdate') or 0) for t in topics]
    lastposts = [int(t.get('lastpost') or 0) for t in topics]
    n = len(replies)
    replies_sum = sum(replies)
    # 当前第一热帖：抓取范围内回帖最多的主题
    top = max(topics, key=lambda t: int(t.get('replies') or 0)) if topics else {}
    return {
        'fid': fid,
        'total_threads': total_threads if total_threads is not None else '',
        'scanned': n,
        'replies_sum': replies_sum,
        'replies_avg': round(replies_sum / n, 2) if n else 0,
        'replies_max': max(replies) if n else 0,
        'top_tid': top.get('tid', ''),
        'top_subject': clean_subject(top.get('subject', '')),
        'new_1h': sum(1 for p in postdates if now - p <= 3600),
        'active_5m': sum(1 for l in lastposts if now - l <= 300),
        'active_1h': sum(1 for l in lastposts if now - l <= 3600),
        'lastpost_ts': max(lastposts) if lastposts else 0,
    }


def last_row_of(path):
    if not os.path.exists(path):
        return None
    last = None
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            last = row
    return last


def latest_record(data_dir, fid):
    """data 目录下所有本 fid 源 CSV 里最新一条记录，返回 (ts_str, machine, filename)。
    ts_str 格式 'YYYY-MM-DD HH:MM:SS'，字典序即时间序。"""
    prefix = f'nga_fid{fid}_heat_'
    latest = None
    if not os.path.isdir(data_dir):
        return None
    for fn in os.listdir(data_dir):
        if not (fn.startswith(prefix) and fn.endswith('.csv')):
            continue
        if fn.endswith('_merged.csv'):
            continue
        last = last_row_of(os.path.join(data_dir, fn))
        if not last or not last.get('ts'):
            continue
        if latest is None or last['ts'] > latest[0]:
            latest = (last['ts'], last.get('machine', ''), fn)
    return latest


def append_row_migrate(path, row):
    """追加一行。若文件 header 落后于当前 FIELDNAMES（历史数据缺新列），先迁移补齐列再追加。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            w.writeheader()
            w.writerow(row)
        return
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        old_header = list(rd.fieldnames or [])
        old_rows = list(rd)
    if old_header == FIELDNAMES:
        with open(path, 'a', encoding='utf-8', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)
        return
    # 迁移：旧行缺的新列补空，重写 header + 旧行 + 新行
    print(f'[csv] header 升级：{len(old_rows)} 条历史数据补齐新列')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
        w.writeheader()
        for r in old_rows:
            w.writerow(r)
        w.writerow(row)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='NGA 版面热度扫描（每小时一行 CSV）')
    ap.add_argument('--fid', default='-343809', help='版面 fid（默认车版 -343809）')
    ap.add_argument('--pages', type=int, default=2, help='抓取页数（每页约 60 主题，默认 2 页）')
    ap.add_argument('--data-dir', default='', help='数据目录（默认 <脚本目录>/data）')
    ap.add_argument('--force', action='store_true', help='强制写入，忽略同小时去重')
    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = args.data_dir or os.path.join(script_dir, 'data')
    machine = re.sub(r'[^A-Za-z0-9_-]', '_', socket.gethostname())
    csv_path = os.path.join(data_dir, f'nga_fid{args.fid}_heat_{machine}.csv')

    now = int(time.time())
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))

    # 按自然小时去重：任意源文件已有本小时记录则跳过（两机同小时、任务延迟、手动补跑都挡住）
    if not args.force:
        latest = latest_record(data_dir, args.fid)
        if latest and latest[0][:13] == ts[:13]:
            print(f'[dedup] {latest[2]} 已记录本小时（{latest[0][:13]}），跳过写入')
            sys.exit(0)

    s = requests.Session()
    s.headers.update(HEADERS)
    ensure_guestjs(s, args.fid)

    topics, total_threads = fetch_board(s, args.fid, args.pages)
    if not topics:
        print('未抓到任何主题，退出')
        sys.exit(1)

    row = compute_metrics(topics, total_threads, args.fid, now)
    row['ts'] = ts
    row['machine'] = machine

    append_row_migrate(csv_path, row)

    print(json.dumps(row, ensure_ascii=False))
    print(f'写入 -> {csv_path}')


if __name__ == '__main__':
    main()
