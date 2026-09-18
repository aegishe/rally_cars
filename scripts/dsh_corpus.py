# -*- coding: utf-8 -*-
"""DSH 会话语料探针：解压 session.jsonl.zstd，统计用户发言规模与形态。

用法：
  python dsh_corpus.py probe            # 看单个会话的结构
  python dsh_corpus.py count            # 全量统计用户消息条数与字数
  python dsh_corpus.py export <out>     # 导出全部用户发言为语料
"""
import os, sys, io, json, glob, zstandard

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SESS = r"C:\Users\AegisH\.dsh\sessions"


def read_jsonl(path):
    dctx = zstandard.ZstdDecompressor()
    with open(path, 'rb') as f:
        raw = dctx.stream_reader(f).read()
    out = []
    for ln in raw.decode('utf-8', 'replace').split('\n'):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def all_files():
    fs = glob.glob(os.path.join(SESS, '**', 'session*.jsonl.zstd'), recursive=True)
    return sorted(set(fs))


def user_msgs(recs):
    """抽出真正的用户发言：type=user/message 且 data.source.kind == 'user'"""
    msgs = []
    for r in recs:
        if r.get('type') != 'user/message':
            continue
        d = r.get('data') or {}
        src = d.get('source') or {}
        if src.get('kind') != 'user':
            continue  # 插件/系统注入（审批策略变更、runtime context、skill 目录等）
        c = d.get('content')
        if isinstance(c, list):
            c = '\n'.join(x.get('text', '') for x in c if isinstance(x, dict))
        if not isinstance(c, str):
            continue
        c = c.strip()
        if len(c) < 2 or c.startswith('<system-reminder>'):
            continue
        msgs.append(c)
    return msgs


def cmd_probe():
    fs = all_files()
    print(f'session.jsonl.zstd 文件数 {len(fs)}')
    p = fs[0]
    print(f'\n样例：{p}\n')
    recs = read_jsonl(p)
    print(f'记录数 {len(recs)}')
    ums = [r for r in recs if r.get('type') == 'user/message']
    print(f'\nuser/message 记录 {len(ums)} 条，结构样例：')
    for r in ums[:2]:
        print(json.dumps(r, ensure_ascii=False)[:800])
        print('---')
    ms = user_msgs(recs)
    print(f'\n成功提取用户发言 {len(ms)} 条：')
    for m in ms[:6]:
        print(f'  · {m[:140]}')


def cmd_count():
    fs = all_files()
    total, chars = 0, 0
    per_proj = {}
    for i, p in enumerate(fs):
        proj = os.path.basename(os.path.dirname(os.path.dirname(p)))
        try:
            ms = user_msgs(read_jsonl(p))
        except Exception:
            continue
        total += len(ms)
        chars += sum(len(m) for m in ms)
        d = per_proj.setdefault(proj, [0, 0])
        d[0] += len(ms)
        d[1] += sum(len(m) for m in ms)
        if (i + 1) % 50 == 0:
            print(f'  ...已处理 {i+1}/{len(fs)}，累计 {total} 条', flush=True)
    print(f'\n==== 全量结果 ====')
    for k, v in sorted(per_proj.items(), key=lambda x: -x[1][0]):
        print(f'{k:<32}{v[0]:>6} 条{v[1]:>10,} 字符')
    print(f'{"合计":<32}{total:>6} 条{chars:>10,} 字符')


def cmd_export(out):
    fs = all_files()
    rows = []
    for p in fs:
        proj = os.path.basename(os.path.dirname(os.path.dirname(p))).strip('-').replace('-', '/')
        try:
            for m in user_msgs(read_jsonl(p)):
                if len(m) >= 8:
                    rows.append((proj, m))
        except Exception:
            continue
    with open(out, 'w', encoding='utf-8') as f:
        for proj, m in rows:
            f.write(f'[{proj}]\n{m}\n\n---\n\n')
    print(f'导出 {len(rows)} 条用户发言 → {out}')


def cmd_find(kw):
    """按标题/内容关键词查找会话"""
    hit = 0
    for p in all_files():
        try:
            recs = read_jsonl(p)
        except Exception:
            continue
        title = ''
        for r in recs:
            if r.get('type') == 'session/title':
                d = r.get('data') or {}
                title = d.get('title') or d.get('text') or title
        ms = user_msgs(recs)
        blob = title + ' ' + ' '.join(ms)
        if kw in blob:
            hit += 1
            proj = os.path.basename(os.path.dirname(os.path.dirname(p)))
            print(f'[{hit}] {proj}')
            print(f'    title: {title}')
            print(f'    path : {p}')
            print(f'    用户消息 {len(ms)} 条')
            for m in ms[:3]:
                print(f'      · {m[:90]}')
            print()
    print(f'匹配 {hit} 个会话')


if __name__ == '__main__':
    a = sys.argv[1:] or ['probe']
    if a[0] == 'probe':
        cmd_probe()
    elif a[0] == 'count':
        cmd_count()
    elif a[0] == 'export':
        cmd_export(a[1] if len(a) > 1 else 'dsh_user_corpus.txt')
    elif a[0] == 'find':
        cmd_find(a[1] if len(a) > 1 else '')
