"""
生成纽北圈速分析交互式可视化HTML
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# ========== 数据 ==========
data = np.array([
    # hp, kg, lap(s), is_ev, is_phev, is_suv, is_sedan, 车型名
    [1063, 1720, 389.1, 0, 1, 0, 0],  # AMG ONE
    [700,  1440, 403.3, 0, 0, 0, 0],  # 911 GT2 RS Manthey
    [525,  1450, 405.4, 0, 0, 0, 0],  # 911 GT3 RS Manthey 992.2
    [730,  1637, 408.0, 0, 0, 0, 0],  # AMG GT Black Series
    [525,  1480, 409.3, 0, 0, 0, 0],  # 911 GT3 RS 992
    [510,  1473, 410.9, 0, 0, 0, 0],  # 911 GT3 Manthey 992.2
    [800,  1600, 412.1, 0, 0, 0, 0],  # Mustang GTD
    [510,  1456, 416.3, 0, 0, 0, 0],  # 911 GT3 992
    [887,  1671, 417.0, 0, 1, 0, 0],  # 918 Spyder
    [830,  1621, 418.7, 0, 1, 0, 0],  # Ferrari 296 GTB
    [3019, 2480, 419.2, 1, 0, 0, 0],  # 仰望 U9
    [720,  1476, 420.0, 0, 0, 0, 0],  # Ferrari 488 Pista
    [654,  1542, 421.3, 0, 0, 0, 0],  # Viper ACR
    [500,  1445, 423.1, 0, 0, 0, 0],  # 718 GT4 RS Manthey
    [650,  1650, 423.9, 0, 0, 0, 0],  # 911 Turbo S 992
    [1914, 2150, 425.3, 1, 0, 0, 0],  # Rimac Nevera
    [720,  1429, 428.0, 0, 0, 0, 0],  # McLaren 720S
    [500,  1449, 429.3, 0, 0, 0, 0],  # 718 GT4 RS
    [770,  1718, 405.0, 0, 0, 0, 0],  # Aventador SVJ
    [551,  1619, 438.1, 0, 0, 0, 1],  # M4 CSL
    [600,  1801, 443.2, 0, 0, 0, 1],  # XE SV Project 8
    [530,  1694, 445.5, 0, 0, 0, 1],  # M2 CS
    [551,  1760, 448.8, 0, 0, 0, 1],  # M3 CS
    [635,  1848, 449.6, 0, 0, 0, 1],  # M5 CS
    [550,  1844, 449.5, 0, 0, 0, 1],  # M3 CS Touring
    [400,  1611, 453.1, 0, 0, 0, 1],  # RS 3
    [330,  1429, 464.9, 0, 0, 0, 1],  # Civic Type R
    [325,  1401, 464.5, 0, 0, 0, 1],  # Golf GTI Ed.50
    [333,  1524, 473.2, 0, 0, 0, 1],  # Golf R 20 Years
    [843,  2370, 448.0, 0, 1, 0, 1],  # GT63 S E Performance
    [1093, 2250, 415.5, 1, 0, 0, 1],  # Taycan GT Manthey
    [1548, 2360, 424.9, 1, 0, 0, 1],  # SU7 Ultra
    [1093, 2250, 427.6, 1, 0, 0, 1],  # Taycan GT Weissach
    [1020, 2190, 455.6, 1, 0, 0, 1],  # Model S Plaid
    [650,  2231, 455.4, 1, 0, 0, 1],  # Ioniq 6 N
    [1003, 2460, 442.8, 1, 0, 1, 0],  # YU7 GT Track Pkg
    [640,  2290, 456.7, 0, 0, 1, 0],  # RS Q8 Performance
    [640,  2247, 458.9, 0, 0, 1, 0],  # Cayenne Turbo GT
    [600,  2270, 462.3, 0, 0, 1, 0],  # RS Q8
    [510,  2015, 469.4, 0, 0, 1, 0],  # GLC 63 S
    [510,  1932, 471.7, 0, 0, 1, 0],  # Stelvio QV
    [570,  2250, 479.7, 0, 0, 1, 0],  # Cayenne Turbo S
])

# 圈速格式化函数
def fmt_lap(s):
    m = int(s // 60)
    sec = s - m * 60
    return f"{m}:{sec:04.1f}"

proto_hp = np.array([1160, 680, 800, 1548, 2000])
proto_kg = np.array([849, 1100, 1350, 1900, 1700])
proto_lap = np.array([319.5, 365.3, 376.0, 382.1, 384.0])
proto_names = ['919 Hybrid Evo', 'VW ID.R', 'Ford GT Mk IV', 'SU7 Ultra Proto', 'Lotus Evija X']

names_list = [
    'AMG ONE', '911 GT2 RS Manthey', '911 GT3 RS Manthey 992.2', 'AMG GT Black Series',
    '911 GT3 RS 992', '911 GT3 Manthey 992.2', 'Mustang GTD', '911 GT3 992',
    '918 Spyder', 'Ferrari 296 GTB', 'Yangwang U9', 'Ferrari 488 Pista',
    'Viper ACR', '718 GT4 RS Manthey', '911 Turbo S 992', 'Rimac Nevera',
    'McLaren 720S', '718 GT4 RS', 'Aventador SVJ',
    'M4 CSL', 'XE SV Project 8', 'M2 CS', 'M3 CS', 'M5 CS', 'M3 CS Touring',
    'RS 3', 'Civic Type R', 'Golf GTI Ed.50', 'Golf R 20 Years',
    'GT63 S E Performance',
    'Taycan GT Manthey', 'SU7 Ultra', 'Taycan GT Weissach', 'Model S Plaid', 'Ioniq 6 N',
    'YU7 GT Track Pkg', 'RS Q8 Performance', 'Cayenne Turbo GT', 'RS Q8',
    'GLC 63 S', 'Stelvio QV', 'Cayenne Turbo S'
]

hp = data[:,0]; kg = data[:,1]; lap = data[:,2]
is_ev = data[:,3]; is_phev = data[:,4]; is_suv = data[:,5]; is_sedan = data[:,6]
pw = hp / kg

# 分类标记
cat_label = np.full(len(data), '两门超跑')
cat_label[is_suv == 1] = 'SUV'
cat_label[is_sedan == 1] = '四门轿跑'

pt_label = np.full(len(data), '纯油')
pt_label[is_ev == 1] = '纯电'
pt_label[is_phev == 1] = '插混'

# 全量回归拟合（用 sklearn）
from sklearn.linear_model import LinearRegression
X_full = np.column_stack([np.log(hp), np.log(kg), is_ev, is_phev, is_suv, is_sedan])
model_full = LinearRegression().fit(X_full, np.log(lap))
y_pred = np.exp(model_full.predict(X_full))
residuals = (lap - y_pred) / y_pred * 100  # 百分比残差

# 功重比 vs 圈速回归线
pw_log = np.log(pw).reshape(-1,1)
pw_model = LinearRegression().fit(pw_log, np.log(lap))
# 回归线范围覆盖全部数据点（含极限组）
pw_min = min(np.min(pw), np.min(proto_hp/proto_kg)) * 0.85
pw_max = max(np.max(pw), np.max(proto_hp/proto_kg)) * 1.15
pw_line_x = np.logspace(np.log10(pw_min), np.log10(pw_max), 100)
pw_line_y = np.exp(pw_model.predict(np.log(pw_line_x).reshape(-1,1)))

# 颜色方案
cat_colors = {'两门超跑': '#e74c3c', '四门轿跑': '#3498db', 'SUV': '#2ecc71'}
pt_symbols = {'纯油': 'circle', '纯电': 'diamond', '插混': 'triangle-up'}
cn_cat_map = {'Coupe': '两门超跑', 'Sedan': '四门轿跑', 'SUV': 'SUV'}
cn_pt_map = {'ICE': '纯油', 'EV': '纯电', 'PHEV': '插混'}

# ========== 图表1: 功重比 vs 圈速 ==========
fig1 = go.Figure()
for cat_en in ['Coupe', 'Sedan', 'SUV']:
    cn = cn_cat_map[cat_en]
    mask = cat_label == cn
    fig1.add_trace(go.Scatter(
        x=pw[mask], y=lap[mask],
        mode='markers',
        name=cn,
        marker=dict(size=10, color=cat_colors[cn], line=dict(width=0.5, color='white')),
        text=[f"{names_list[i]}<br>{hp[i]:.0f}hp / {kg[i]:.0f}kg<br>功重比={pw[i]:.0f} hp/t<br>圈速={fmt_lap(lap[i])}" for i in range(len(data)) if mask[i]],
        hoverinfo='text'
    ))

# 极限组
fig1.add_trace(go.Scatter(
    x=proto_hp/proto_kg, y=proto_lap,
    mode='markers',
    name='极限组（原型车）',
    marker=dict(size=12, color='black', symbol='star', line=dict(width=1, color='gold')),
    text=[f"{proto_names[i]}<br>{proto_hp[i]:.0f}hp/{proto_kg[i]:.0f}kg<br>圈速={fmt_lap(proto_lap[i])}" for i in range(len(proto_hp))],
    hoverinfo='text'
))

# 回归线
fig1.add_trace(go.Scatter(
    x=pw_line_x, y=pw_line_y,
    mode='lines', name=f'全局回归 k={-pw_model.coef_[0]:.4f}',
    line=dict(color='gray', dash='dash', width=1),
    hoverinfo='skip'
))

fig1.update_layout(
    title='功重比 vs 纽北圈速（对数坐标，按车体类型着色）',
    xaxis_title='功重比 (hp/t)', yaxis_title='圈速',
    xaxis=dict(type='log'), yaxis=dict(type='log', autorange='reversed'),
    legend=dict(x=0.02, y=0.98), height=600,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial, sans-serif')
)

# ========== 图表2: 重量 vs 圈速 ==========
fig2 = go.Figure()
for pt_en in ['ICE', 'PHEV', 'EV']:
    cn = cn_pt_map[pt_en]
    mask = pt_label == cn
    fig2.add_trace(go.Scatter(
        x=kg[mask], y=lap[mask],
        mode='markers',
        name=cn,
        marker=dict(size=11, symbol=pt_symbols[cn], line=dict(width=0.5, color='white')),
        text=[f"{names_list[i]}<br>{hp[i]:.0f}hp / {kg[i]:.0f}kg<br>功重比={pw[i]:.0f} hp/t<br>圈速={fmt_lap(lap[i])}" for i in range(len(data)) if mask[i]],
        hoverinfo='text'
    ))

fig2.add_trace(go.Scatter(
    x=proto_kg, y=proto_lap,
    mode='markers', name='极限组',
    marker=dict(size=12, color='black', symbol='star', line=dict(width=1, color='gold')),
    text=[f"{proto_names[i]}<br>{proto_hp[i]:.0f}hp/{proto_kg[i]:.0f}kg<br>圈速={fmt_lap(proto_lap[i])}" for i in range(len(proto_hp))],
    hoverinfo='text'
))

fig2.update_layout(
    title='车重 vs 纽北圈速（按动力架构着色）',
    xaxis_title='车重 (kg)', yaxis_title='圈速',
    yaxis=dict(autorange='reversed'),
    legend=dict(x=0.02, y=0.98), height=600,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial, sans-serif')
)

# ========== 图表3: k值 vs 车重窗格 ==========
bins = [(1300,1500), (1500,1700), (1700,1900), (1900,2100), (2100,2300), (2300,2500)]
bin_labels = ['1300-1500', '1500-1700', '1700-1900', '1900-2100', '2100-2300', '2300-2500']
k_vals = []; kg_mid = []; r2_vals = []; n_vals = []
for lo, hi in bins:
    m = (kg >= lo) & (kg < hi)
    if np.sum(m) < 3: continue
    sx = np.log(pw[m]).reshape(-1,1); sy = np.log(lap[m])
    sm = LinearRegression().fit(sx, sy)
    k_vals.append(-sm.coef_[0])
    r2_vals.append(sm.score(sx, sy))
    kg_mid.append((lo+hi)/2)
    n_vals.append(np.sum(m))

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=kg_mid, y=k_vals,
    mode='lines+markers',
    marker=dict(size=14, color='#e74c3c'),
    line=dict(color='#e74c3c', width=2),
    text=[f"{bl}kg<br>k={k:.4f}<br>R2={r2:.3f}<br>样本数={n}" for bl,k,r2,n in zip(bin_labels, k_vals, r2_vals, n_vals)],
    hoverinfo='text'
))
# 标注重量死亡线
fig3.add_vline(x=2200, line_dash='dash', line_color='red',
              annotation_text='~2.2吨 (k骤降区)', annotation_position='top right',
              annotation_font=dict(size=13, color='red'))

fig3.update_layout(
    title='功重比弹性 k 随车重窗格的变化（2000-2200kg 数据稀疏，虚线为示意）',
    xaxis_title='车重窗格中心 (kg)', yaxis_title='弹性系数 k',
    height=500, template='plotly_white',
    font=dict(family='Microsoft YaHei, SimHei, Arial, sans-serif')
)

# ========== 图表4: 残差柱状图 ==========
res_sorted_idx = np.argsort(residuals)
top10 = res_sorted_idx[:10]
bot10 = res_sorted_idx[-10:]
all_show = np.concatenate([top10, bot10])
colors_bar = ['#27ae60' if residuals[i] < 0 else '#e74c3c' for i in all_show]

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=[names_list[i] for i in all_show],
    y=[residuals[i] for i in all_show],
    marker_color=colors_bar,
    text=[f"{residuals[i]:+.1f}%" for i in all_show],
    textposition='outside',
    textfont=dict(size=11)
))
fig4.update_layout(
    title='效率排名：回归残差（绿色=高效/比预测快，红色=低效/比预测慢）',
    xaxis_title='', yaxis_title='残差（% 快于/慢于预测圈速）',
    height=600, template='plotly_white',
    font=dict(family='Microsoft YaHei, SimHei, Arial, sans-serif'),
    xaxis=dict(tickangle=-30)
)

# ========== 合并到单页HTML ==========
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>纽博格林北环圈速分析</title>
<style>
  body {{ font-family: 'Microsoft YaHei', 'PingFang SC', 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ text-align: center; color: #2c3e50; margin-bottom: 5px; }}
  .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }}
  .chart {{ background: white; border-radius: 8px; padding: 15px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .chart h3 {{ margin: 0 0 10px 0; color: #2c3e50; font-size: 15px; }}
  .footer {{ text-align: center; color: #95a5a6; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
<h1>纽博格林北环圈速分析</h1>
<p class="subtitle">42辆量产车 + 5辆原型车 | 多元对数回归模型 | <a href="../docs/赛道场景性能分析-核心结论.md">完整报告</a></p>

<div class="chart">
  <h3>图表一：功重比 vs 圈速（对数坐标，按车体类型着色）</h3>
  <p style="font-size:13px; color:#666;">灰色虚线 = 功重比全局平均转化效率（弹性 k={-pw_model.coef_[0]:.4f}）。<b>线上方</b>：两门超跑 + 极限组——空力/底盘红利，同样功重比跑得更快。<b>线下方</b>：四门轿跑 + 重电车——受到重量税和（部分车型）马力虚高的拖累。黑色星形 = 极限组原型车天花板。鼠标悬停查看详情。</p>
  {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
</div>

<div class="chart">
  <h3>图表二：车重 vs 圈速（按动力架构着色）</h3>
  <p style="font-size:13px; color:#666;">两端方差接近：1400-1600kg 区间从 911 GT2 RS Manthey（6:43）到 Golf R 20Y（7:53）跨度 70 秒；&gt;2200kg 区间从 Taycan Manthey（6:55）到 Cayenne Turbo S（7:59）跨度 64 秒。纯电（菱形）全在右侧 2100-2500kg 区——电池必然重，但电机马力便宜，同重量下功重比碾压燃油 SUV，圈速更快。<b>纯电的圈速落后 100% 来自车重，但它在重车区的竞争力恰恰来自电驱的低成本大马力。</b></p>
  {fig2.to_html(full_html=False, include_plotlyjs=False)}
</div>

<div class="chart">
  <h3>图表三：功重比弹性系数 k 随车重窗格的变化</h3>
  <p style="font-size:13px; color:#666;">≤2000kg 区间 k≈0.15-0.20（功重比有效）；≥2200kg 区间 k≈0.08（功重比腰斩）。<b>2000-2200kg 数据稀疏，k 的确切转折位置无法精确定位</b>——"死亡线"可能在 2 吨，也可能在 2.2 吨。红色虚线仅为示意，非精确阈值。</p>
  {fig3.to_html(full_html=False, include_plotlyjs=False)}
</div>

<div class="chart">
  <h3>图表四：效率排名（回归残差）</h3>
  <p style="font-size:13px; color:#666;">绿色 = 比预测快（高效），红色 = 比预测慢（低效）。Taycan GT Manthey 全榜最高效，仰望 U9 / Rimac Nevera 全榜最低效。</p>
  {fig4.to_html(full_html=False, include_plotlyjs=False)}
</div>

<div class="footer">
  <p>数据来源：纽博格林官方认证记录（nuerburgring.de/records）+ fastestlaps.com | 分析时间：2026年7月</p>
  <p>项目：rally_cars — 跨场景车辆性能分析框架 | <a href="../../offroad/docs/越野车场景打分标准-核心结论.md">越野体系</a></p>
</div>
</div>
</body>
</html>
"""

# 输出
import os
output_dir = os.path.dirname(os.path.abspath(__file__)) + '/../charts'
os.makedirs(output_dir, exist_ok=True)
output_path = output_dir + '/ring_analysis.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML saved to charts/ring_analysis.html")
print(f"File size: {len(html):,} bytes")
print(f"4 charts generated.")
