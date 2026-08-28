# -*- coding: utf-8 -*-
"""临时：确认 NGA JSON 里真正的总页数/总回帖字段"""
import requests, re, json

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
    'Referer': 'https://bbs.nga.cn/',
})
r0 = s.get('https://bbs.nga.cn/read.php?tid=47412917', timeout=15)
t0 = r0.content.decode('gbk', errors='ignore')
m = re.search(r'guestJs=([\w]+)', t0)
s.cookies.set('guestJs', m.group(1), domain='bbs.nga.cn', path='/')

r = s.get('https://bbs.nga.cn/read.php?tid=47412917&page=2&__output=8', timeout=20)
d = json.loads(r.content.decode('utf-8', errors='ignore'), strict=False)
data = d.get('data', {})
print('=== data 顶层字段 ===')
for k, v in data.items():
    t = type(v).__name__
    if isinstance(v, dict):
        print(f'{k}: dict keys={list(v.keys())[:12]}')
    elif isinstance(v, list):
        print(f'{k}: list len={len(v)}')
    else:
        print(f'{k}: {t} = {str(v)[:60]}')
print()
print('=== __T（帖子信息）===')
t_info = data.get('__T', {})
if isinstance(t_info, dict):
    for k in ['tid', 'subject', 'replies', 'pages', 'lou']:
        if k in t_info:
            print(f'  __T.{k} = {t_info[k]}')
    print('  __T 全字段:', {k: str(v)[:50] for k, v in t_info.items()})
