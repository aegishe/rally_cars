# -*- coding: utf-8 -*-
"""百分比差距分析：
A. 达喀尔: 路虎T2(502/合成) vs 韩魏220/鹿丙龙243
B. 环塔:   坦克700(251) vs 鹿丙龙104
C. 外推:   若坦克按环塔的相对速度跑达喀尔, 相对达喀尔基准会差多少
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
def to_sec(t):
    if not t: return None
    p = t.strip().split(':')
    try: return int(p[0])*3600+int(p[1])*60+int(p[2])
    except: return None
def fmt(s):
    if s is None: return '—'
    neg=s<0; s=abs(s)
    return ('-' if neg else '') + f'{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}'
def pct(diff, base):
    return f'{diff/base*100:.1f}%'

rows = list(csv.reader(open(r'D:\Project\dsh_rally_cars\offroad\达喀尔2026_T1+与T2_逐车逐赛段成绩.csv', encoding='utf-8-sig')))
car = {r[1]: r for r in rows[1:]}
rows2 = list(csv.reader(open(r'D:\Project\dsh_rally_cars\offroad\环塔2026_T1+_逐车逐赛段成绩.csv', encoding='utf-8-sig')))
ht104 = next(r for r in rows2[1:] if r[0]=='104')
rows3 = list(csv.reader(open(r'D:\Project\dsh_rally_cars\offroad\环塔2026_总成绩.csv', encoding='utf-8-sig')))
ht251 = next(r for r in rows3[1:] if r[0]=='251')

print('=== A. 达喀尔组 百分比(落后方 = 路虎T2) ===')
hw = to_sec(car['220'][30]); lu = to_sec(car['243'][30]); lr = to_sec(car['502'][30])
print(f'路虎502 vs 韩魏220 : 总差 {fmt(lr-hw)} = {pct(lr-hw, hw)} (以韩魏为基准)')
print(f'路虎502 vs 鹿丙龙243: 总差 {fmt(lr-lu)} = {pct(lr-lu, lu)} (以鹿丙龙为基准)')
# 合成路虎
syn = sum(min(to_sec(car[b][5+i]) for b in ('500','502','504')) for i in range(13))
print(f'合成路虎 vs 韩魏   : 总差 {fmt(syn-hw)} = {pct(syn-hw, hw)}')
print(f'合成路虎 vs 鹿丙龙 : 总差 {fmt(syn-lu)} = {pct(syn-lu, lu)}')

print()
print('=== B. 环塔组 百分比(落后方 = 坦克700 T2.E) ===')
luht = to_sec(ht104[18]); tkht = 51*3600+59*60+8  # ewrc官方总
print(f'坦克251 vs 鹿丙龙104: 总差 {fmt(tkht-luht)} = {pct(tkht-luht, luht)} (以鹿丙龙为基准)')

print()
print('=== B2. 环塔逐段百分比(坦克相对鹿丙龙, 该段坦克时间=基准) ===')
cum_pct = []
print(f'{"SS":<4}{"鹿丙龙":>11}{"坦克700":>11}{"坦克/鹿":>9}{"坦克慢%":>9}')
for i in range(12):
    a = to_sec(ht104[5+i]); b = to_sec(ht251[5+i])
    if a and b:
        print(f'SS{i+1:<4}{fmt(a):>11}{fmt(b):>11}{b/a:>8.2f}x{b/a*100-100:>8.1f}%')
        cum_pct.append(b/a)
avg = sum(cum_pct)/len(cum_pct)
print(f'平均: 坦克/鹿丙龙 = {avg:.2f}x (慢 {avg*100-100:.1f}%)')

print()
print('=== A2. 达喀尔逐段百分比(路虎502相对韩魏220) ===')
lr_hw_ratio = []
print(f'{"SS":<4}{"韩魏220":>11}{"路虎502":>11}{"路虎/韩魏":>10}')
for i in range(13):
    a = to_sec(car['220'][5+i]); b = to_sec(car['502'][5+i])
    if a and b:
        print(f'SS{i+1:<4}{fmt(a):>11}{fmt(b):>11}{b/a:>9.2f}x')
        lr_hw_ratio.append(b/a)
avg2 = sum(lr_hw_ratio)/len(lr_hw_ratio)
print(f'平均: 路虎502/韩魏 = {avg2:.2f}x (慢 {avg2*100-100:.1f}%)')
