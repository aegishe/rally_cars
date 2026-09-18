# -*- coding: utf-8 -*-
"""NGA 用户台账 —— 累积式记录「观察 / 判定 / 交锋」

真相源：knowledge/nga/ledger/observations.jsonl（一行一条观察，只追加不覆盖）
人读视图：knowledge/nga/用户台账.md（由 render 生成，请勿手改）

用法：
  python scripts/nga_ledger.py scan                     扫描历史抓取文件，自动回填 profile
  python scripts/nga_ledger.py import-manual <file>     导入人工条目（jsonl）
  python scripts/nga_ledger.py add --uid U [--name N] --kind encounter --text "..."
  python scripts/nga_ledger.py show <uid|昵称>          秒查某人全部记录
  python scripts/nga_ledger.py list                     全部用户概览
  python scripts/nga_ledger.py render                   生成 md 台账
"""

import os, re, sys, io, json, glob, argparse, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(ROOT, 'knowledge', 'nga', 'ledger')
OBS = os.path.join(LEDGER_DIR, 'observations.jsonl')
VIEW = os.path.join(ROOT, 'knowledge', 'nga', '用户台账.md')
SCAN_DIRS = [os.path.join(ROOT, 'knowledge', 'nga'), os.path.join(ROOT, '.tmp')]

TOPICS = ['比亚迪', '迪子', '笛子', 'BYD', '小米', '特斯拉', '蔚来', '换电', '理想', '小鹏',
          '宁德', '长城', '吉利', '极氪', '华为', '问界', '鸿蒙', '智驾', '刀片', '闪充', '固态']
ATTACK = ['垃圾', '煞笔', '傻逼', '傻', '泰迪', '水军', '公关', '商单', '智商税', '洗地', '跪', '双标',
          '吹', '黑子', '吠', '猕猴', '海狗']
SELF_KW = ['我买', '我的车', '我车是', '我的是', '提车', '订了', '下定', '车主']
SKIP = re.compile(r'^\s*(\[quote\]|\[b\]Reply to|Reply to|\[pid|主题作者:|该用户|===)')


