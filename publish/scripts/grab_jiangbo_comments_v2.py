# -*- coding: utf-8 -*-
"""抓取 B 站蒋波视频全部主评论（移动端 x/v2/reply/main，无需 wbi）。
节流纪律：每页随机 sleep 2.5~3.5 秒；-352 风控内圈 sleep 60 秒重试最多 5 次，
仍被风控则外圈 sleep 300 秒后继续（断点续传），直到抓完或达到总轮数上限。
输出：publish/jiangbo_comments.txt；进度：publish/scripts/.jiangbo_progress.json
"""
import json
import os
import random
import time
import urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
AID = '117045827995620'
OUT = r'D:\Project\dsh_rally_cars\publish\jiangbo_comments.txt'
PROG = r'D:\Project\dsh_rally_cars\publish\scripts\.jiangbo_progress.json'
MAX_ROUNDS = 60  # 外圈最大轮数（每轮风控冷却 300s，上限约 5 小时）


def get_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Referer': 'https://www.bilibili.com/',
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch(url):
    """抓一页：内圈 -352 风控重试 5 次（每次 60s）；网络异常 3 次（每次 5s）。"""
    for attempt in range(6):  # 1 次首发 + 5 次风控重试
        try:
            r = get_json(url)
        except Exception as e:
            print(f'[err] 请求异常 attempt={attempt + 1}: {e}', flush=True)
            time.sleep(5)
            continue
        if r.get('code') == -352:
            if attempt >= 5:
                return r  # 仍被风控，交给外圈冷却
            print(f'[risk] -352 风控，sleep 60s 后重试 ({attempt + 1}/5)', flush=True)
            time.sleep(60)
            continue
        return r
    return None


def main():
    seen = set()
    next_cursor = 0
    count = 0
    if os.path.exists(PROG):
        with open(PROG, encoding='utf-8') as f:
            p = json.load(f)
        seen = set(p.get('seen', []))
        next_cursor = p.get('next', 0)
        count = p.get('count', 0)
        print(f'resume: cursor={next_cursor} count={count} seen={len(seen)}', flush=True)
    else:
        with open(OUT, 'w', encoding='utf-8') as f:
            f.write('')
        print('fresh start', flush=True)

    fout = open(OUT, 'a', encoding='utf-8')

    def save_prog(done=False):
        with open(PROG, 'w', encoding='utf-8') as f:
            json.dump({'seen': list(seen), 'next': next_cursor,
                       'count': count, 'done': done}, f)

    try:
        for rnd in range(1, MAX_ROUNDS + 1):
            url = f'https://api.bilibili.com/x/v2/reply/main?type=1&oid={AID}&mode=3&next={next_cursor}'
            r = fetch(url)

            if r is None or r.get('code') == -352:
                # 内圈重试耗尽仍被风控 → 外圈冷却后续抓
                print(f'[cool] 第 {rnd} 轮仍未恢复（code={r and r.get("code")}），sleep 300s 冷却续抓；已抓 {count} 条', flush=True)
                save_prog()
                time.sleep(300)
                continue

            if r.get('code') != 0:
                print(f'[code] {r.get("code")} {r.get("message")} 终态停止；已抓 {count} 条', flush=True)
                save_prog(done=True)
                break

            data = r.get('data') or {}
            reps = data.get('replies') or []
            new = 0
            for rep in reps:
                rpid = rep.get('rpid_str')
                if rpid in seen:
                    continue
                seen.add(rpid)
                msg = (rep.get('content') or {}).get('message', '').replace('\n', ' ').replace('\r', ' ')
                uname = (rep.get('member') or {}).get('uname', '')
                fout.write(f'[{uname}] {msg}\n')
                new += 1
            count += new

            cursor = data.get('cursor') or {}
            is_end = cursor.get('is_end', False)
            next_cursor = cursor.get('next', 0)
            fout.flush()
            save_prog()
            print(f'next={next_cursor}: +{new} (total {count}) is_end={is_end}', flush=True)
            if is_end or not reps:
                save_prog(done=True)
                break
            time.sleep(random.uniform(2.5, 3.5))
    finally:
        fout.close()

    done = False
    if os.path.exists(PROG):
        with open(PROG, encoding='utf-8') as f:
            done = json.load(f).get('done', False)
    print(f'EXIT: done={done} 共 {count} 条 -> {OUT}', flush=True)
    return count, done


if __name__ == '__main__':
    main()
