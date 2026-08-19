"""
5fps 重采数据清洗 (帧号口径 v3, 配置驱动)
配置: track/scripts/resample_config.json
时间 = (frame_start + 5*(n-1)) / 25 + lap_offset  —— 与手工时间戳同口径
提取: 连续性优先 (修复 OCR 截断如 022->122, 10->210, 多候选取最接近前一帧)
"""
import csv
import json
import re
import numpy as np

with open(r'D:\Project\dsh_rally_cars\track\scripts\resample_config.json', 'r', encoding='utf-8') as f:
    CFG = json.load(f)

BASE = CFG['out_base']
FPS_DIV = CFG.get('fps_div', 5)
SEGS = [(f"{s['car']}_{s['name']}", s['frame_start'], s['car']) for s in CFG['segments']]
LAP_OFFSET = CFG['lap_offset']

def load_manual(path):
    ts, vs = [], []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            ts.append(float(row[0]))
            vs.append(float(row[1]))
    return np.array(ts), np.array(vs)

t_man_u, v_man_u = load_manual(r'D:\Project\dsh_rally_cars\track\U9X_power_analysis.csv')
t_man_s, v_man_s = load_manual(r'D:\Project\dsh_rally_cars\track\SU7_power_analysis.csv')

def parse_ocr(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 2:
                continue
            m = re.match(r'f_(\d+)\.jpg', parts[0])
            if not m:
                continue
            nums = [int(x) for x in re.findall(r'\d{1,3}', parts[1])]
            rows.append({'n': int(m.group(1)), 'nums': nums, 'raw': parts[1]})
    out = []
    prev = None
    for r in rows:
        cands = [x for x in r['nums'] if 10 <= x <= 400]
        if not cands:
            out.append((r['n'], None))
            continue
        if prev is None:
            big = [x for x in cands if x >= 60]
            v = max(big) if big else (max(cands) + 200 if max(cands) < 60 else max(cands))
        else:
            # 候选 + 百位截断修复 (OCR 丢 '2' 百位: 10=210, 96=296)
            cands2 = []
            for x in cands:
                cands2.append(x)
                if x < 100 and 100 + x <= 400 and abs(100 + x - prev) < 60:
                    cands2.append(100 + x)
                if x < 100 and 200 + x <= 400 and abs(200 + x - prev) < 60:
                    cands2.append(200 + x)
            v = min(cands2, key=lambda x: abs(x - prev))
        out.append((r['n'], v))
        prev = v
    return out

all_res = {}
for name, fr0, car in SEGS:
    rows = parse_ocr(fr'{BASE}\{name}.txt')
    t = np.array([(fr0 + FPS_DIV * (n - 1)) / 25.0 for n, v in rows])
    sp = np.array([v if v is not None else np.nan for n, v in rows], dtype=float)
    # 孤立跳变剔除 (相邻有效帧间 >45km/h/s)
    valid = ~np.isnan(sp)
    for i in range(1, len(sp) - 1):
        if valid[i] and (valid[i-1] or valid[i+1]):
            ref = sp[i-1] if valid[i-1] else sp[i+1]
            if abs(sp[i] - ref) > 12:  # 0.2s 内 12km/h = 16.7m/s2 不物理
                sp[i] = np.nan
    all_res[name] = {'t': t, 'sp': sp, 'car': car}
    n_valid = np.sum(~np.isnan(sp))
    print(f"{name}: {len(rows)} 帧, 有效 {n_valid} ({n_valid/len(rows)*100:.0f}%)")

def best_offset(t_ocr, v_ocr, t_man, v_man, dmax=0.5, step=0.04):
    best = None
    for d in np.arange(-dmax, dmax + 0.001, step):
        v_at = np.interp(t_man + d, t_ocr, v_ocr)
        m = ~np.isnan(v_at)
        if np.sum(m) < 5:
            continue
        rmse = np.sqrt(np.mean((v_at[m] - v_man[m])**2))
        if best is None or rmse < best[0]:
            best = (rmse, d)
    return best

print("\n=== 与手工数据一致性检查 (仅报告, 不做平移; 相位差属正常) ===")
offsets = {}
for name, fr0, car in SEGS:
    d = all_res[name]
    t_man = t_man_u if car == 'u9x' else t_man_s
    v_man = v_man_u if car == 'u9x' else v_man_s
    m_seg = (t_man >= fr0 / 25 - 2) & (t_man <= (fr0 + FPS_DIV * 300) / 25 + 2)
    res = best_offset(d['t'], d['sp'], t_man[m_seg], v_man[m_seg])
    if res is None:
        print(f"  {name}: 有效点不足")
        offsets[name] = 0.0
        continue
    rmse, off = res
    offsets[name] = 0.0  # 帧号口径, 不平移
    print(f"  {name}: 建议偏移 {off:+.2f}s (RMSE={rmse:.1f}, 相位差预期值, 不应用)")

print("\n=== 保存校准后 CSV ===")
# 时间口径: 手工时间戳 = 帧号/25 + lap_offset (配置文件, 已按 Laptime 前缓冲校准)
for car in ['u9x', 'su7']:
    rows_out = []
    for name, fr0, c in SEGS:
        if c != car:
            continue
        d = all_res[name]
        for i in range(len(d['t'])):
            if not np.isnan(d['sp'][i]):
                rows_out.append((d['t'][i] + LAP_OFFSET[car], d['sp'][i]))
    rows_out.sort(key=lambda x: x[0])
    out = fr'D:\Project\dsh_rally_cars\track\{car}_5fps.csv'
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['t_s', 'speed_kmh'])
        for t, v in rows_out:
            w.writerow([f"{t:.2f}", f"{v:.1f}"])
    print(f"  {out}: {len(rows_out)} 点")
