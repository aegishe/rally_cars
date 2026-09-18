# -*- coding: utf-8 -*-
"""从 NGA 抓取的本人帖子中提取「网友 → 本人回复」的完整问答对，用于补全语料。

默认 dry-run（只统计不写盘）。加 --write 才写盘，且先备份原件。
"""
import re, os, sys, io, shutil, glob, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NGADIR = r"D:\Project\dsh_rally_cars\knowledge\nga"
TARGET = r"D:\Project\dsh_chat\knowledge\My\2026-车.txt"
ME = '64578'


def clean(s):
    s = re.sub(r'\[uid=(\d+)\]([^\[]*)\[/uid\]', r'\2', s)
    s = re.sub(r'\[pid=[^\]]*\]', '', s)
    s = re.sub(r'\[/?[a-zA-Z][^\]]*\]', '', s)
    # 去掉行尾的楼层分隔线
    s = re.sub(r'-{5,}', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def extract(path):
    """返回 [(对方原文, 我的回应), ...]"""
    txt = open(path, encoding='utf-8').read()
    blocks = re.split(r'^\[(\d+)楼\]\s+(.+?)\s+\(uid=(\d+)\)', txt, flags=re.M)
    out = []
    for i in range(1, len(blocks), 4):
        uid, body = blocks[i + 2], blocks[i + 3]
        if uid != ME:
            continue
        quotes = re.findall(r'\[quote\](.*?)\[/quote\]', body, re.S)
        if not quotes:
            continue
        # 我的回应 = 去掉所有引用块后的正文
        mine = re.sub(r'\[quote\].*?\[/quote\]', '', body, flags=re.S)
        mine = re.sub(r'\[b\]Reply to.*?\[/b\]', '', mine, flags=re.S)
        mine = clean(mine)
        if not mine:
            continue
        for q in quotes:
            # 只保留「引用他人发言」的 quote：必须含 Post by [uid=X] 且 X 不是本人
            qm = re.search(r'Post by \[uid=(\d+)\]', q)
            if not qm or qm.group(1) == ME:
                continue
            # 引用块首行是 pid/作者/时间，去掉
            his = re.sub(r'^\s*\[pid=[^\]]*\][^\n]*\n?', '', q)
            his = clean(his)
            # 跳过只有分隔线/空内容的引用
            if len(his) < 6:
                continue
            out.append((his, mine))
    return out


files = sorted(glob.glob(os.path.join(NGADIR, 'nga_tid[0-9]*_replies.txt')))
pairs, per_file = [], {}
for p in files:
    # 只取本人为楼主的帖子
    head = open(p, encoding='utf-8').read(3000)
    m = re.search(r'\[0楼\]\s+(.+?)\s+\(uid=(\d+)\)', head)
    if not m or m.group(2) != ME:
        continue
    got = extract(p)
    if got:
        per_file[os.path.basename(p)] = len(got)
        pairs += got

# 去重（同一对内容只留一次）
seen, uniq = set(), []
for his, my in pairs:
    k = (his[:40], my[:40])
    if k in seen:
        continue
    seen.add(k)
    uniq.append((his, my))

orig = open(TARGET, encoding='utf-8').read() if os.path.exists(TARGET) else ''
new = [(h, m) for h, m in uniq if h[:24] not in orig]

print(f'源帖 {len(per_file)} 个：')
for k, v in sorted(per_file.items()):
    print(f'  {k}  → {v} 对')
print(f'\n提取问答对 {len(pairs)} → 去重 {len(uniq)} → 原件已有 {len(uniq)-len(new)} → 待补 {len(new)}')
print(f'原件当前 {len(orig)} 字符')

if '--write' in sys.argv and new:
    bak = TARGET + '.bak-' + datetime.date.today().strftime('%Y%m%d')
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
        print(f'已备份 → {bak}')
    add = '\n\n' + '\n\n'.join(f'网友：{h}\n\n回复：{m}' for h, m in new) + '\n'
    open(TARGET, 'a', encoding='utf-8').write(add)
    print(f'已追加 {len(new)} 对，文件现 {os.path.getsize(TARGET)} 字节')
else:
    print('\n(dry-run，未写盘。加 --write 执行)')
    if new:
        print('\n---- 待补样例（前 3 对）----')
        for h, m in new[:3]:
            print(f'\n网友：{h[:160]}\n\n回复：{m[:240]}')
