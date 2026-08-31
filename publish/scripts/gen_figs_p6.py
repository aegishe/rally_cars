# -*- coding: utf-8 -*-
"""
publish/篇6 配图生成 —— 用途定位图（草样 v2）
横轴 = 能去哪里（通过性/场景强度）
纵轴 = 能带什么（载人/载货取向）：两厢 → 轿车 → SUV/MPV（对货/对人）→ 皮卡
颜色 = 能源形态（红=油/P2 机械直驱 → 蓝=纯电）
气泡大小 = 性能（够用/够快/性能级）
输出：publish/assets/chapter6-1-purpose-map.png

草样口径说明：车型坐标与能源归类为草样估计，定稿需按官方参数逐项核对。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Patch

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r'D:\Project\dsh_rally_cars'
OUT = os.path.join(ROOT, 'publish', 'assets')
os.makedirs(OUT, exist_ok=True)

# 能源形态 → 颜色（红=油/P2 机械直驱 → 蓝=纯电）
ENERGY = {
    '纯油/P2': '#e74c3c',
    '多档DHT': '#e67e22',
    '单档混动': '#f1c40f',
    '增程': '#27ae60',
    '纯电': '#3498db',
}

SIZE = {'小': 42, '中': 130, '大': 300}

# (label, x, y, energy, perf, label_dx, label_dy)
# x=能去哪里：0 纯铺装 / 1 混合路 / 2 穿越
# y=能带什么：0 两厢 / 1 轿车 / 2 SUV·MPV（SUV对货≈1.9 MPV对人≈2.2）/ 3 皮卡
cars = [
    # 两厢（y≈0）
    ('海豚', 0.05, -0.16, '纯电', '小', 0.22, -0.16),
    ('高尔夫', 0.05, 0.16, '纯油/P2', '小', 0.22, 0.20),
    # 轿车（y≈1）
    ('秦L DM-i', 0.05, 1.00, '单档混动', '中', 0.16, 0.96),
    ('SU7', 0.00, 0.80, '纯电', '大', 0.20, 0.80),
    ('Model 3', -0.02, 1.20, '纯电', '中', -0.02, 1.32),
    ('56E', 0.22, 1.05, '纯油/P2', '中', 0.32, 1.10),
    # SUV（y≈1.85-2.15，对货）
    ('元PLUS', 0.10, 1.84, '纯电', '小', 0.26, 1.82),
    ('理想L6', 0.28, 1.98, '增程', '中', 0.40, 2.04),
    ('问界M7', 0.13, 2.10, '增程', '中', 0.13, 2.24),
    ('捷途旅行者C-DM', 0.85, 1.88, '多档DHT', '中', 0.85, 1.66),
    ('哈弗猛龙', 1.00, 1.98, '多档DHT', '中', 1.00, 2.16),
    ('钛7', 0.90, 2.10, '单档混动', '中', 0.60, 2.16),
    ('豹5', 1.25, 1.86, '单档混动', '大', 1.46, 1.84),
    ('坦克300 Hi4-T', 1.72, 1.98, '纯油/P2', '中', 1.72, 1.72),
    ('坦克700 Hi4-T', 2.00, 2.08, '纯油/P2', '大', 2.00, 2.32),
    ('卫士', 2.00, 1.80, '纯油/P2', '大', 1.74, 1.56),
    ('仰望U8', 1.86, 2.20, '增程', '大', 1.86, 2.44),
    # MPV（y≈2.25-2.4，对人）
    ('腾势D9', 0.10, 2.28, '单档混动', '中', 0.32, 2.30),
    ('理想MEGA', 0.03, 2.40, '纯电', '大', 0.24, 2.46),
    # 皮卡（y≈3）
    ('雷达RD6', 0.30, 2.96, '纯电', '小', 0.56, 2.98),
    ('长城炮', 1.30, 3.04, '纯油/P2', '中', 1.56, 3.06),
]

fig, ax = plt.subplots(figsize=(12.6, 8.6))

for label, x, y, energy, perf, dx, dy in cars:
    ax.scatter(x, y, s=SIZE[perf], color=ENERGY[energy], alpha=0.85,
               edgecolors='white', linewidths=0.7, zorder=3)
    ax.text(dx, dy, label, fontsize=8.5, ha='center', va='center',
            color='#222', zorder=4)

ax.set_xlim(-0.40, 2.50)
ax.set_ylim(-0.55, 3.40)
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(['纯铺装\n(城市/高速)', '混合路\n(偶尔烂路)', '穿越\n(长距非铺装)'], fontsize=11)
ax.set_yticks([0, 1, 2, 3])
ax.set_yticklabels(['两厢', '轿车', 'SUV / MPV\n(对货 / 对人)', '皮卡'], fontsize=11)
ax.set_xlabel('能去哪里（通过性 / 场景强度）', fontsize=12.5)
ax.set_ylabel('能带什么（载人 / 载货）', fontsize=12.5)
ax.set_title('买车先看两件事：能去哪里 × 能带什么（其余都是标签）', fontsize=14.5, fontweight='bold')
ax.grid(alpha=0.22, lw=0.5, zorder=0)

energy_handles = [Patch(color=c, label=k) for k, c in ENERGY.items()]
leg1 = ax.legend(handles=energy_handles, title='能源形态（颜色）',
                 loc='upper left', fontsize=9, title_fontsize=9, framealpha=0.92)

size_handles = [
    mlines.Line2D([], [], color='gray', marker='o', linestyle='None', markersize=4, label='小 · 够用'),
    mlines.Line2D([], [], color='gray', marker='o', linestyle='None', markersize=7, label='中 · 够快'),
    mlines.Line2D([], [], color='gray', marker='o', linestyle='None', markersize=10, label='大 · 性能级'),
]
leg2 = ax.legend(handles=size_handles, title='性能（气泡大小）',
                 loc='upper right', fontsize=9, title_fontsize=9, framealpha=0.92)
ax.add_artist(leg1)

fig.tight_layout()
out = os.path.join(OUT, 'chapter6-1-purpose-map.png')
fig.savefig(out, dpi=150)
plt.close(fig)
print('saved ->', out)
