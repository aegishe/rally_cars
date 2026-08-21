# -*- coding: utf-8 -*-
"""
publish/篇1 配图生成
数据源：offroad/docs/越野车场景打分标准-核心结论.md（SOC三状态、P1发电、适配矩阵）
输出：publish/assets/*.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r'D:\Project\dsh_rally_cars'
OUT = os.path.join(ROOT, 'publish', 'assets')
os.makedirs(OUT, exist_ok=True)

# ============ 图1：SOC 跌落比（满态 vs 弱态） ============
archs = ['纯油V6', 'P2并联V6', 'HEV浅充浅放', 'P2并联2.0T', '单档DMO', '增程式', '多档DHT', '功率分流+3DHT', 'T1+增程(奥迪)']
full = [190, 300, 200, 250, 300, 300, 300, 635, 288]
weak = [190, 190, 190, 150, 100, 60, 70, 100, 220]

# 按满态排序（升序）
order = np.argsort(full)
archs = [archs[i] for i in order]
full = [full[i] for i in order]
weak = [weak[i] for i in order]

# 机械直驱根基着色
mech_roots = {'纯油V6', 'P2并联V6', 'HEV浅充浅放', 'P2并联2.0T'}
colors = ['#27ae60' if a in mech_roots else '#e74c3c' for a in archs]

y = np.arange(len(archs))
h = 0.36
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(y + h/2, full, height=h, color=colors, alpha=0.85, label='满态功率（SOC>20%）')
ax.barh(y - h/2, weak, height=h, color=colors, alpha=0.35, label='弱态功率（亏电+限功率）')
for yi, f, w, a in zip(y, full, weak, archs):
    ax.text(f + 12, yi + h/2, f'{f}', va='center', fontsize=9, fontweight='bold')
    ax.text(w + 12, yi - h/2, f'{w}', va='center', fontsize=9, color='#555')
    ratio = f / w
    ax.text(660, yi, f'{ratio:.1f}:1', va='center', ha='left', fontsize=9,
            color='#c0392b' if ratio >= 3 else '#27ae60', fontweight='bold')
ax.text(600, len(archs) - 0.3, '跌落比', fontsize=9, color='#888')
ax.set_yticks(y)
ax.set_yticklabels(archs, fontsize=10)
ax.set_xlabel('系统功率（kW）')
ax.set_xlim(0, 780)
ax.set_title('SOC 三状态的核心：满态峰值 vs 弱态可持续功率')
ax.legend(loc='lower right', fontsize=9)
ax.grid(axis='x', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter1-1-soc-collapse.png'), dpi=150)
plt.close(fig)
print('fig1 done')

# ============ 图2：额定/持续 vs 最大发电功率（重叠柱） ============
fig, ax = plt.subplots(figsize=(9, 5.4))
cars = ['猛士M817\n(混动箱, 2.0T)', '纵横G700\n(P1电机, 2.0T)', '豹5\n(P1, 1.5T)', '坦克500 Hi4-T\n(2.0T机械直驱, 参照)']
rated = [110, 100, 91, 180]   # 额定/持续口径（深柱）
maxv  = [None, 150, 150, None]  # 最大/电机功率口径（浅宽柱，未公布则无）
x = np.arange(len(cars))
# 宽柱：最大口径（背景带）
for xi, mv in zip(x, maxv):
    if mv is not None:
        ax.bar(xi, mv, 0.58, color='#f39c12', alpha=0.28)
        ax.text(xi, mv + 4, f'最大/电机 {mv}', ha='center', fontsize=8, color='#b8860b')
# 窄柱：额定/持续口径（前景柱）
for xi, rv in zip(x, rated):
    c = '#27ae60' if xi == 3 else '#e74c3c'
    ax.bar(xi, rv, 0.22, color=c, alpha=0.95)
    ax.text(xi, rv + 6, f'{rv}', ha='center', fontsize=10.5, fontweight='bold', color='#c0392b' if xi != 3 else '#1e7d46')
notes = ['官方"持续发电"口径\n（上市初期素材标 100kW）',
         '额定持续 100kW（历史页面口径）\n最大/电机 150kW（持续官方未公布）',
         '行驶状态额定 91kW\n（autohome 问答；原地 20kW）',
         '2.0T 最大功率\n（机械直驱参照）']
for xi, n in zip(x, notes):
    ax.text(xi, 8, n, ha='center', fontsize=7.3, color='#555')
ax.set_xticks(x)
ax.set_xticklabels(cars, fontsize=10)
ax.set_ylabel('功率（kW）')
ax.set_ylim(0, 205)
ax.set_title('电驱越野的保电生命线：额定/持续 vs 最大发电功率（2026-08 修正）')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#e74c3c', label='额定/持续口径（深柱）'),
                   Patch(color='#f39c12', alpha=0.5, label='最大/电机功率口径（浅宽柱）')],
          loc='upper right', fontsize=8.5)
ax.grid(axis='y', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter1-2-p1-generator.png'), dpi=150)
plt.close(fig)
print('fig2 done')

# ============ 图3：9 场景 × 架构适配矩阵 ============
scenes = ['岩石/攀爬', '丛林/泥泞', '日常通勤', '沙漠短冲刺', '戈壁短冲刺', '砂石竞速', '高原山路', '戈壁长耐力', '沙漠长耐力']
arch_cols = ['纯油V6', 'P2并联', 'HEV', 'DMO', '多档DHT', '增程']
# 2=最优, 1=适用, 0=不推荐
M = np.array([
    [1, 2, 1, 2, 2, 0],  # 岩石攀爬: DMO/DHT/P2
    [1, 2, 1, 2, 2, 0],  # 丛林泥泞
    [1, 1, 1, 2, 2, 2],  # 日常通勤
    [1, 1, 0, 2, 2, 1],  # 沙漠短冲刺（满态）
    [1, 1, 0, 2, 2, 1],  # 戈壁短冲刺
    [2, 2, 1, 0, 0, 0],  # 砂石竞速: 纯油/P2
    [2, 2, 1, 0, 0, 0],  # 高原山路
    [0, 2, 1, 0, 0, 0],  # 戈壁长耐力: P2唯一
    [0, 2, 1, 0, 0, 0],  # 沙漠长耐力: P2唯一
])

fig, ax = plt.subplots(figsize=(10.5, 6.8))
cmap = matplotlib.colors.ListedColormap(['#ecf0f1', '#f9e79f', '#27ae60'])
im = ax.imshow(M, cmap=cmap, aspect='auto', vmin=0, vmax=2)
ax.set_xticks(np.arange(len(arch_cols)))
ax.set_xticklabels(arch_cols, fontsize=10)
ax.set_yticks(np.arange(len(scenes)))
ax.set_yticklabels(scenes, fontsize=10)
for i in range(len(scenes)):
    for j in range(len(arch_cols)):
        val = M[i, j]
        txt = '★' if val == 2 else ('●' if val == 1 else '')
        ax.text(j, i, txt, ha='center', va='center', fontsize=13,
                color='#1a6e3d' if val == 2 else ('#8a6d00' if val == 1 else '#bbb'))
ax.set_xticks(np.arange(len(arch_cols) + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(len(scenes) + 1) - 0.5, minor=True)
ax.grid(which='minor', color='white', lw=2)
ax.tick_params(which='minor', length=0)
ax.set_title('9 场景 × 架构适配矩阵（★=最优解 ●=适用）')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#27ae60', label='★ 最优'), Patch(color='#f9e79f', label='● 适用'), Patch(color='#ecf0f1', label='不推荐')],
          loc='lower right', bbox_to_anchor=(1.28, 0.5), fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter1-3-scene-matrix.png'), dpi=150)
plt.close(fig)
print('fig3 done')

print('ALL DONE ->', OUT)
