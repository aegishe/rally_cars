# -*- coding: utf-8 -*-
"""环塔 T2 悬架形式 × 赛段成绩对照账
数据源：offroad/环塔2026_赛段成绩.csv
输出：各悬架形式组在已知长度赛段（SS3 469km / SS4 91km / SS5 281km / SS9 354km）的平均速度对比
说明：样本小（每形式 1-3 台），不做回归，只做同赛段对照账。
"""
import csv
import io
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CSV_PATH = r"D:\Project\dsh_rally_cars\offroad\环塔2026_赛段成绩.csv"

STAGE_KM = {"SS3": 469, "SS4": 91, "SS5": 281, "SS9": 354}

SUSP_MAP = [
    ("全整体桥", ["212 T01"]),
    ("后整体桥", ["火炮V6", "坦克300 Hi4-T"]),
    ("全独立", ["坦克700 Hi4-T", "坦克700", "猛士M817"]),
    ("全独立+空悬", ["猛士M817"]),
]
# 车型 -> 悬架形式
CAR_SUSP = {}
for form, cars in SUSP_MAP:
    for c in cars:
        CAR_SUSP[c] = form

def parse_hms(t):
    t = (t or "").strip()
    if not t or ":" not in t:
        return None
    parts = t.split(":")
    try:
        parts = [float(p) for p in parts]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except ValueError:
        return None

# car -> {stage: seconds}
stage_time = defaultdict(dict)
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

for row in rows[2:]:
    if len(row) < 8 or not row[0].strip():
        continue
    stage = row[0].strip()
    carno = row[2].strip()
    car = row[4].strip()
    t = parse_hms(row[6])
    if stage.startswith("SS") and carno and car:
        stage_time[carno] = stage_time[carno] or {}
        stage_time[carno]["_car"] = car
        if t:
            stage_time[carno][stage] = t

print("车号 | 车型 | SS3 | SS4 | SS5 | SS9")
print("---|---|---|---|---|---")
for carno in sorted(stage_time, key=lambda x: int(x) if x.isdigit() else 999):
    d = stage_time[carno]
    car = d.get("_car", "?")
    line = f"{carno} | {car}"
    for st in ["SS3", "SS4", "SS5", "SS9"]:
        sec = d.get(st)
        if sec and st in STAGE_KM:
            v = STAGE_KM[st] / (sec / 3600)
            line += f" | {v:.1f}km/h"
        elif sec:
            line += f" | ({sec/60:.0f}min)"
        else:
            line += " | —"
    print(line)

# 分组汇总
print()
print("=== 悬架形式 × 赛段平均速度（只含该赛段完赛车）===")
groups = defaultdict(lambda: defaultdict(list))
for carno, d in stage_time.items():
    car = d.get("_car", "")
    form = CAR_SUSP.get(car, "其他")
    for st, km in STAGE_KM.items():
        sec = d.get(st)
        if sec:
            groups[form][st].append(km / (sec / 3600))

for form in ["全整体桥", "后整体桥", "全独立"]:
    for st, km in STAGE_KM.items():
        vs = groups[form].get(st, [])
        if vs:
            avg = sum(vs) / len(vs)
            print(f"{form} {st}: n={len(vs)} 平均 {avg:.1f} km/h（{'/'.join(f'{v:.1f}' for v in vs)}）")
    print()
