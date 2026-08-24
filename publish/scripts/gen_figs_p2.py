# -*- coding: utf-8 -*-
"""
publish/篇2 配图生成
数据源：track/scripts/ring_regression.py（42车）、track/U9X_power_analysis.csv（反推）
输出：publish/assets/*.png（静态配图，中文标注）
"""
import io, os, sys, contextlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r'D:\Project\dsh_rally_cars'
OUT = os.path.join(ROOT, 'publish', 'assets')
os.makedirs(OUT, exist_ok=True)

# ---------- 数据准备 ----------
sys.path.insert(0, os.path.join(ROOT, 'track', 'scripts'))
with contextlib.redirect_stdout(io.StringIO()):
    import ring_regression as rr

data = rr.data
hp   = np.array([d[0] for d in data])
kg   = np.array([d[1] for d in data])
lap  = np.array([d[2] for d in data])
is_ev   = np.array([d[3] for d in data])
is_phev = np.array([d[4] for d in data])
names = [d[7] for d in data]
pw = hp / (kg / 1000.0)  # hp/t

# ============ 图1：功重比 vs 圈速（42车，按动力着色） ============
fig, ax = plt.subplots(figsize=(10, 6.5))
colors = np.where(is_ev == 1, '#e74c3c', np.where(is_phev == 1, '#f39c12', '#27ae60'))
for c, lab in [('#27ae60', '纯油'), ('#f39c12', 'PHEV'), ('#e74c3c', '纯电')]:
    m = (is_ev == 1) if lab == '纯电' else ((is_phev == 1) if lab == 'PHEV' else ((is_ev == 0) & (is_phev == 0)))
    ax.scatter(pw[m], lap[m], c=c, label=lab, s=36, alpha=0.85, edgecolors='white', linewidths=0.5)

# 关键车标注
marks = {
    '仰望 U9': (3019/2.48, 419.2, '仰望U9'),
    'GT2 RS Manthey': (700/1.44, 403.3, 'GT2 RS'),
    'Taycan GT Manthey': (1093/2.25, 415.5, 'Taycan'),
    'SU7 Ultra': (1548/2.36, 424.9, 'SU7 Ultra 量产'),
    'YU7 GT': (1003/2.46, 442.8, 'YU7 GT'),
    '911 GT3': (510/1.456, 416.3, '911 GT3'),
    'Nevera': (1914/2.15, 425.3, 'Nevera'),
}
for key, (x, y, lab) in marks.items():
    ax.annotate(lab, (x, y), textcoords='offset points', xytext=(6, -2),
                fontsize=9, fontweight='bold',
                arrowprops=dict(arrowstyle='-', lw=0.6, color='#555'))

# SU7 Ultra 原型车 —— 实心星标注（2024 版，回归样本）
ax.scatter([1548/1.9], [406.874], marker='*', s=260, facecolors='#e74c3c',
           edgecolors='#e74c3c', linewidths=1.5, zorder=6)
ax.annotate('SU7 Ultra 原型（2024 版，回归样本）\n6:46.874 · 1548hp · 1900kg · 残差 -3.4%',
            (1548/1.9, 406.874), textcoords='offset points', xytext=(10, -40),
            fontsize=9, fontweight='bold', color='#c0392b',
            arrowprops=dict(arrowstyle='->', lw=0.8, color='#c0392b'))

# SU7 Ultra 原型车 —— 空心星标注（2025 升级版，未纳入回归）
ax.scatter([1548/1.86], [382.091], marker='*', s=260, facecolors='none',
           edgecolors='#c0392b', linewidths=1.5, zorder=6)
ax.annotate('SU7 Ultra 原型（2025 升级版，未纳入回归）\n6:22.091 · 1548hp · ≈1860kg · 参数未公开',
            (1548/1.86, 382.091), textcoords='offset points', xytext=(10, 18),
            fontsize=9, fontweight='bold', color='#8a4b2a',
            arrowprops=dict(arrowstyle='->', lw=0.8, color='#8a4b2a'))

