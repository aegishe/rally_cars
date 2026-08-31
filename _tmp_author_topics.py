# -*- coding: utf-8 -*-
import requests, json, sys, time, random
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36', 'Referer': 'https://bbs.nga.cn/'})
for line in open(r'D:\Project\dsh_rally_cars\nga_cookies.txt', encoding='utf-8'):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    p = line.split('\t')
    if len(p) >= 7 and p[5] and p[6]:
        s.cookies.set(p[5], p[6], domain='bbs.nga.cn', path='/')
seen = set()
for page in range(1, 25):
    try:
        r = s.get(f'https://bbs.nga.cn/thread.php?authorid=64497967&__output=8&page={page}', timeout=20)
        d = json.loads(r.content.decode('utf-8', errors='ignore'))
        rows = d.get('data', {}).get('__T', {})
        if not rows:
            break
        for k, v in rows.items():
            tid = v.get('tid', '')
            if tid in seen:
                continue
            seen.add(tid)
            print(f"{v.get('postdate','')} {v.get('subject','')[:60]} | replies={v.get('replies','')}")
        time.sleep(random.uniform(1.5, 2.5))
    except Exception as e:
        print(f'ERR page {page}: {e}')
        break
print(f'TOTAL {len(seen)}')
