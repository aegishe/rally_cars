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
fig.savefig(os.path.join(OUT, 'fig1_soc_collapse.png'), dpi=150)
plt.close(fig)
print('fig1 done')

# ============ 图2：P1/P0 持续发电对比 ============
fig, ax = plt.subplots(figsize=(8.5, 5))
cars = ['猛士M817\n(P0, 2.0T)', '纵横G700\n(P1, 2.0T)', '豹5\n(P1, 1.5T)', '坦克500 Hi4-T\n(2.0T机械直驱, 参照)']
peak = [100, 120, 150, 180]
cont = [50, 60, 91, 180]
x = np.arange(len(cars))
w = 0.35
b1 = ax.bar(x - w/2, peak, w, color='#f39c12', alpha=0.8, label='发电峰值（30秒，不可依赖）')
b2 = ax.bar(x + w/2, cont, w, color='#e74c3c', alpha=0.85, label='持续发电功率（可依赖）')
for xi, p, c in zip(x, peak, cont):
    ax.text(xi - w/2, p + 4, f'{p}', ha='center', fontsize=9, color='#b8860b')
    ax.text(xi + w/2, c + 4, f'{c}', ha='center', fontsize=9, fontweight='bold', color='#c0392b')
ax.set_xticks(x)
ax.set_xticklabels(cars, fontsize=10)
ax.set_ylabel('功率（kW）')
ax.set_ylim(0, 230)
ax.set_title('电驱越野的保电生命线：P1/P0 持续发电功率（环塔实测/公开参数）')
ax.legend(loc='upper right', fontsize=9)
ax.grid(axis='y', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig2_p1_generator.png'), dpi=150)
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
fig.savefig(os.path.join(OUT, 'fig3_scene_matrix.png'), dpi=150)
plt.close(fig)
print('fig3 done')

print('ALL DONE ->', OUT)