ax.set_xlabel('账面功重比（hp/t）')
ax.set_ylabel('纽北圈速（秒）')
ax.set_title('44 车：功重比 vs 圈速（N=44，R²=0.901 加入质量分布+扭矩矢量后）')
ax.invert_yaxis()
ax.legend(loc='lower right')
ax.grid(alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter2-1-pw-laptime.png'), dpi=150)
plt.close(fig)
print('fig1 done')

# ============ 图2：重量窗格 k 值 ============
fig, ax = plt.subplots(figsize=(8, 5))
bins = ['1400-1600', '1600-1800', '1800-2000', '2200-3000']
ks = [0.153, 0.160, 0.199, 0.082]
r2s = [0.635, 0.846, 0.760, 0.726]
bars = ax.bar(bins, ks, color=['#27ae60', '#27ae60', '#27ae60', '#c0392b'], width=0.55)
for b, k, r2 in zip(bars, ks, r2s):
    ax.text(b.get_x() + b.get_width()/2, k + 0.006, f'{k:.3f}\n(R²={r2:.2f})',
            ha='center', va='bottom', fontsize=9)
ax.set_ylabel('功重比弹性 k（功重比+1% → 圈速缩短 k%）')
ax.set_title('功重比效率随车重非线性下降：≥2200kg 后腰斩（死亡线）')
ax.set_ylim(0, 0.24)
ax.grid(axis='y', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter2-2-k-value.png'), dpi=150)
plt.close(fig)
print('fig2 done')

# ============ 图3：U9X 功率反推全圈曲线 (5fps 滑动回归口径) ============
df = pd.read_csv(os.path.join(ROOT, 'track', 'u9x_5fps_power.csv'))
t = df['t_s'].values
p = df['power_kW'].values
v = df['speed_kmh'].values

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(t, p, color='#2c3e50', lw=0.6, alpha=0.9, label='轮上功率反推（5fps 滑动回归口径）')
ax.fill_between(t, p, 0, where=(p > 0), color='#3498db', alpha=0.15)
ax.fill_between(t, p, 0, where=(p < 0), color='#95a5a6', alpha=0.25, label='制动/回收（负值）')

# 账面功率参考线
ax.axhline(2220, color='#c0392b', ls='--', lw=1.2, label='账面峰值 2220kW（3019hp）')

# 峰值标注 (5fps 口径 + 1s 口径区间)
imax = np.argmax(p)
ax.annotate(f'5fps 稳健口径峰值 {p[imax]:.0f}kW @ {v[imax]:.0f}km/h\n（1s 差分口径 1761kW；真实峰值在两者之间，\n兑现率 73-79%，账面从未兑现）',
            xy=(t[imax], p[imax]), xytext=(t[imax] - 190, p[imax] + 300),
            fontsize=9.5, fontweight='bold', color='#c0392b',
            arrowprops=dict(arrowstyle='->', lw=1, color='#c0392b'))

# 349 平台段高亮（375-405s）
ax.axvspan(375, 405, color='#e67e22', alpha=0.12)
ax.text(390, 1650, '349km/h\n限速平台', ha='center', fontsize=8.5, color='#a04000')

ax.set_xlabel('时间（秒）')
ax.set_ylabel('轮上功率（kW）')
ax.set_title('U9X 纽北 7:03.5 全程轮上功率反推：实测峰值 1627-1761kW，账面从未兑现')
ax.set_xlim(0, t.max())
ax.set_ylim(-1200, 2600)
ax.legend(loc='upper right', fontsize=9)
ax.grid(alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter2-3-u9x-power.png'), dpi=150)
plt.close(fig)
print('fig3 done')

# ============ 图4：残差 Top/Bottom ============
fig, ax = plt.subplots(figsize=(9, 5.5))
top_names  = ['Taycan GT Manthey', 'AMG ONE', '911 GT3 RS Manthey', 'SU7 Ultra 原型', 'Aventador SVJ']
top_vals   = [-5.6, -4.2, -3.8, -3.4, -3.3]
bot_names  = ['Model S Plaid', 'Golf R 20Y', 'McLaren 720S', '仰望 U9', 'Rimac Nevera']
bot_vals   = [3.5, 3.8, 3.9, 5.3, 5.3]
all_names = top_names[::-1] + bot_names
all_vals = top_vals[::-1] + bot_vals
bar_colors = ['#27ae60'] * 5 + ['#e74c3c'] * 5
y = np.arange(len(all_names))
ax.barh(y, all_vals, color=bar_colors, height=0.6)
for yi, val in zip(y, all_vals):
    ax.text(val + (0.12 if val > 0 else -0.12), yi, f'{val:+.1f}%',
            va='center', ha='left' if val > 0 else 'right', fontsize=9, fontweight='bold')
ax.set_yticks(y)
ax.set_yticklabels(all_names, fontsize=9)
ax.axvline(0, color='#333', lw=0.8)
ax.set_xlabel('残差（ln实际 − ln预测，负=高效）')
ax.set_title('全量回归残差：Top 5 高效 vs Bottom 5 低效')
ax.set_xlim(-7, 6.5)
ax.grid(axis='x', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter2-4-residual.png'), dpi=150)
plt.close(fig)
print('fig4 done')

print('ALL DONE ->', OUT)
