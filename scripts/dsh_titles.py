# -*- coding: utf-8 -*-
"""快速列出某工程目录下所有 DSH 会话的标题（只解压前 200KB）。"""
import zstandard, json, glob, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

D = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\AegisH\.dsh\sessions\--D-Project-dsh_rally_cars--"
kw = sys.argv[2] if len(sys.argv) > 2 else ''

fs = sorted(glob.glob(os.path.join(D, '**', 'session*.jsonl.zstd'), recursive=True))
print(f'会话文件 {len(fs)} 个 in {D}\n')
rows = []
for p in fs:
    title = ''
    try:
        dctx = zstandard.ZstdDecompressor()
        with open(p, 'rb') as f:
            chunk = dctx.stream_reader(f).read(300000).decode('utf-8', 'replace')
        for ln in chunk.split('\n'):
            if '"session/title"' in ln:
                try:
                    j = json.loads(ln)
                    d = j.get('data') or {}
                    title = d.get('title') or d.get('text') or title
                except Exception:
                    pass
    except Exception as e:
        title = f'<解压失败 {e}>'
    rows.append((title, p))

for t, p in rows:
    if kw and kw not in t:
        continue
    sid = os.path.basename(os.path.dirname(p))
    print(f'{t[:58]:<60} {sid}')
print(f'\n共 {len(rows)} 个会话，其中标题含「{kw}」的如上' if kw else '')
