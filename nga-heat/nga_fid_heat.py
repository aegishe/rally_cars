# -*- coding: utf-8 -*-
"""
NGA 版面热度定时扫描器

每小时抓取指定版面的主题列表（thread.php?fid=xxx&__output=8），统计回帖数等热度指标，
追加一行到 CSV。游客态（guestJs）访问，无需登录账号。

用法：
    python nga_fid_heat.py --fid -343809 --pages 2
    python nga_fid_heat.py --fid -343809 --csv D:\\data\\heat.csv --force

反爬纪律（勿改小）：
    - 页间隔 1.5-2.5s 随机
    - 单进程、不并行、不加速
    - 非 200 退避重试，连败 3 次停止
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


def ensure_guestjs(session: requests.Session, fid: str):
    """第一次请求版面触发游客 cookie + guestJs，写入 session。

    游客态首次访问返回 403，body 里 JS 会生成 guestJs=xxx；
    带该 cookie 再请求即返回 200 JSON。登录态首次即 200 则无需处理。
    """
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
    """NGA JSON 自适应解码：优先 UTF-8，失败退 GBK。"""
    try:
        return json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json.loads(raw.decode('gbk', errors='ignore'), strict=False)


def fetch_board(session: requests.Session, fid: str, pages: int):
    """抓取版面前 N 页主题列表，返回 (topics, total_threads)。"""
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
    """基于抓到的主题列表计算热度指标。"""
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
    """读 CSV 最后一条数据行（无则 None）。"""
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        last = None
        for row in reader:
            last = row
        return last


def append_csv(path, row, force=False):
    """追加一行；同 machine 同一小时内已有记录则跳过（防重复运行）。"""
    if not force:
        last = last_row_of(path)
        if last and last.get('machine') == row['machine'] and last.get('ts', '')[:13] == row['ts'][:13]:
            print(f'[csv] 本机本小时已有记录（{row["ts"][:13]}），跳过写入')
            return False

    exists = os.path.exists(path) and os.path.getsize(path) > 0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return True


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='NGA 版面热度扫描（每小时一行 CSV）')
    ap.add_argument('--fid', default='-343809', help='版面 fid（默认车版 -343809）')
    ap.add_argument('--pages', type=int, default=2, help='抓取页数（每页约 60 主题，默认 2 页）')
    ap.add_argument('--csv', default='', help='CSV 输出路径（默认 <脚本目录>/data/nga_fid<fid>_heat.csv）')
    ap.add_argument('--force', action='store_true', help='强制写入，忽略本小时去重')
    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = args.csv or os.path.join(script_dir, 'data', f'nga_fid{args.fid}_heat.csv')

    now = int(time.time())
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
    machine = socket.gethostname()

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

    written = append_csv(csv_path, row, force=args.force)
    print(json.dumps(row, ensure_ascii=False))
    print(f'{"写入" if written else "跳过"} -> {csv_path}')


if __name__ == '__main__':
    main()
