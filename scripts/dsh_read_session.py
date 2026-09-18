# -*- coding: utf-8 -*-
"""读取指定 DSH 会话的用户与助手消息全文，输出到文件。"""
import zstandard, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\AegisH\.dsh\sessions\--D-Project-dsh_rally_cars--\session-f4e07a7d-183f-4834-9cfd-7a799bff9721\session.v3.jsonl.zstd"
OUT = r"D:\Project\dsh_rally_cars\.tmp\session_read.txt"


def flat(x):
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        for k in ('text', 'content', 'message', 'value'):
            if k in x:
                v = flat(x[k])
                if v:
                    return v
        return ''
    if isinstance(x, list):
        return '\n'.join(v for v in (flat(i) for i in x) if v)
    return ''


def text_of(d):
    for k in ('content', 'text', 'message'):
        if k in d:
            v = flat(d[k])
            if v:
                return v
    return ''


dctx = zstandard.ZstdDecompressor()
raw = dctx.stream_reader(open(P, 'rb')).read().decode('utf-8', 'replace')
recs = []
for ln in raw.split('\n'):
    ln = ln.strip()
    if ln:
        try:
            recs.append(json.loads(ln))
        except Exception:
            pass

out = [f'文件 {os.path.basename(P)}', f'记录 {len(recs)} 条', '=' * 70]
for r in recs:
    t = r.get('type')
    d = r.get('data') or {}
    if t == 'user/message':
        src = d.get('source') or {}
        if src.get('kind') != 'user':
            continue
        out += ['', '########## 用户 ##########', text_of(d).strip()]
    elif t == 'assistant/message':
        txt = text_of(d).strip()
        if txt:
            out += ['', '########## 助手 ##########', txt]
    elif t == 'session/title':
        out.append(f'--- 标题: {flat(d.get("title") or d.get("text") or "")} ---')
    elif t in ('tool/call', 'tool/call/start'):
        nm = flat(d.get('name') or d.get('tool') or '')
        out.append(f'  [工具] {nm}')
out.append('\n' + '=' * 70 + ' 结束')

txt = '\n'.join(out)
open(OUT, 'w', encoding='utf-8').write(txt)
print(f'written {len(txt)} chars -> {OUT}')
print(txt[:1200])
