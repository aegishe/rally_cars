# -*- coding: utf-8 -*-
"""
篇2s 弯道截图对比生成器（三行版：U9X / SU7 量产 / SU7 原型）
- Wehrseifen 复合弯四帧结构：刹车点 → 弯心1（Wehrseifen）→ 弯心2（Breidscheid）→ 出弯
- U9X、量产行：corner_comparison.csv 驱动（s_m 位置，速度=CSV 值）
- 原型行：6:22.091 YouTube 原版 mp4（视频时间= Laptime+1.77s，速度=人工读数）
用法：python publish/scripts/gen_corner_compare.py
输出：publish/assets/chapter2s-c1-kesselchen.png
"""
import csv
import subprocess
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\Project\dsh_rally_cars'
CORNER_CSV = os.path.join(ROOT, 'track', 'corner_comparison.csv')
U9X_VIDEO = r'G:\Capture\youtube\YANGWANG U9 Xtreme ｜ 6_59.157 official laptime ｜ Nordschleife [pcPraRlmi8s].mp4'
SU7_VIDEO = r'G:\Capture\youtube\Xiaomi SU7 Ultra ｜ Official uncut Nürburgring footage [I2EjtbqkZIU].mp4'
P622_VIDEO = r'G:\Capture\youtube\Xiaomi SU7 Ultra prototype ｜ Official uncut Nürburgring footage [M2zt0yAcplU].mp4'
OUT_DIR = os.path.join(ROOT, 'publish', 'assets')
TMP_DIR = os.path.join(ROOT, 'publish', 'assets', '_corner_tmp')

U9X_OFFSET = 1.28   # 视频时间 = 圈内时间 + 1.28s（OCR 验证）
SU7_OFFSET = 2.08   # 视频时间 = 圈内时间 + 2.08s（像素级对齐）
P622_OFFSET = 1.77  # mp4 原版：视频时间 = Laptime + 1.77s

# 三车统一赛道位置（s_m），速度从 CSV/人工读数取；刹车点差异在正文文字说明
U9X_SPOTS = [(8400, '弯前'), (8590, '弯心1'), (8900, '弯心2'), (9100, '出弯')]
SU7_SPOTS = [(8400, '弯前'), (8590, '弯心1'), (8900, '弯心2'), (9100, '出弯')]
# 原型帧（Laptime, 标注）——t 由相邻弯锚分段插值到同一位置
PROTO_SPOTS = [
    (165.0, '257 km/h（弯前）'),
    (169.0, '216 km/h（弯心1）'),
    (172.0, '111 km/h（弯心2）'),
    (177.0, '194 km/h（出弯）'),
]

ROW_LABELS = [
    '仰望 U9 Xtreme（3019hp / 2480kg / 1217hp/t）',
    'SU7 Ultra 量产（1548hp / 2360kg / 656hp/t）',
    'SU7 Ultra 原型（1548hp / ≈1860kg / 832hp/t，6:22.091）',
]
COL_TITLES = ['弯前（8400m）', '弯心1（Wehrseifen 8590m）', '弯心2（Breidscheid 8900m）', '出弯（9100m）']
FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
FRAME_W, FRAME_H = 480, 270
LABEL_H = 26
ROW_H = FRAME_H + LABEL_H
TITLE_H = 40
COL_GAP, ROW_GAP = 4, 4
N_COLS = 4


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def load_corner_rows():
    rows = {}
    with open(CORNER_CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows[int(float(r['s_m']))] = r
    return rows


def ffmpeg_frame(video, t, out_path):
    subprocess.run(['ffmpeg', '-y', '-ss', f'{t:.3f}', '-i', video,
                    '-frames:v', '1', '-q:v', '2', out_path],
                   check=True, capture_output=True)


def make_panel(img, label):
    panel = Image.new('RGB', (FRAME_W, FRAME_H + LABEL_H), (0, 0, 0))
    panel.paste(img, (0, 0))
    d = ImageDraw.Draw(panel)
    f = font(17)
    tw = d.textlength(label, font=f)
    d.text(((FRAME_W - tw) / 2, FRAME_H + 2), label, fill=(255, 255, 255), font=f)
    return panel


def main():
    rows = load_corner_rows()
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    grid = []
    # 行1/2：U9X 与量产（CSV 驱动）
    for ri, (name, video, offset, tkey, vkey, spots) in enumerate([
        ('U9X', U9X_VIDEO, U9X_OFFSET, 't_u9x', 'v_u9x', U9X_SPOTS),
        ('SU7', SU7_VIDEO, SU7_OFFSET, 't_su7', 'v_su7', SU7_SPOTS),
    ]):
        for ci, (s, _tag) in enumerate(spots):
            row = rows.get(s)
            t = float(row[tkey]) + offset
            v = row[vkey]
            tmp = os.path.join(TMP_DIR, f'{name}_{s}.jpg')
            ffmpeg_frame(video, t, tmp)
            img = Image.open(tmp).resize((FRAME_W, FRAME_H), Image.LANCZOS)
            grid.append((ri, ci, make_panel(img, f'{v} km/h（{s}m）')))

    # 行3：原型（mp4 固定帧，人工读数）
    for ci, (t_lap, label) in enumerate(PROTO_SPOTS):
        tmp = os.path.join(TMP_DIR, f'PROTO_{ci}.jpg')
        ffmpeg_frame(P622_VIDEO, t_lap + P622_OFFSET, tmp)
        img = Image.open(tmp).resize((FRAME_W, FRAME_H), Image.LANCZOS)
        grid.append((2, ci, make_panel(img, label)))

    W = FRAME_W * N_COLS + COL_GAP * (N_COLS - 1)
    H = TITLE_H + ROW_H * 3 + ROW_GAP * 2
    canvas = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    d.text((8, 8), 'Wehrseifen 8.6km 极高速弯：三车同弯对照（复合弯四帧）', fill=(0, 0, 0), font=font(24))

    for ci, ct in enumerate(COL_TITLES):
        x = ci * (FRAME_W + COL_GAP)
        d.text((x, TITLE_H - 2), ct, fill=(90, 90, 90), font=font(18))

    for ri in range(3):
        d.text((2, TITLE_H + ri * (ROW_H + ROW_GAP) + 2), ROW_LABELS[ri],
               fill=(0, 0, 0), font=font(16))

    for ri, ci, panel in grid:
        x = ci * (FRAME_W + COL_GAP)
        y = TITLE_H + ri * (ROW_H + ROW_GAP)
        canvas.paste(panel, (x, y))

    out = os.path.join(OUT_DIR, 'chapter2s-c1-kesselchen.png')
    canvas.save(out, dpi=(150, 150))
    print(f'[完成] {out} ({W}x{H})')


if __name__ == '__main__':
    main()
