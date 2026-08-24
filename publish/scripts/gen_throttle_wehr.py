# -*- coding: utf-8 -*-
"""
Wehrseifen 复合弯段三车 BRAKE/ACCELERATOR 条高对比（纯像素）
- 输出 CSV + 控制台对比表
"""
import csv
import glob
import os
import re
import subprocess

import numpy as np
from PIL import Image

ROOT = r'D:\Project\dsh_rally_cars'

def bar_h(img, box, color):
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert('RGB'), dtype=np.int16)
    sub = a[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    if color == 'red':
        mask = (r > 100) & (r - g > 35) & (r - b > 35)
    else:
        mask = (g > 140) & (r < 160) & (b < 110)
    if mask.sum() < 10:
        return 0.0
    top = np.where(mask.any(axis=1))[0].min()
    return round((y1 - y0 - top) / (y1 - y0) * 100, 1)

# 各车条区域
REG = {
    'u9x':  {'red': (1460, 855, 1520, 1060), 'green': (1722, 855, 1785, 1060)},
    'su7':  {'red': (1553, 798, 1668, 1042), 'green': (1745, 798, 1862, 1042)},
    'pot':  {'red': (1553, 798, 1668, 1042), 'green': (1745, 798, 1862, 1042)},
}

def u9x_frames(t0, t1, step=0.5):
    """U9X PotPlayer 图：视频时间 vt = lap + 1.28，文件名 HHMMSS.mmm"""
    files = sorted(glob.glob(r'G:\Capture\youtube\U9X\*.jpg'))
    idx = {}
    for f in files:
        m = re.search(r'(\d{2})(\d{2})(\d{2})\.(\d{3})\.jpg$', f)
        vt = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000
        idx[round(vt, 3)] = f
    laps = np.arange(t0, t1 + 1e-9, step)
    out = []
    for lap in laps:
        vt = round(lap + 1.28, 3)
        best = min(idx.keys(), key=lambda k: abs(k - vt))
        if abs(best - vt) < 0.1:
            out.append((lap, idx[best]))
    return out

def su7_frames(t0, t1, step=0.5):
    """量产 _su7f 帧：帧号 n → lap = n/25 - 2.08"""
    base = os.path.join(ROOT, 'publish', 'assets', '_su7f')
    laps = np.arange(t0, t1 + 1e-9, step)
    out = []
    for lap in laps:
        n = int(round((lap + 2.08) * 25))
        f = os.path.join(base, f'f{n:05d}.jpg')
        if os.path.exists(f):
            out.append((lap, f))
    return out

def pot_frames(t0, t1, step=0.5):
    """原型 mp4 现截"""
    v = r'G:\Capture\youtube\Xiaomi SU7 Ultra prototype ｜ Official uncut Nürburgring footage [M2zt0yAcplU].mp4'
    laps = np.arange(t0, t1 + 1e-9, step)
    tmpdir = os.path.join(ROOT, 'publish', 'assets', '_thr')
    os.makedirs(tmpdir, exist_ok=True)
    out = []
    for lap in laps:
        tmp = os.path.join(tmpdir, f'p{lap:.1f}.jpg')
        subprocess.run(['ffmpeg', '-y', '-ss', f'{1.77 + lap:.2f}', '-i', v,
                        '-frames:v', '1', '-q:v', '1', tmp], check=True, capture_output=True)
        out.append((lap, tmp))
    return out

def run(car, frames):
    reg = REG[car]
    rows = []
    for lap, f in frames:
        img = Image.open(f)
        b = bar_h(img, reg['red'], 'red')
        a = bar_h(img, reg['green'], 'green')
        rows.append((lap, b, a))
    return rows

# Wehrseifen 段：原型 t=163-179（圈速时间），U9X/量产对齐（各自圈速比例）
# 原型 163-179；量产对应 t≈(163-179)*424.9/382.1 = 181-199；U9X ≈ 179-196
print('=== Wehrseifen 复合弯段 条高对比（brake% / accel%） ===')
print('%-6s | %-22s | %-22s | %-22s' % ('Laptime', 'U9X', '量产', '原型'))
print('       |   brake  accel |   brake  accel |   brake  accel')
res_u = run('u9x', u9x_frames(179, 196, 0.5))
res_s = run('su7', su7_frames(182, 199, 0.5))
res_p = run('pot', pot_frames(163, 179, 0.5))
for i in range(max(len(res_u), len(res_s), len(res_p))):
    def fmt(r):
        if i < len(r):
            lap, b, a = r[i]
            return '%6.1f |  %5.1f %5.1f' % (lap, b, a)
        return '   --   |'
    line = ' '.join(fmt(x) for x in [res_u, res_s, res_p])
    print(line)
