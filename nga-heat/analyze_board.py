# -*- coding: utf-8 -*-
"""一次性回溯分析：抓车版多页，按钟点聚合 postdate/lastpost，看热度日内分布。

口径：
- 每帖只带 postdate(发帖) 和 lastpost(最后回复)，无法知道中间每条回复的时间；
  "lastpost 钟点分布" = 每钟点至少有新回复的主题数（活跃度下界，被多次回复只算一次）。
- 版面列表大致按 lastpost 倒序推进，抓得越深覆盖越早的活跃帖，但混有被顶起的老帖。

用法：python analyze_board.py [pages=25]
"""
import json
import re
import sys
import time
import random
import requests
from collections import Counter, defaultdict

NGA = 'https://bbs.nga.cn'
FID = '-343809'
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 25
TZ = 8  # 北京时间

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
           'Referer': NGA + '/'}


def bj_hour(ts):
    """unix 秒 -> 北京钟点 (0-23)。"""
    return (int(ts) // 3600 + TZ) % 24


def bj_ymd_hour(ts):
    return time.strftime('%m-%d %H', time.gmtime(int(ts) + TZ * 3600))


def main():
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(f'{NGA}/thread.php?fid={FID}&__output=8', timeout=15)
    if r.status_code != 200:
        m = re.search(r'guestJs=([\w]+)', r.content.decode('gbk', 'ignore'))
        if not m:
            print('guestJs fail', r.status_code)
            sys.exit(1)
        s.cookies.set('guestJs', m.group(1), domain='bbs.nga.cn', path='/')
        time.sleep(1)

    now = int(time.time())
    topics = {}  # tid -> topic
    for page in range(1, PAGES + 1):
        ok = False
        for _ in range(3):
            try:
                rr = s.get(f'{NGA}/thread.php?fid={FID}&__output=8&page={page}', timeout=20)
                if rr.status_code == 200:
                    d = json.loads(rr.content.decode('utf-8', 'ignore'))
                    T = (d.get('data') or {}).get('__T', {})
                    for t in T.values():
                        topics[t.get('tid')] = t
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(random.uniform(5, 12))
        if not ok:
            print(f'page {page} failed, stopping', flush=True)
            break
        print(f'page {page} done, unique {len(topics)}', flush=True)
        time.sleep(random.uniform(1.5, 2.5))

    if not topics:
        print('no data')
        sys.exit(1)

    # 收集时间字段
    rows = []
    for tid, t in topics.items():
        pd = int(t.get('postdate') or 0)
        lp = int(t.get('lastpost') or 0)
        if pd and lp:
            rows.append((tid, pd, lp))
    n = len(rows)
    print(f'\n== unique topics={n}')
    if not n:
        return

    # 覆盖诊断
    now = int(time.time())
    ages_lp = sorted(now - lp for _, _, lp in rows)
    ages_pd = sorted(now - pd for _, pd, _ in rows)
    print(f'lastpost age: min {ages_lp[0]/3600:.1f}h med {ages_lp[n//2]/3600:.1f}h max {ages_lp[-1]/3600:.1f}h')
    print(f'postdate age: min {ages_pd[0]/3600:.1f}h med {ages_pd[n//2]/3600:.1f}h max {ages_pd[-1]/3600:.1f}h')

    # 只保留"过去 96h 内最后回复"的帖（近 4 天活跃池），避免远古帖污染日内形态
    pool_lp = [(tid, pd, lp) for tid, pd, lp in rows if now - lp <= 96 * 3600]
    print(f'pool (lastpost<=96h): {len(pool_lp)}')

    if not pool_lp:
        return

    # A. lastpost 钟点分布（"该钟点至少有新回复"的主题数）
    c_lp = Counter()
    # B. postdate 钟点分布（该钟点发的新帖数），仅统计发帖也在 96h 内的
    c_pd = Counter()
    for tid, pd, lp in pool_lp:
        c_lp[bj_hour(lp)] += 1
        if now - pd <= 96 * 3600:
            c_pd[bj_hour(pd)] += 1

    def dump(c, label):
        print(f'\n== {label} ==')
        total = sum(c.values())
        print('hour : count  %   (cum)')
        cum = 0
        for h in range(24):
            v = c.get(h, 0)
            cum += v
            bar = '#' * int(v / max(total, 1) * 60)
            print(f'{h:02d}   : {v:4d}  {v/max(total,1)*100:4.1f}% {bar}')
        print(f'total {total}')

    dump(c_lp, 'lastpost by BJ hour (topics with a new reply that hour, last-4d pool)')
    dump(c_pd, 'postdate by BJ hour (new threads that hour, last-4d)')

    # C. 过去 24h：按距现在小时数（0-23h）看每小时的活跃主题数（本次抓取覆盖的）
    print('\n== last 24h: active topics by hours-ago bucket ==')
    hb = defaultdict(int)
    for tid, pd, lp in pool_lp:
        age = int((now - lp) / 3600)
        if 0 <= age <= 23:
            hb[age] += 1
    for age in range(24):
        v = hb.get(age, 0)
        print(f'{age:2d}h ago ({bj_ymd_hour(now - age*3600)}): {v:3d}')


if __name__ == '__main__':
    main()
