# -*- coding: utf-8 -*-
"""
publish/篇3 配图生成（派克峰篇）
数据源：pikes-peak/charts/regression_results.json（权威回归结果）
输出：publish/assets/fig*_pp_*.png（静态配图，中文标注，150dpi）
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r'D:\Project\dsh_rally_cars'
OUT = os.path.join(ROOT, 'publish', 'assets')
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(ROOT, 'pikes-peak', 'charts', 'regression_results.json'), encoding='utf-8') as f:
    res = json.load(f)

cars = res['cars']
protos = res['protos']
truck = res['truck_ref'][0]

pt_cn = {'ICE': '纯油', 'EV': '纯电', 'PHEV': 'PHEV'}
pt_colors = {'ICE': '#27ae60', 'EV': '#e74c3c', 'PHEV': '#f39c12'}

hp = np.array([c['hp'] for c in cars])
kg = np.array([c['weight'] for c in cars])
lap = np.array([c['lap_s'] for c in cars])
pw = hp / (kg / 1000.0)
pt = [c['powertrain'] for c in cars]
aero = [c['aero'] for c in cars]
names = [c['name'] for c in cars]
resid = np.array([c['residual_pct'] for c in cars])

def fmt_lap(s):
    m = int(s // 60)
    return f"{m}:{s - m*60:04.1f}"

# ============ 图1：功重比 vs 圈速 ============
fig, ax = plt.subplots(figsize=(10, 6.5))

for p, lab in [('ICE', '纯油'), ('PHEV', 'PHEV'), ('EV', '纯电')]:
    m = [x == p for x in pt]
    if not any(m):
        continue
    ax.scatter(pw[m], lap[m], c=pt_colors[p], label=lab, s=42, alpha=0.85,
               edgecolors='white', linewidths=0.5, zorder=3)

# 改装空力：加圈标注
m_mod = [x == 'Modified' for x in aero]
ax.scatter(pw[m_mod], lap[m_mod], facecolors='none', edgecolors='#333',
           s=200, linewidths=1.2, zorder=4, label='改装空力')

# 极限组原型（星）
ppw = np.array([p['hp'] for p in protos]) / (np.array([p['weight'] for p in protos]) / 1000.0)
plap = np.array([p['lap_s'] for p in protos])
ax.scatter(ppw, plap, marker='*', s=420, facecolors='black', edgecolors='gold',
           linewidths=1.2, zorder=5, label='Unlimited 原型')

# 皮卡参照（X）
ax.scatter([truck['pw_ratio']], [truck['lap_s']], marker='x', s=140, c='#8e44ad',
           linewidths=2.5, zorder=5, label='Rivian R1T（参照，不入回归）')

# 关键标注
marks = [
    ('VW I.D. R', 680/1.1, 477.148, 'I.D. R 7:57.1\n680hp/1100kg', 8, -10),
    ('Peugeot 208 T16', 875/0.875, 493.878, '208 T16 8:13.9\n875hp/875kg', 8, -10),
    ('Hyundai Ioniq 5 N TA', 641/2.1, 570.852, 'Ioniq 5 N TA 9:30.9\n残差冠军 −3.5%', 8, -16),
    ('911 Turbo S', 650/1.65, 593.74, '911 Turbo S 9:53.7', 8, -14),
    ('Bentayga W12', 635/2.44, 649.902, 'Bentayga 10:49.9', 8, 6),
]
for _, x, y, lab, dx, dy in marks:
    ax.annotate(lab, (x, y), textcoords='offset points', xytext=(dx, dy),
                fontsize=9, fontweight='bold',
                arrowprops=dict(arrowstyle='-', lw=0.6, color='#555'))

ax.set_xscale('log')
ax.set_xlabel('账面功重比（hp/t，对数轴）')
ax.set_ylabel('派克峰圈速（秒）')
ax.set_title('派克峰：功重比 vs 圈速（N=13 量产 + 4 原型 + 1 皮卡参照）')
ax.invert_yaxis()
ax.legend(loc='lower left', fontsize=9)
ax.grid(alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter3-6-pw-laptime.png'), dpi=150)
plt.close(fig)
print('fig1 done')

# ============ 图2：车重 vs 圈速（原厂组单调，改装空力/车手打穿） ============
fig, ax = plt.subplots(figsize=(10, 6.5))

for p, lab in [('ICE', '纯油'), ('PHEV', 'PHEV'), ('EV', '纯电')]:
    m = [x == p for x in pt]
    if not any(m):
        continue
    ax.scatter(kg[m], lap[m], c=pt_colors[p], label=lab, s=42, alpha=0.85,
               edgecolors='white', linewidths=0.5, zorder=3)

# 改装空力：空心圈标注（打破"越重越慢"的主力）
m_mod = [x == 'Modified' for x in aero]
ax.scatter(kg[m_mod], lap[m_mod], facecolors='none', edgecolors='#333',
           s=260, linewidths=1.4, zorder=4, label='改装空力')

ax.scatter(np.array([p['weight'] for p in protos]), plap, marker='*', s=420,
           facecolors='black', edgecolors='gold', linewidths=1.2, zorder=5,
           label='Unlimited 原型')
ax.scatter([truck['weight']], [truck['lap_s']], marker='x', s=140, c='#8e44ad',
           linewidths=2.5, zorder=5, label='Rivian R1T（参照）')

# 重却快的反例：点出空力与车手
driver_marks = [
    ('Corvette ZR1X', 1884, 570.104, 'ZR1X\n改装空力+职业车手', -30, -18),
    ('Hyundai Ioniq 5 N TA', 2100, 570.852, 'Ioniq 5 N TA\n改装空力+WRC车手', 18, 22),
    ('Tesla Model S Plaid改', 2200, 594.901, 'Model S Plaid改\n改装空力(私人)', 26, -30),
    ('Bentley Continental GT', 2244, 618.488, 'Continental GT\n宾利刷纪录+职业车手', -36, -46),
]
for _, x, y, lab, dx, dy in driver_marks:
    ax.annotate(lab, (x, y), textcoords='offset points', xytext=(dx, dy),
                fontsize=8.5, fontweight='bold', color='#c0392b',
                arrowprops=dict(arrowstyle='-', lw=0.8, color='#c0392b'))

# 单调性说明（诚实口径）
ax.annotate('原厂、同车手口径下才大致越重越慢\n（爬坡税：每 100kg 先扣 2-3hp）',
            xy=(2440, 649.902), xytext=(1750, 700),
            fontsize=11, fontweight='bold', color='#333',
            arrowprops=dict(arrowstyle='->', lw=1.2, color='#333'))

ax.set_xlabel('车重（kg）')
ax.set_ylabel('派克峰圈速（秒）')
ax.set_title('派克峰：车重与圈速——原厂组内大致单调，改装空力/车手会打穿排序')
ax.invert_yaxis()
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter3-7-weight-laptime.png'), dpi=150)
plt.close(fig)
print('fig2 done')

# ============ 图3：跨场景对比（马力软通货） ============
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

scenes_hp = ['派克峰\n+10% 马力', '纽北\n+10% 马力']
hp_vals = [0.36, 0.67]
hp_cols = ['#e74c3c', '#3498db']
bars = axes[0].bar(scenes_hp, hp_vals, color=hp_cols, width=0.55)
for b, v in zip(bars, hp_vals):
    axes[0].text(b.get_x() + b.get_width()/2, v + 0.02, f'{v:.2f}%',
                 ha='center', va='bottom', fontsize=11, fontweight='bold')
axes[0].set_ylabel('圈速缩短（%）')
axes[0].set_title('马力是软通货：+10% 马力只换 0.36% 圈速')
axes[0].set_ylim(0, 0.8)
axes[0].grid(axis='y', alpha=0.3, lw=0.5)

scenes_k = ['派克峰\n量产', '纽北\n全量']
k_vals = [0.110, 0.15]
k_cols = ['#e74c3c', '#3498db']
bars = axes[1].bar(scenes_k, k_vals, color=k_cols, width=0.55)
for b, v in zip(bars, k_vals):
    axes[1].text(b.get_x() + b.get_width()/2, v + 0.008, f'{v:.3f}',
                 ha='center', va='bottom', fontsize=11, fontweight='bold')
axes[1].set_ylabel('功重比弹性 k（功重比 +1% → 圈速缩短 k%）')
axes[1].set_title('功重比效率也低一档')
axes[1].set_ylim(0, 0.2)
axes[1].grid(axis='y', alpha=0.3, lw=0.5)

fig.suptitle('派克峰 vs 纽北：同样加马力，这座山上贬了值', fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(os.path.join(OUT, 'chapter3-8-cross-scene.png'), dpi=150)
plt.close(fig)
print('fig3 done')

# ============ 图4：残差排行 ============
fig, ax = plt.subplots(figsize=(9, 6.5))
idx = np.argsort(resid)
snames = np.array(names)[idx]
sres = resid[idx]
cols = [pt_colors[x] for x in np.array(pt)[idx]]
ax.barh(range(len(snames)), sres, color=cols, height=0.62)
for i, v in enumerate(sres):
    ax.text(v + (0.08 if v > 0 else -0.08), i, f'{v:+.1f}%',
            va='center', ha='left' if v > 0 else 'right', fontsize=9, fontweight='bold')
ax.set_yticks(range(len(snames)))
ax.set_yticklabels(snames, fontsize=9)
ax.axvline(0, color='#333', lw=0.8)
ax.set_xlabel('残差（ln 实际 − ln 预测，负 = 高效）')
ax.set_title('派克峰全量回归残差排行：Ioniq 5 N TA 夺冠（改装空力 + 纯电免疫 + AWD）')
ax.set_xlim(-4.5, 3.5)
ax.grid(axis='x', alpha=0.3, lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'chapter3-9-residual.png'), dpi=150)
plt.close(fig)
print('fig4 done')

print('ALL DONE ->', OUT)
