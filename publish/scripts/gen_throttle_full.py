# -*- coding: utf-8 -*-
"""
三车全圈 BRAKE/ACCELERATOR 条高统计（纯像素，零 token）
- 遍历三车全部逐帧图，量红条/绿条高度
- 统计：刹车帧占比、油门帧占比、并存帧占比、交替频率、油门均值
"""
import csv
import glob
import os
import re

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

REG = {
    'u9x':  {'red': (1460, 855, 1520, 1060), 'green': (1722, 855, 1785, 1060)},
    'su7':  {'red': (1553, 798, 1668, 1042), 'green': (1745, 798, 1862, 1042)},
    'pot':  {'red': (1553, 798, 1668, 1042), 'green': (1745, 798, 1862, 1042)},
}

def analyze(car, frames):
    reg = REG[car]
    brakes, accels = [], []
    laps = []
    for lap, f in frames:
        img = Image.open(f)
        b = bar_h(img, reg['red'], 'red')
        a = bar_h(img, reg['green'], 'green')
        laps.append(lap)
        brakes.append(b)
        accels.append(a)
    b = np.array(brakes)
    a = np.array(accels)
    n = len(b)
    brake_on = (b > 8).sum()
    accel_on = (a > 8).sum()
    coexist = ((b > 8) & (a > 8)).sum()
    # 交替频率：刹车或油门状态切换次数（>8 阈值）
    switches = 0
    prev = 'none'
    for i in range(n):
        if b[i] > 8 and a[i] > 8:
            state = 'both'
        elif b[i] > 8:
            state = 'brake'
        elif a[i] > 8:
            state = 'accel'
        else:
            state = 'none'
        if state != prev and prev != 'none':
            switches += 1
        prev = state
    return {
        'car': car, 'n': n,
        'brake%': brake_on / n * 100,
        'accel%': accel_on / n * 100,
        'coexist%': coexist / n * 100,
        'switches': switches, 'switch_rate': switches / n * 1000,
        'accel_mean_on': a[a > 8].mean() if accel_on > 0 else 0,
    }

# 帧列表（带 lap 时间）
def u9x_frames():
    files = sorted(glob.glob(r'G:\Capture\youtube\U9X\*.jpg'))
    out = []
    for f in files:
        m = re.search(r'(\d{2})(\d{2})(\d{2})\.(\d{3})\.jpg$', f)
        vt = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000
        out.append((round(vt - 1.28, 3), f))
    return out

def su7_frames():
    base = os.path.join(ROOT, 'publish', 'assets', '_su7f')
    files = sorted(glob.glob(os.path.join(base, 'f*.jpg')))
    out = []
    for f in files:
        n = int(re.search(r'f(\d+)\.jpg', os.path.basename(f)).group(1))
        out.append((round(n/25 - 2.08, 3), f))
    return out

def pot_frames():
    files = sorted(glob.glob(r'G:\Capture\youtube\Xiaomi SU7 Ultra Prototype\*.jpg'))
    out = []
    for f in files:
        m = re.search(r'(\d{2})(\d{2})(\d{2})\.(\d{3})\.jpg$', f)
        vt = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000
        out.append((round(vt - 1.77, 3), f))
    return out

print('=== 三车全圈油门/刹车条高统计（5fps 降采样） ===')
results = []
for car, frames in [('u9x', u9x_frames()[::5]), ('su7', su7_frames()[::5]), ('pot', pot_frames()[::5])]:
    r = analyze(car, frames)
    results.append(r)
    print('%-4s 帧%d | 刹车帧 %.1f%% | 油门帧 %.1f%% | 并存帧 %.1f%% | 切换 %d 次(%.0f次/10s) | 给油时平均开度 %.0f%%' % (
        r['car'], r['n'], r['brake%'], r['accel%'], r['coexist%'], r['switches'], r['switch_rate']/10, r['accel_mean_on']))