def load():
    if not os.path.exists(OBS):
        return []
    out = []
    with open(OBS, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def save(rows):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    with open(OBS, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def next_id(rows, kind):
    d = datetime.date.today().strftime('%Y%m%d')
    n = sum(1 for r in rows if r.get('id', '').startswith(d)) + 1
    return f'{d}-{n:03d}'


def build_name_map():
    """从所有抓取文件反查 uid -> 昵称（两种格式：楼层标头 + 引用块）"""
    names = {}

    def add(u, n):
        n = (n or '').strip()
        if not n or n == '?':
            return
        names.setdefault(u, {})
        names[u][n] = names[u].get(n, 0) + 1

    for d in SCAN_DIRS:
        for path in glob.glob(os.path.join(d, 'nga_*.txt')):
            try:
                for line in open(path, encoding='utf-8'):
                    m = re.match(r'\s*\[(\d+)楼\]\s+(.+?)\s+\(uid=(\d+)\)', line)
                    if m:
                        add(m.group(3), m.group(2))
                    for mm in re.finditer(r'\[uid=(\d+)\]([^\[]*)\[/uid\]', line):
                        add(mm.group(1), mm.group(2))
            except Exception:
                pass
    return {u: max(c, key=c.get) for u, c in names.items()}


def build_appearances():
    """从帖子抓取文件统计每个 uid 出现在哪些 tid"""
    app = {}
    for d in SCAN_DIRS:
        for path in glob.glob(os.path.join(d, 'nga_tid*_replies.txt')):
            mt = re.search(r'tid(\d+)', os.path.basename(path))
            if not mt:
                continue
            seen = set()
            for line in open(path, encoding='utf-8'):
                m = re.match(r'\s*\[(\d+)楼\]\s+(.+?)\s+\(uid=(\d+)\)', line)
                if m:
                    seen.add(m.group(3))
            for u in seen:
                app.setdefault(u, set()).add(mt.group(1))
    return {u: sorted(v) for u, v in app.items()}


def parse_user_file(path, name_map=None):
    """从 nga_user_*.txt 提取 uid/昵称/主题数/词频/样本"""
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'uid=(\d+)', txt[:400])
    if not m:
        return None
    uid = m.group(1)
    name = (name_map or {}).get(uid, '')
    mt = re.search(r'(\d+)\s*个主题', txt[:600])
    threads = int(mt.group(1)) if mt else txt.count('该用户最新回帖')
    is_deep = ('精确拔取' in txt[:200]) or ('authorid 直过滤' in txt[:200]) or ('_deep' in path)
    topics = {k: txt.count(k) for k in TOPICS if txt.count(k) > 0}
    attack = {k: txt.count(k) for k in ATTACK if txt.count(k) > 0}
    # 样本发言：按主题块抽含品牌/自曝词的句子
    quotes, facts = [], []
    for blk in txt.split('-' * 40):
        # 关键：剔除跨行引用块，否则引文里独立成行的句子会被误当成本人发言
        body = re.sub(r'\[quote\].*?\[/quote\]', '', blk, flags=re.S)
        for ln in body.split('\n'):
            s = ln.strip()
            if not s or len(s) < 8 or SKIP.match(s):
                continue
            if any(k in s for k in TOPICS) and len(quotes) < 8:
                quotes.append(s[:120])
                break
    for blk in txt.split('-' * 40):
        blk = re.sub(r'\[quote\].*?\[/quote\]', '', blk, flags=re.S)
        for ln in blk.split('\n'):
            s = ln.strip()
            if any(k in s for k in SELF_KW) and len(s) > 8 and not SKIP.match(s) and len(facts) < 4:
                facts.append(s[:120])
                break
    deep = is_deep
    return {'uid': uid, 'name': name, 'threads': threads, 'chars': len(txt),
            'topics': topics, 'attack': attack, 'quotes': quotes,
            'facts': facts, 'evidence': 'C' if deep else 'B',
            'source': os.path.relpath(path, ROOT)}


def cmd_scan(args):
    rows = load()
    if getattr(args, 'rebuild', False):
        rows = [r for r in rows if r.get('kind') != 'profile']
    name_map = build_name_map()
    app = build_appearances()
    seen = {(r['uid'], r['source']) for r in rows if r.get('kind') == 'profile'}
    added = 0
    for d in SCAN_DIRS:
        for path in sorted(glob.glob(os.path.join(d, 'nga_user_*.txt'))):
            info = parse_user_file(path, name_map)
            if not info or (info['uid'], info['source']) in seen:
                continue
            row = {'id': next_id(rows, 'profile'), 'ts': str(datetime.date.today()),
                   'kind': 'profile', 'note': '', 'stance': '', 'traits': [], 'tags': [],
                   'reaction': '', 'appear_threads': app.get(info['uid'], [])[:30], **info}
            rows.append(row)
            seen.add((info['uid'], info['source']))
            added += 1
    save(rows)
    print(f'扫描完成：新增 {added} 条 profile，当前共 {len(rows)} 条记录，'
          f'涉及 {len({r["uid"] for r in rows})} 个 uid')


def cmd_import_manual(args):
    rows = load()
    added = 0
    with open(args.file, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith('#'):
                continue
            row = json.loads(ln)
            row.setdefault('id', next_id(rows, row.get('kind', 'note')))
            row.setdefault('ts', str(datetime.date.today()))
            rows.append(row)
            added += 1
    save(rows)
    print(f'导入人工条目 {added} 条，当前共 {len(rows)} 条')


def cmd_add(args):
    rows = load()
    row = {'id': next_id(rows, args.kind), 'ts': args.date or str(datetime.date.today()),
           'kind': args.kind, 'uid': args.uid, 'name': args.name or '',
           'evidence': args.evidence, 'source': args.source or '',
           'text': args.text, 'reaction': args.reaction or '',
           'tags': [t for t in (args.tags or '').split(',') if t]}
    rows.append(row)
    save(rows)
    print(f'已记录：{row["id"]} [{row["kind"]}] uid={row["uid"]}')


def merged(rows, uid):
    prof = [r for r in rows if r['uid'] == uid and r.get('kind') == 'profile']
    # 每个来源保留最新的 profile
    merged_p = {}
    for r in prof:
        merged_p[r['source']] = r
    prof = list(merged_p.values())
    others = [r for r in rows if r['uid'] == uid and r.get('kind') != 'profile']
    return prof, sorted(others, key=lambda x: x.get('ts', ''))


def fmt_person(rows, uid, verbose=True):
    prof, others = merged(rows, uid)
    if not prof and not others:
        return None
    name = next((r.get('name') for r in prof + others if r.get('name')), '')
    topics, attack = {}, {}
    for p in prof:
        for k, v in p.get('topics', {}).items():
            topics[k] = max(topics.get(k, 0), v)
        for k, v in p.get('attack', {}).items():
            attack[k] = max(attack.get(k, 0), v)
    threads = max([p.get('threads', 0) for p in prof], default=0)
    lines = [f'### uid={uid} {name}'.rstrip()]
    lines.append(f'- 抓取来源：' + ('；'.join(f'{p["source"]}（{p["evidence"]}级，{p["threads"]}主题）' for p in prof) or '无'))
    lines.append(f'- 跨帖规模：最多 {threads} 个主题')
    ath = next((p.get('appear_threads') for p in prof if p.get('appear_threads')), [])
    if ath:
        lines.append(f'- 本地帖子库中出现于 {len(ath)} 个帖：' + '、'.join(ath[:10]) + ('…' if len(ath) > 10 else ''))
    if topics:
        lines.append('- 话题分布：' + ' · '.join(f'{k} {v}' for k, v in sorted(topics.items(), key=lambda x: -x[1])))
    if attack:
        lines.append('- 攻击词：' + ' · '.join(f'{k} {v}' for k, v in sorted(attack.items(), key=lambda x: -x[1])))
    for p in prof:
        if p.get('facts'):
            lines.append('- 自曝/身份线索（来自该用户在其他帖的历史，与你无直接互动）：')
            lines += [f'    - {q}' for q in p['facts']]
    if verbose:
        for p in prof:
            if p.get('quotes'):
                lines.append('- 跨帖历史样本（该用户在其他帖的发言，与本人无直接互动）：')
                lines += [f'    - {q}' for q in p['quotes'][:5]]
    for o in others:
        tag = ' '.join(f'[{t}]' for t in o.get('tags', []))
        head = f'- **{o.get("kind")}** {o.get("ts","")} {tag}'.rstrip()
        lines.append(head)
        for k in ('stance', 'traits', 'text', 'reaction', 'note'):
            v = o.get(k)
            if not v:
                continue
            if isinstance(v, list):
                v = ' · '.join(v)
            lines.append(f'    - {k}：{v}')
    return '\n'.join(lines)


def cmd_show(args):
    rows = load()
    key = args.key
    uids = set()
    if key.isdigit():
        uids.add(key)
    else:
        uids |= {r['uid'] for r in rows if key in (r.get('name') or '')}
    if not uids:
        print(f'台账中没有匹配「{key}」的记录。')
        print('提示：先用 scan 回填历史抓取，或用 add 手工登记。')
        return
    for uid in sorted(uids):
        print(fmt_person(rows, uid))
        print()


def _clean(s):
    s = re.sub(r'\[uid=(\d+)\]([^\[]*)\[/uid\]', r'\2', s)
    s = re.sub(r'\[pid=[^\]]*\]', '', s)
    s = re.sub(r'\[/?[a-zA-Z][^\]]*\]', '', s)
    s = re.sub(r'[-=]{5,}', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def find_my_threads(uid):
    """找出以 uid 为楼主的帖子抓取文件，按 tid 去重"""
    files = {}
    for d in SCAN_DIRS:
        for pat in ('nga_tid*_replies*.txt', 'nga_pian*.txt'):
            for p in glob.glob(os.path.join(d, pat)):
                head = open(p, encoding='utf-8').read(4000)
                m = re.search(r'\[0楼\]\s+(.+?)\s+\(uid=(\d+)\)', head)
                if not m or m.group(2) != uid:
                    continue
                k = re.search(r'tid(\d+)', os.path.basename(p))
                key = k.group(1) if k else None
                if key is None:
                    m2 = re.search(r'tid=(\d+)', open(p, encoding='utf-8').read())
                    key = m2.group(1) if m2 else os.path.basename(p)
                # 优先级：nga_tid 前缀 > 其他命名；latest 后缀优先
                def _pref(x):
                    b = os.path.basename(x)
                    return (2 if b.startswith('nga_tid') else 0) + (1 if 'latest' in b else 0)
                if key not in files or _pref(p) > _pref(files[key]):
                    files[key] = p
    return files


def build_title_map():
    """从用户抓取文件里反查 tid -> 主题标题"""
    titles = {}
    for d in SCAN_DIRS:
        for p in glob.glob(os.path.join(d, 'nga_user_*.txt')):
            try:
                for line in open(p, encoding='utf-8'):
                    m = re.match(r'^=== 主题 tid=(\d+) \| (.*?)===\s*$', line.rstrip())
                    if m:
                        t = re.sub(r'（该用户.*$', '', m.group(2)).strip()
                        titles.setdefault(m.group(1), t)
            except Exception:
                pass
    return titles


def extract_links(uid):
    """提取你和每个对象的交锋原文：(tid, 标题, 对方uid, 对方原话, 你的回应)"""
    links = []
    tmap = build_title_map()
    for key, p in sorted(find_my_threads(uid).items()):
        txt = open(p, encoding='utf-8').read()
        mt = re.search(r'\[0楼\]\s+(.+?)\s+\(uid=(\d+)\)', txt)
        title = _clean(mt.group(1)) if mt else key
        if title in ('?', '') or title == key:
            title = tmap.get(key, key)
        blocks = re.split(r'^\[(\d+)楼\]\s+(.+?)\s+\(uid=(\d+)\)', txt, flags=re.M)
        for i in range(1, len(blocks), 4):
            u, body = blocks[i + 2], blocks[i + 3]
            if u != uid:
                continue
            my = re.sub(r'\[quote\].*?\[/quote\]', '', body, flags=re.S)
            my = re.sub(r'\[b\]Reply to.*?\[/b\]', '', my, flags=re.S)
            my = _clean(my)
            seen = set()
            for q in re.findall(r'\[quote\](.*?)\[/quote\]', body, re.S):
                qm = re.search(r'Post by \[uid=(\d+)\]', q)
                if not qm:
                    continue
                tu = qm.group(1)
                if tu == uid or tu in seen:
                    continue
                seen.add(tu)
                his = _clean(re.sub(r'^.*?\):\s*', '', q, count=1, flags=re.S))
                if his or my:
                    links.append((key, title, tu, his[:300], my[:400]))
            for mm in re.finditer(r'Post by \[uid=(\d+)\]', body):
                tu = mm.group(1)
                if tu != uid and tu not in seen:
                    seen.add(tu)
                    if my:
                        links.append((key, title, tu, '', my[:400]))
    return links


def cmd_links(args):
    rows = load()
    name_map = build_name_map()
    links = extract_links(args.uid)
    if not links:
        print('未提取到交锋记录。')
        return
    by_t = {}
    for tid, title, tu, his, my in links:
        by_t.setdefault((tid, title, tu), []).append((his, my))
    print(f'共 {len(by_t)} 段交锋（涉及 {len({k[2] for k in by_t})} 个对象）\n')
    for (tid, title, tu), items in by_t.items():
        print(f'=== [{tid}] {title[:40]} → {name_map.get(tu, tu)}({tu}) ===')
        for his, my in items:
            if his:
                print(f'  他：{his[:220]}')
            print(f'  我：{my[:260]}')
        print()
    if args.save:
        exist = {(r['uid'], r.get('source')) for r in rows if r.get('kind') == 'encounter'}
        added = skipped = 0
        for (tid, title, tu), items in by_t.items():
            if (tu, f'thread:{tid}') in exist:
                skipped += 1
                continue
            his = items[0][0]
            my = ' ｜ '.join(x[1] for x in items if x[1])[:600]
            row = {'id': next_id(rows, 'encounter'), 'ts': str(datetime.date.today()),
                   'kind': 'encounter', 'uid': tu, 'name': name_map.get(tu, ''),
                   'evidence': 'A', 'source': f'thread:{tid}', 'tags': ['交锋对象'],
                   'text': f'在《{title[:30]}》帖内交锋。对方原话：{his[:200] or "(未留存)"}',
                   'reaction': f'我的回应：{my}', 'note': ''}
            rows.append(row)
            added += 1
        save(rows)
        print(f'已写入台账 {added} 条 encounter 记录（跳过重复 {skipped} 条）')


def cmd_targets_threads(args):
    """反向模式：以该 uid 为楼主的帖子里，提取交锋对象"""
    rows = load()
    ledger = {r['uid']: (r.get('name') or '') for r in rows}
    name_map = build_name_map()
    tmap = build_title_map()

    def nm(u):
        return name_map.get(u) or ledger.get(u) or ''

    files = find_my_threads(args.uid)
    if not files:
        print('未找到以该 uid 为楼主的帖子抓取文件。')
        return
    print(f'以 uid={args.uid} 为楼主的帖子：{len(files)} 个\n')
    for key, p in sorted(files.items()):
        txt = open(p, encoding='utf-8').read()
        mt = re.search(r'\[0楼\]\s+(.+?)\s+\(uid=(\d+)\)', txt)
        title = _clean(mt.group(1)) if mt else key
        if title in ('?', '') or title == key:
            title = tmap.get(key, key)
        blocks = re.split(r'^\[(\d+)楼\]\s+(.+?)\s+\(uid=(\d+)\)', txt, flags=re.M)
        speakers, direct, replied_me = {}, {}, {}
        for i in range(1, len(blocks), 4):
            u, body = blocks[i + 2], blocks[i + 3]
            speakers[u] = speakers.get(u, 0) + 1
            if u == args.uid:
                for mm in re.finditer(r'Post by \[uid=(\d+)\]', body):
                    direct[mm.group(1)] = direct.get(mm.group(1), 0) + 1
            elif f'Post by [uid={args.uid}]' in body:
                replied_me[u] = replied_me.get(u, 0) + 1
        total = len(re.findall(r'^\[\d+楼\]', txt, flags=re.M))
        print(f'=== [{key}] {title[:46]} ===')
        print(f'    全帖 {total} 楼 / 参与 {len(speakers)} 人 / 你 {speakers.get(args.uid, 0)} 楼')
        if direct:
            print('  ▸ 你直接回复过的人（精确交锋对象）：')
            for u, c in sorted(direct.items(), key=lambda x: -x[1]):
                print(f'      {u:<10}{nm(u)[:14]:<16}{c}次  {"✓台账" if u in ledger else ""}')
        if replied_me:
            print('  ▸ 在帖里点名回复你的人：')
            for u, c in sorted(replied_me.items(), key=lambda x: -x[1]):
                print(f'      {u:<10}{nm(u)[:14]:<16}{c}次  {"✓台账" if u in ledger else ""}')
        top = sorted(((u, c) for u, c in speakers.items() if u != args.uid), key=lambda x: -x[1])[:12]
        print('  ▸ 帖内发言最多的人 TOP12：')
        for u, c in top:
            print(f'      {u:<10}{nm(u)[:14]:<16}{c}楼 {"✓台账" if u in ledger else ""}')
        print()


def cmd_targets(args):
    if getattr(args, 'threads', False):
        return cmd_targets_threads(args)
    """从自己的抓取文件里提取「互动对象」——即被引用/被回复过的 uid"""
    rows = load()
    ledger = {}
    for r in rows:
        if r.get('name'):
            ledger[r['uid']] = r['name']
    paths = []
    for d in SCAN_DIRS:
        paths += glob.glob(os.path.join(d, f'nga_user_{args.uid}_*.txt'))
    if not paths:
        print(f'未找到 uid={args.uid} 的抓取文件。先跑：'
              f'python "<skill>\\nga_scraper.py" user {args.uid} --deep -o knowledge\\nga\\nga_user_{args.uid}_deep.txt')
        return
    targets, own = {}, []
    for path in paths:
        txt = open(path, encoding='utf-8').read()
        parts = re.split(r'^=== 主题 tid=(\d+) \| (.*?)===', txt, flags=re.M)
        for i in range(1, len(parts), 3):
            tid, title, body = parts[i], parts[i + 1], parts[i + 2]
            for m in re.finditer(r'Post by \[uid=(\d+)\]([^\[]*)\[/uid\]', body):
                u, n = m.group(1), m.group(2).strip()
                d = targets.setdefault(u, {'name': n, 'count': 0, 'tids': set()})
                d['count'] += 1
                d['tids'].add(tid)
                if n:
                    d['name'] = n
            clean = re.sub(r'\[quote\].*?\[/quote\]', '', body, flags=re.S)
            clean = re.sub(r'\[b\]Reply to .*?\[/b\]', '', clean, flags=re.S)
            for ln in clean.split('\n'):
                s = ln.strip()
                if len(s) > 12 and not s.startswith('['):
                    own.append((tid, title[:22], s[:88]))
                    break
    print(f'扫描 {len(paths)} 个文件，提取到 {len(targets)} 个互动对象\n')
    print(f'{"uid":<10}{"昵称":<16}{"次数":>4}  台账  涉及主题')
    for u, d in sorted(targets.items(), key=lambda x: -x[1]['count']):
        mark = '✓ 已有' if u in ledger else '—'
        tids = '、'.join(sorted(d['tids'])[:4])
        print(f'{u:<10}{d["name"][:15]:<16}{d["count"]:>4}  {mark:<5} {tids}')
    print(f'\n---- 你在这些主题里的发言样本（判断是交锋还是闲聊）----')
    for tid, title, s in own[:args.samples]:
        print(f'[{tid}] {title} :: {s}')


def cmd_list(args):
    rows = load()
    uids = sorted({r['uid'] for r in rows})
    print(f'台账共 {len(rows)} 条记录 / {len(uids)} 个 uid\n')
    print(f'{"uid":<10}{"昵称":<14}{"主题":>5}  观察  最近  source')
    for uid in uids:
        prof, others = merged(rows, uid)
        threads = max([p.get('threads', 0) for p in prof], default=0)
        name = next((r.get('name') for r in prof + others if r.get('name')), '')
        last = max([r.get('ts', '') for r in prof + others], default='')
        src = ','.join(p['source'].split('/')[-1][:26] for p in prof[:2])
        print(f'{uid:<10}{name:<14}{threads:>5}  {len(others):>4}  {last}  {src}')


def cmd_render(args):
    rows = load()
    uids = sorted({r['uid'] for r in rows})
    out = ['# NGA 用户台账', '',
           f'> 自动生成于 {datetime.date.today()}，请勿手改——改数据请用 `scripts/nga_ledger.py add` 或编辑 `ledger/observations.jsonl`。',
           '> 用途：一次判定、长期复用；再次遇到同一 uid 时秒查，不必重抓 200–300 个主题。',
           '> 边界：仅记录公开论坛的公开发言；不判粉籍（证据不足时只标话术）；不做人肉、不用于攻击个人。', '',
           f'共 {len(uids)} 个 uid · {len(rows)} 条记录', '']
    for uid in uids:
        out.append(fmt_person(rows, uid, verbose=False))
        out.append('')
    os.makedirs(os.path.dirname(VIEW), exist_ok=True)
    open(VIEW, 'w', encoding='utf-8').write('\n'.join(out))
    print(f'已生成 {VIEW}（{len(uids)} 个 uid）')


def main():
    p = argparse.ArgumentParser(prog='nga_ledger')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('scan'); s.add_argument('--rebuild', action='store_true')
    s = sub.add_parser('import-manual'); s.add_argument('file')
    a = sub.add_parser('add')
    a.add_argument('--uid', required=True); a.add_argument('--name'); a.add_argument('--kind', default='encounter')
    a.add_argument('--text', required=True); a.add_argument('--reaction'); a.add_argument('--tags')
    a.add_argument('--evidence', default='A'); a.add_argument('--source'); a.add_argument('--date')
    sh = sub.add_parser('show'); sh.add_argument('key')
    tg = sub.add_parser('targets'); tg.add_argument('uid'); tg.add_argument('--samples', type=int, default=15)
    tg.add_argument('--threads', action='store_true', help='反向模式：从该 uid 为楼主的帖子里提取交锋对象')
    lk = sub.add_parser('links'); lk.add_argument('uid'); lk.add_argument('--save', action='store_true')
    sub.add_parser('list')
    sub.add_parser('render')
    args = p.parse_args()
    {'scan': cmd_scan, 'import-manual': cmd_import_manual, 'add': cmd_add,
     'show': cmd_show, 'list': cmd_list, 'render': cmd_render, 'targets': cmd_targets,
     'links': cmd_links}[args.cmd](args)


if __name__ == '__main__':
    main()
