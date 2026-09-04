# -*- coding: utf-8 -*-
"""
合并各机 CSV，输出单份去重后的 merged CSV。

把 data/ 下所有 nga_fid<fid>_heat_<machine>.csv 按 ts 排序，
丢弃时间相差小于 --dedup-window 秒（默认 900 = 15 分钟）的重复组（保留每组第一条），
输出 data/nga_fid<fid>_heat_merged.csv（本地产物，已 gitignore）。

用法：
    python merge.py --fid -343809 --dedup-window 900
"""

import argparse
import csv
import os
import sys
import time

FIELDNAMES = [
    'ts', 'machine', 'fid',
    'total_threads', 'scanned',
    'replies_sum', 'replies_avg', 'replies_max',
    'new_1h', 'active_5m', 'active_1h',
    'lastpost_ts',
]


def parse_ts(s):
    try:
        return time.mktime(time.strptime(s, '%Y-%m-%d %H:%M:%S'))
    except Exception:
        return None


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='合并各机 CSV 并按时间相近去重')
    ap.add_argument('--fid', default='-343809')
    ap.add_argument('--data-dir', default='')
    ap.add_argument('--dedup-window', type=int, default=900)
    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = args.data_dir or os.path.join(script_dir, 'data')
    prefix = f'nga_fid{args.fid}_heat_'

    rows = []
    for fn in sorted(os.listdir(data_dir)):
        if not (fn.startswith(prefix) and fn.endswith('.csv')):
            continue
        if fn.endswith('_merged.csv'):
            continue
        p = os.path.join(data_dir, fn)
        with open(p, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('ts'):
                    rows.append(row)
        print(f'[读] {fn}')

    if not rows:
        print('无源数据')
        sys.exit(1)

    rows.sort(key=lambda r: parse_ts(r.get('ts', '')) or 0)

    kept = []
    dropped = 0
    for r in rows:
        t = parse_ts(r.get('ts', ''))
        if t is None:
            kept.append(r)
            continue
        if kept:
            t_last = parse_ts(kept[-1].get('ts', ''))
            if t_last is not None and abs(t - t_last) < args.dedup_window:
                dropped += 1
                continue
        kept.append(r)

    out = os.path.join(data_dir, f'nga_fid{args.fid}_heat_merged.csv')
    with open(out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(kept)

    print(f'合并 {len(rows)} 条 -> 去重 {dropped} 条 -> 保留 {len(kept)} 条')
    print(f'输出 -> {out}')


if __name__ == '__main__':
    main()
