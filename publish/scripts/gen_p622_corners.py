# -*- coding: utf-8 -*-
"""
6:22.091 原型车视频采样 → 三弯弯速定位
输入：publish/assets/_p622/ocr.txt（batch-ocr -Label 输出：文件名 时间 速度）
流程：解析 Laptime 与速度 → 速度积分成距离 → 找 0.53/7.4/8.6km 三弯弯心速度
"""
import re
import numpy as np

OCR = r'D:\Project\dsh_rally_cars\publish\assets\_p622\ocr.txt'

rows = []
with open(OCR, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        # 文件名 sNNN.jpg | 时间(MM:SS.xx 或 乱码) | 速度数字
        name = parts[0]
        # 时间：找 MM:SS 模式（OCR 可能把冒号读成全角/逗号）
        tm = None
        m = re.search(r'(\d{1,2})[:：,;](\d{2})[.,]?(\d*)', line)
        if m:
            mm, ss = int(m.group(1)), int(m.group(2))
            frac = float('0.' + m.group(3)) if m.group(3) else 0.0
            tm = mm * 60 + ss + frac
        # 速度：时间之后最后一个 2-3 位数字（排除 20832、22.091 等）
        v = None
        for tok in parts[2:]:
            tok = re.sub(r'[^\d]', '', tok)
            if tok.isdigit() and 20 <= int(tok) <= 350:
                v = int(tok)
                break
        if tm is not None and v is not None:
            rows.append((name, tm, v))
        else:
            rows.append((name, tm, v))

ok = [r for r in rows if r[1] is not None and r[2] is not None]
print(f'解析：{len(rows)} 行，可用 {len(ok)} 行')
ok.sort(key=lambda r: r[1])

ts = np.array([r[1] for r in ok])
vs = np.array([r[2] for r in ok], dtype=float)

# 简单清洗：速度连续性与孤点剔除（与相邻差 >60km/h 且两侧一致则视为误读）
v_fixed = vs.copy()
for i in range(1, len(vs) - 1):
    if abs(vs[i] - vs[i-1]) > 60 and abs(vs[i] - vs[i+1]) > 60:
        v_fixed[i] = (vs[i-1] + vs[i+1]) / 2
vs = v_fixed

# 速度积分 → 距离
s = np.zeros_like(ts)
for i in range(1, len(ts)):
    s[i] = s[i-1] + (vs[i-1] + vs[i]) / 2 / 3.6 * (ts[i] - ts[i-1])
print(f'圈速段距离: {s[-1]:.0f} m ({s[-1]/20832*100:.1f}% 官方长度)')

# 三弯定位（量产口径位置 ±120m 找局部最小）
targets = [(530, '高速弯0.53km'), (7400, '低速弯7.4km'), (8590, 'Kesselchen8.6km')]
print(f'\n{"弯":<16}{"位置":>8}{"弯速":>8}{"时间":>8}')
for tgt, label in targets:
    lo, hi = tgt - 120, tgt + 120
    m = (s >= lo) & (s <= hi)
    if not np.any(m):
        print(f'{label:<16} 无数据')
        continue
    idx = np.where(m)[0]
    imin = idx[np.argmin(vs[idx])]
    print(f'{label:<16}{s[imin]:>8.0f}m{vs[imin]:>8.1f}km/h{ts[imin]:>8.1f}s')

# 也输出三弯附近 ±300m 的速度谷全表供人工核对
print('\n全圈主要速度谷（<140km/h 或相邻谷）：')
for i in range(2, len(vs) - 2):
    if vs[i] <= vs[i-1] and vs[i] <= vs[i-2] and vs[i] <= vs[i+1] and vs[i] <= vs[i+2] and vs[i] < 300:
        print(f'  s={s[i]:6.0f}m  v={vs[i]:5.1f}  t={ts[i]:6.1f}s')
