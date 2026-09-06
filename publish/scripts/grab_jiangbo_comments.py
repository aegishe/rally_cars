# -*- coding: utf-8 -*-
"""抓取 B 站蒋波视频全部主评论（移动端 x/v2/reply/main 接口，cursor 游标分页，无需 wbi）。
输出：publish/jiangbo_comments.txt（每行 [用户名] 评论内容）
"""
import json
import urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
AID = '117045827995620'
OUT = r'D:\Project\dsh_rally_cars\publish\jiangbo_comments.txt'

def get_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Referer': 'https://www.bilibili.com/',
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))

def collect(reps, allc):
    for rep in reps:
        msg = rep['content']['message'].replace('\n', ' ').replace('\r', ' ')
        allc.append(f"[{rep['member']['uname']}] {msg}")

allc = []
seen = set()
next_cursor = 0
for i in range(80):
    url = f'https://api.bilibili.com/x/v2/reply/main?type=1&oid={AID}&mode=3&next={next_cursor}'
    try:
        r = get_json(url)
    except Exception as e:
        print(f'[err] next={next_cursor}: {e}')
        break
    if r['code'] != 0:
        print(f'[code] {r["code"]} {r.get("message")}')
        break
    data = r['data']
    reps = data.get('replies') or []
    # 去重（按 rpid）
    for rep in reps:
        rpid = rep['rpid_str']
        if rpid in seen:
            continue
        seen.add(rpid)
        msg = rep['content']['message'].replace('\n', ' ').replace('\r', ' ')
        allc.append(f"[{rep['member']['uname']}] {msg}")
    cursor = data.get('cursor') or {}
    is_end = cursor.get('is_end', False)
    next_cursor = cursor.get('next', 0)
    print(f'next={next_cursor}: +{len(reps)} (total {len(allc)}) is_end={is_end}')
    if is_end or not reps:
        break

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(allc))
print(f'saved {len(allc)} comments -> {OUT}')
