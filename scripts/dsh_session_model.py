# -*- coding: utf-8 -*-
"""查指定会话的模型与运行参数。"""
import zstandard, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\AegisH\.dsh\sessions\--D-Project-dsh_rally_cars--\session-f4e07a7d-183f-4834-9cfd-7a799bff9721\session.v3.jsonl.zstd"

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

print(f'记录 {len(recs)} 条\n')
seen = set()
for r in recs:
    t = r.get('type') or ''
    d = r.get('data') or {}
    if t in ('session', 'request/header', 'turn/start', 'model', 'session/start'):
        key = t
        if key in seen:
            continue
        seen.add(key)
        print(f'--- {t} ---')
        print(json.dumps(d, ensure_ascii=False)[:1200])
        print()

# 兜底：全文件搜 model 关键字
print('=== 含 model/provider 字段的记录 ===')
n = 0
for r in recs:
    s = json.dumps(r, ensure_ascii=False)
    if '"model"' in s or '"provider"' in s:
        n += 1
        if n <= 6:
            print(f'[{r.get("type")}] {s[:400]}')
print(f'共 {n} 条')
