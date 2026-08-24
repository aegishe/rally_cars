# -*- coding: utf-8 -*-
"""
BRAKE 红条 / ACCELERATOR 绿条 批量定量（纯像素，零 token）
- 每车界面布局不同，区域自动探测（限右下角）
- 输出 CSV：t, brake%, accel%（高度=条顶部到区域基线/满条高度）
"""
import csv
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

def detect_bars(img, x_lo=1350, y_lo=700):
    a = np.asarray(img.convert('RGB'), dtype=np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 100) & (r - g > 35) & (r - b > 35)
    green = (g > 140) & (r < 160) & (b < 110)
    red[:, :x_lo] = False
    green[:, :x_lo] = False
    red[:y_lo, :] = False
    green[:y_lo, :] = False
    out = {}
    for name, mask in [('brake', red), ('accel', green)]:
        ys, xs = np.where(mask)
        if len(ys) > 20:
            out[name] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return out

def bar_fill(img, box):
    """box=(x0,y0,x1,y1) 条区域：宽度主体列，量条顶部位置"""
    a = np.asarray(img.convert('RGB'), dtype=np.int16)
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    red = (r > 100) & (r - g > 35) & (r - b > 35)
    green = (g > 140) & (r < 160) & (b < 110)
    mask = red if 'brake' in box[2] if False else None  # placeholder
    return None


def main():
    # 直接对单个目录批量：文件名含时间戳（视频时间），输出条高 CSV
    # 简化：探测+条高的帧级函数
    pass


if __name__ == '__main__':
    main()
