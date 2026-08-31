# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\Project\dsh_rally_cars\publish\scripts')
from nga_replies import decode_nga_json, clean_content
import requests
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36', 'Referer': 'https://bbs.nga.cn/'})
for line in open(r'D:\Project\dsh_rally_cars\nga_cookies.txt', encoding='utf-8'):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    p = line.split('\t')
    if len(p) >= 7 and p[5] and p[6]:
        s.cookies.set(p[5], p[6], domain='bbs.nga.cn', path='/')
r = s.get('https://bbs.nga.cn/read.php?tid=46970227&__output=8&page=1', timeout=20)
d = decode_nga_json(r.content)
rows = d.get('data', {}).get('__R', {})
for k, v in sorted(rows.items(), key=lambda x: int(x[0])):
    uid = str(v.get('authorid') or '')
    if uid == '64497967':
        print(f'===== 楼层 {k} =====')
        print(clean_content(v.get('content') or ''))
        print()
