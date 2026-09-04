# -*- coding: utf-8 -*-
"""
NGA 版面热度定时扫描器

每小时抓取指定版面主题列表（thread.php?fid=xxx&__output=8），统计回帖数等热度指标，
追加一行到本机专属 CSV（文件名带机器名，双机各自写、git 同步不冲突）。

数据文件：
    data/nga_fid<fid>_heat_<machine>.csv   每机一份（随 git 同步）
    data/nga_fid<fid>_heat_merged.csv      merge.py 合并去重产物（本地，gitignore）

去重：扫描前检查 data 目录下所有本 fid 源 CSV 的最新一条，若与本次采样时间相差
小于 --dedup-window 秒（默认 900 = 15 分钟）则跳过——用于丢弃两机同时在线产生的
时间相近的重复采样。最终去重以 merge.py 为准（时间相近只保留每组第一条）。

用法：
    python nga_fid_heat.py --fid -343809 --pages 2
    python nga_fid_heat.py --fid -343809 --force --dedup-window 900

反爬纪律（勿改小）：页间隔 1.5-2.5s 随机、单进程不并行、非 200 退避重试。
"""

import argparse
import csv
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
    'new_1h', 'active_5m', 'active_1h',
    'lastpost_ts',
]

MAX_FAILS = 3
DEFAULT_DEDUP_WINDOW = 900  # 秒，两机同小时采样视为重复


def parse_ts(s):
    """'YYYY-MM-DD HH:MM:SS' -> unix 秒（失败返回 None）。"""
    try:
        return time.mktime(time.strptime(s, '%Y-%m-%d %H:%M:%S'))
    except Exception:
        return None


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
    return {
        'fid': fid,
        'total_threads': total_threads if total_threads is not None else '',
        'scanned': n,
        'replies_sum': replies_sum,
        'replies_avg': round(replies_sum / n, 2) if n else 0,
        'replies_max': max(replies) if n else 0,
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
    """data 目录下所有本 fid 源 CSV 里最新一条记录，返回 (unix_ts, machine, filename)。"""
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
        t = parse_ts(last['ts'])
        if t is not None and (latest is None or t > latest[0]):
            latest = (t, last.get('machine', ''), fn)
    return latest


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='NGA 版面热度扫描（每小时一行 CSV）')
    ap.add_argument('--fid', default='-343809', help='版面 fid（默认车版 -343809）')
    ap.add_argument('--pages', type=int, default=2, help='抓取页数（每页约 60 主题，默认 2 页）')
    ap.add_argument('--data-dir', default='', help='数据目录（默认 <脚本目录>/data）')
    ap.add_argument('--dedup-window', type=int, default=DEFAULT_DEDUP_WINDOW,
                    help='时间相近去重窗口，秒（默认 900 = 15 分钟）')
    ap.add_argument('--force', action='store_true', help='强制写入，忽略时间相近去重')
    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = args.data_dir or os.path.join(script_dir, 'data')
    machine = re.sub(r'[^A-Za-z0-9_-]', '_', socket.gethostname())
    csv_path = os.path.join(data_dir, f'nga_fid{args.fid}_heat_{machine}.csv')

    now = int(time.time())
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))

    # 时间相近去重（丢弃两机同时在线产生的重复采样）
    if not args.force:
        latest = latest_record(data_dir, args.fid)
        if latest:
            delta = abs(now - latest[0])
            if delta < args.dedup_window:
                print(f'[dedup] 距 {latest[2]} 最新记录仅 {delta:.0f}s（< {args.dedup_window}s），跳过写入')
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

    os.makedirs(data_dir, exist_ok=True)
    exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow(row)

    print(json.dumps(row, ensure_ascii=False))
    print(f'写入 -> {csv_path}')


if __name__ == '__main__':
    main()
