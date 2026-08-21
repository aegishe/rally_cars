# -*- coding: utf-8 -*-
"""
篇2s 弯道截图对比生成器
- 从 corner_comparison.csv 取典型弯道（弯心 s_m）
- 对两车视频截帧：入弯前(-200m) / 弯心 / 出弯(+200m)
- Pillow 拼接为 3列×2行 对比图 + 中文标注
- 视频时间戳口径：U9X 视频时间 = t_u9x + 1.28s（视频 1.28s 过起跑线）；
  SU7 视频时间 = t_su7（视频 0s 即圈速计时 0 点附近，clips 00:00.72=119km/h 与 corner t_su7=0.72 吻合）
用法：python publish/scripts/gen_corner_compare.py
输出：publish/assets/chapter2s-c1/c2/c3-*.png
"""
import csv
import subprocess
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\Project\dsh_rally_cars'
CORNER_CSV = os.path.join(ROOT, 'track', 'corner_comparison.csv')
U9X_VIDEO = r'G:\Capture\youtube\YANGWANG U9 Xtreme ｜ 6_59.157 official laptime ｜ Nordschleife [pcPraRlmi8s].mp4'
SU7_VIDEO = r'G:\Capture\youtube\Xiaomi SU7 Ultra ｜ Official uncut Nürburgring footage [I2EjtbqkZIU].mp4'
OUT_DIR = os.path.join(ROOT, 'publish', 'assets')
TMP_DIR = os.path.join(ROOT, 'publish', 'assets', '_corner_tmp')

U9X_OFFSET = 1.28  # 视频时间 = 圈内时间 + 1.28s（OCR 验证 9 帧速度吻合）
SU7_OFFSET = 2.08  # 视频时间 = 圈内时间 + 2.08s（像素级对齐：视频 9.80s 帧 = clips 00:07.72 截图，mae=0.4）

# (弯心s_m, 图文件名前缀, 标题)
CORNERS = [
    (8590, 'chapter2s-c1-kesselchen', 'Kesselchen 8.6km 极高速弯：SU7 弯心快 15km/h'),
    (7400, 'chapter2s-c2-lowspeed', '低速弯（7.4km）：SU7 弯心 +7km/h'),
    (530,  'chapter2s-c3-highspeed', '高速弯（0.53km）：U9X 弯心 +6km/h 的反例'),
]
OFFSETS_M = [-200, 0, +200]
COL_TITLES = ['入弯前（弯心-200m）', '弯心', '出弯（弯心+200m）']
ROW_NAMES = ['仰望 U9 Xtreme', '小米 SU7 Ultra']

FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
FRAME_W, FRAME_H = 640, 360          # 每帧缩放后尺寸
LABEL_H = 26                          # 每帧底部速度标签高
ROW_H = FRAME_H + LABEL_H
TITLE_H = 40
COL_GAP, ROW_GAP = 4, 4


def load_corner_rows():
    rows = {}
    with open(CORNER_CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            s = int(float(r['s_m']))
            rows[s] = r
    return rows


def ffmpeg_frame(video, t, out_path):
    subprocess.run([
        'ffmpeg', '-y', '-ss', f'{t:.3f}', '-i', video,
        '-frames:v', '1', '-q:v', '2', out_path,
    ], check=True, capture_output=True)


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def make_panel(img, speed_text):
    """帧 + 底部黑底白字标签"""
    panel = Image.new('RGB', (FRAME_W, FRAME_H + LABEL_H), (0, 0, 0))
    panel.paste(img, (0, 0))
    d = ImageDraw.Draw(panel)
    f = font(20)
    tw = d.textlength(speed_text, font=f)
    d.text(((FRAME_W - tw) / 2, FRAME_H + 2), speed_text, fill=(255, 255, 255), font=f)
    return panel


def build_corner_figure(rows, corner_s, out_base, title):
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    grid = []  # (row, col) -> panel
    for ri, (name, video, offset, tkey, vkey) in enumerate([
        ('U9X', U9X_VIDEO, U9X_OFFSET, 't_u9x', 'v_u9x'),
        ('SU7', SU7_VIDEO, SU7_OFFSET, 't_su7', 'v_su7'),
    ]):
        for ci, dm in enumerate(OFFSETS_M):
            s = corner_s + dm
            row = rows.get(s)
            if row is None:
                print(f'[跳过] s_m={s} 无数据')
                continue
            t = float(row[tkey]) + offset
            v = row[vkey]
            tmp = os.path.join(TMP_DIR, f'{name}_{corner_s}_{dm:+d}.jpg')
            ffmpeg_frame(video, t, tmp)
            img = Image.open(tmp).resize((FRAME_W, FRAME_H), Image.LANCZOS)
            grid.append((ri, ci, make_panel(img, f'{name}  {v} km/h  (t={t:.2f}s)')))

    W = FRAME_W * 3 + COL_GAP * 2
    H = TITLE_H + ROW_H * 2 + ROW_GAP
    canvas = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    d.text((8, 8), title, fill=(0, 0, 0), font=font(24))

    for ci, ct in enumerate(COL_TITLES):
        x = ci * (FRAME_W + COL_GAP)
        d.text((x, TITLE_H - 2), ct, fill=(90, 90, 90), font=font(20))

    for ri in range(2):
        d.text((2, TITLE_H + ri * (ROW_H + ROW_GAP) + 2), ROW_NAMES[ri],
               fill=(0, 0, 0), font=font(18))

    for ri, ci, panel in grid:
        x = ci * (FRAME_W + COL_GAP)
        y = TITLE_H + ri * (ROW_H + ROW_GAP)
        canvas.paste(panel, (x, y))

    out = os.path.join(OUT_DIR, out_base + '.png')
    canvas.save(out, dpi=(150, 150))
    print(f'[完成] {out} ({W}x{H})')


def main():
    rows = load_corner_rows()
    for corner_s, base, title in CORNERS:
        build_corner_figure(rows, corner_s, base, title)
    print('全部完成')


if __name__ == '__main__':
    main()
