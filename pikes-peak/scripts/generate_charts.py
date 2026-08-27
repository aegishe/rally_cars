# -*- coding: utf-8 -*-
"""派克峰登山赛 - 交互式可视化图表"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ========== 加载回归结果 ==========
with open('pikes-peak/charts/regression_results.json', 'r', encoding='utf-8') as f:
    res = json.load(f)

cars = res['cars']
protos = res['protos']
truck_ref = res.get('truck_ref', [])
reg = res['regression']
proto_reg = res['proto_regression']
nbr = res['comparison_nbr']

# 转换为数组
hp = np.array([c['hp'] for c in cars])
kg = np.array([c['weight'] for c in cars])
lap = np.array([c['lap_s'] for c in cars])
pw = np.array([c['pw_ratio'] for c in cars])
residuals = np.array([c['residual_pct'] for c in cars])
names = [c['name'] for c in cars]
pt_labels = [c['powertrain'] for c in cars]
body_labels = [c['body'] for c in cars]
aero_labels = [c['aero'] for c in cars]
mod_levels = np.array([c.get('mod_level', '未知') for c in cars])
mod_details = np.array([c.get('mod_detail', '') for c in cars])

# 圈速格式化
def fmt_lap(s):
    m = int(s // 60)
    sec = s - m * 60
    return f"{m}:{sec:04.1f}"

# 组合标签: 动力+车体
pt_cn = {'ICE': '燃油', 'EV': '纯电', 'PHEV': '混动'}
body_short = {'Coupe': '超跑', 'Sedan': '轿跑', 'SUV': 'SUV', 'Truck': '皮卡', 'Proto': '原型车'}
combo_labels = [f"{pt_cn.get(p, p)}{body_short.get(b, b)}" for p, b in zip(pt_labels, body_labels)]

# 组合颜色方案（7组）
combo_colors = {
    '燃油超跑': '#e74c3c',
    '混动超跑': '#f39c12',
    '燃油轿跑': '#1abc9c',
    '纯电轿跑': '#3498db',
    '燃油SUV': '#27ae60',
    '纯电SUV': '#2ecc71',
    '纯电皮卡': '#8e44ad',
}
pt_colors = {'ICE': '#e74c3c', 'EV': '#3498db', 'PHEV': '#f39c12'}  # 图2/3用
aero_colors = {'Race': '#000000', 'Modified': '#e67e22', 'Stock': '#95a5a6'}
aero_cn = {'Race': '赛事空力', 'Modified': '改装空力', 'Stock': '原厂空力'}

# ========== 图1: 功重比 vs 圈速 ==========
fig1 = go.Figure()

for combo in sorted(set(combo_labels)):
    mask = np.array([c == combo for c in combo_labels])
    if not any(mask): continue
    color = combo_colors.get(combo, '#95a5a6')
    fig1.add_trace(go.Scatter(
        x=pw[mask], y=lap[mask],
        mode='markers', name=combo,
        marker=dict(size=11, color=color, line=dict(width=0.5, color='white')),
        text=[f"{n}<br>{hp[mask][i]:.0f}hp / {kg[mask][i]:.0f}kg<br>PW={pw[mask][i]:.1f} hp/t<br>{fmt_lap(lap[mask][i])}<br>改装: {mod_levels[mask][i]} - {mod_details[mask][i]}" for i, n in enumerate(np.array(names)[mask])],
        hoverinfo='text'
    ))

# 极限组
proto_hp_arr = np.array([p['hp'] for p in protos])
proto_kg_arr = np.array([p['weight'] for p in protos])
proto_lap_arr = np.array([p['lap_s'] for p in protos])
proto_names = [p['name'] for p in protos]
proto_pw = proto_hp_arr / proto_kg_arr

fig1.add_trace(go.Scatter(
    x=proto_pw, y=proto_lap_arr,
    mode='markers', name='Unlimited (原型)',
    marker=dict(size=14, color='black', symbol='star', line=dict(width=1, color='gold')),
    text=[f"{pn}<br>{proto_hp_arr[i]:.0f}hp/{proto_kg_arr[i]:.0f}kg<br>{fmt_lap(proto_lap_arr[i])}" for i, pn in enumerate(proto_names)],
    hoverinfo='text'
))

# 皮卡参照（不参与回归）
if truck_ref:
    truck_pw = np.array([t['pw_ratio'] for t in truck_ref])
    truck_lap = np.array([t['lap_s'] for t in truck_ref])
    truck_names = [t['name'] for t in truck_ref]
    truck_hp = np.array([t['hp'] for t in truck_ref])
    truck_kg = np.array([t['weight'] for t in truck_ref])
    fig1.add_trace(go.Scatter(
        x=truck_pw, y=truck_lap,
        mode='markers', name='皮卡参照 (不参与回归)',
        marker=dict(size=13, color='#8e44ad', symbol='x', line=dict(width=2, color='#8e44ad')),
        text=[f"{tn}<br>{truck_hp[i]:.0f}hp/{truck_kg[i]:.0f}kg<br>越野皮卡 悬架+空力+重量劣势<br>{fmt_lap(truck_lap[i])}" for i, tn in enumerate(truck_names)],
        hoverinfo='text'
    ))

# 回归线
pw_line_x = np.logspace(np.log10(0.1), np.log10(2.0), 100)
from sklearn.linear_model import LinearRegression
pw_model = LinearRegression().fit(np.log(pw).reshape(-1,1), np.log(lap))
pw_line_y = np.exp(pw_model.predict(np.log(pw_line_x).reshape(-1,1)))
k_val = -pw_model.coef_[0]

fig1.add_trace(go.Scatter(
    x=pw_line_x, y=pw_line_y,
    mode='lines', name=f'量产回归 k={k_val:.3f}',
    line=dict(color='gray', dash='dash', width=1.5),
    hoverinfo='skip'
))

# 图1 图例保持左上
fig1.update_layout(
    title=dict(text='<b>图1: 功重比 vs 派克峰圈速</b><br><sub>对数坐标 | 动力+车体双定义着色 | 星=原型 X=皮卡参照 | 虚线=回归</sub>', font=dict(size=14)),
    xaxis_title='功重比 (hp/t)', yaxis_title='圈速',
    xaxis=dict(type='log', dtick=1), yaxis=dict(type='log', autorange='reversed'),
    legend=dict(x=0.02, y=0.98), height=600,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial')
)

# ========== 图2: 重量 vs 圈速 ==========
fig2 = go.Figure()

for combo in sorted(set(combo_labels)):
    mask = np.array([c == combo for c in combo_labels])
    if not any(mask): continue
    color = combo_colors.get(combo, '#95a5a6')
    fig2.add_trace(go.Scatter(
        x=kg[mask], y=lap[mask],
        mode='markers', name=combo,
        marker=dict(size=11, color=color, line=dict(width=0.5, color='white')),
        text=[f"{n}<br>{hp[mask][i]:.0f}hp / {kg[mask][i]:.0f}kg<br>PW={pw[mask][i]:.1f}<br>{fmt_lap(lap[mask][i])}<br>改装: {mod_levels[mask][i]} - {mod_details[mask][i]}" for i, n in enumerate(np.array(names)[mask])],
        hoverinfo='text'
    ))

fig2.add_trace(go.Scatter(
    x=proto_kg_arr, y=proto_lap_arr,
    mode='markers', name='Unlimited',
    marker=dict(size=14, color='black', symbol='star', line=dict(width=1, color='gold')),
    text=[f"{pn}<br>{proto_hp_arr[i]:.0f}hp/{proto_kg_arr[i]:.0f}kg<br>{fmt_lap(proto_lap_arr[i])}" for i, pn in enumerate(proto_names)],
    hoverinfo='text'
))

# 皮卡参照
if truck_ref:
    fig2.add_trace(go.Scatter(
        x=truck_kg, y=truck_lap,
        mode='markers', name='皮卡参照 (不参与回归)',
        marker=dict(size=13, color='#8e44ad', symbol='x', line=dict(width=2, color='#8e44ad')),
        text=[f"{tn}<br>{truck_hp[i]:.0f}hp/{truck_kg[i]:.0f}kg<br>{fmt_lap(truck_lap[i])}" for i, tn in enumerate(truck_names)],
        hoverinfo='text'
    ))

# 改装空力车：空心圈标注（打破"越重越慢"的主力）
mod_mask = np.array([a == 'Modified' for a in aero_labels])
if any(mod_mask):
    fig2.add_trace(go.Scatter(
        x=kg[mod_mask], y=lap[mod_mask],
        mode='markers', name='改装空力',
        marker=dict(size=16, color='rgba(255,255,255,0)', line=dict(width=1.6, color='#333')),
        text=[f"{n}<br>改装空力<br>{mod_details[mod_mask][i]}" for i, n in enumerate(np.array(names)[mod_mask])],
        hoverinfo='text'
    ))

fig2.update_layout(
    title=dict(text='<b>图2: 车重 vs 派克峰圈速</b><br><sub>动力+车体着色 | 空心圈=改装空力 | 星=原型 X=皮卡参照 | 原厂同车手口径下才大致越重越慢</sub>', font=dict(size=14)),
    xaxis_title='车重 (kg)', yaxis_title='圈速',
    yaxis=dict(autorange='reversed'),
    legend=dict(x=0.98, y=0.98, xanchor='right', yanchor='top'), height=600,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial')
)

# ========== 图3: 残差柱状图 ==========
sorted_idx = np.argsort(residuals)
sorted_names = np.array(names)[sorted_idx]
sorted_res = residuals[sorted_idx]
sorted_pt = np.array(pt_labels)[sorted_idx]
colors = [pt_colors.get(p, '#95a5a6') for p in sorted_pt]
text_colors = ['green' if r < 0 else 'red' if r > 0 else 'gray' for r in sorted_res]

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=sorted_res, y=sorted_names,
    orientation='h',
    marker=dict(color=colors, line=dict(width=0)),
    text=[f"{r:+.1f}%" for r in sorted_res],
    textposition='outside',
    textfont=dict(color=text_colors, size=11),
))

fig3.add_vline(x=0, line_dash='solid', line_color='black', line_width=1)

fig3.update_layout(
    title=dict(text='<b>图3: 残差排行</b><br><sub>负残差=高效(比预测快) | 正残差=低效(比预测慢) | 按动力架构着色</sub>', font=dict(size=14)),
    xaxis_title='残差 (ln实际 - ln预测)',
    height=500,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial'),
    margin=dict(l=200, r=50, t=80, b=50)
)

# ========== 图4: 跨场景对比 ==========
fig4 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('<b>功重比弹性 k (越大越有效)</b>', '<b>重量惩罚比 (重量每+1%需马力+?%)</b>'),
    specs=[[{'type': 'xy'}, {'type': 'xy'}]]
)

# 使用回归结果中的 k
pw_elasticity_k = reg.get('pw_elasticity_k', 0.110)

# 计算ICE k
ice_mask = np.array([p == 'ICE' for p in pt_labels])
if sum(ice_mask) >= 3:
    ice_k_model = LinearRegression().fit(np.log(pw[ice_mask]).reshape(-1,1), np.log(lap[ice_mask]))
    ice_k = -ice_k_model.coef_[0]
else:
    ice_k = 0.058

scenes_k = ['Pikes Peak<br>量产', 'NBR<br>全量', 'NBR<br>>2200kg', 'Pikes Peak<br>纯油', 'NBR<br>纯油']
k_values = [pw_elasticity_k, 0.15, 0.08, ice_k, 0.166]
colors_k = ['#e74c3c', '#3498db', '#3498db', '#e74c3c', '#3498db']

fig4.add_trace(go.Bar(
    x=scenes_k, y=k_values,
    marker=dict(color=colors_k),
    text=[f"{v:.3f}" for v in k_values],
    textposition='outside',
    textfont=dict(size=13)
), row=1, col=1)

# 重量惩罚比
wpr_reg = reg.get('weight_penalty_ratio')
if wpr_reg is None:
    wpr_reg = 1.89
# 计算 Pikes Peak ICE WPR
wpr_scenes = ['Pikes Peak<br>量产', 'NBR<br>全量', 'NBR<br>ICE', 'NBR<br>Proto']
wpr_values = [wpr_reg, 1.73, 1.61, 4.34]
wpr_colors = ['#e74c3c', '#3498db', '#3498db', '#3498db']

fig4.add_trace(go.Bar(
    x=wpr_scenes, y=wpr_values,
    marker=dict(color=wpr_colors),
    text=[f"{v:.2f}" for v in wpr_values],
    textposition='outside',
    textfont=dict(size=13)
), row=1, col=2)

fig4.update_layout(
    title=dict(text='<b>图4: 派克峰 vs 纽北 — 核心指标对比</b><br><sub>红色=派克峰 | 蓝色=纽北 | k=功重比弹性 | WPR=重量惩罚比</sub>', font=dict(size=14)),
    height=450, showlegend=False,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial')
)

# ========== 图5: 空力水平 vs 圈速分组 ==========
fig5 = go.Figure()
for aero_en in ['Modified', 'Stock']:
    cn = aero_cn[aero_en]
    mask = np.array([a == aero_en for a in aero_labels])
    if not any(mask): continue
    fig5.add_trace(go.Box(
        y=lap[mask], name=cn,
        marker_color=aero_colors[aero_en],
        boxmean=True,
        text=[f"{n}: {fmt_lap(l)}" for n, l in zip(np.array(names)[mask], lap[mask])],
        hoverinfo='text'
    ))

fig5.update_layout(
    title=dict(text='<b>图5: 空力水平 vs 圈速分布</b><br><sub>改装空力(TA1/Exhibition改装) vs 原厂空力 | 框内线=均值</sub>', font=dict(size=14)),
    yaxis_title='圈速', yaxis=dict(autorange='reversed'),
    height=450,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial')
)

# ========== 图6: 海拔衰减效应 ==========
fig6 = go.Figure()

# 模拟海拔-功率曲线（定性）
altitude = np.array([0, 1000, 2000, 2862, 3500, 4000, 4300])
na_power = 100 * (1 - altitude * 0.0001 * 0.9)  # 约每1000m掉10%
turbo_power = 100 * np.clip(1 - (altitude - 2500) * 0.00005, 0.7, 1.0)  # 2500m后有衰减
ev_power = np.full_like(altitude, 100.0)  # 纯电免疫

fig6.add_trace(go.Scatter(x=altitude, y=na_power, mode='lines+markers', name='NA发动机', line=dict(color='red', width=2)))
fig6.add_trace(go.Scatter(x=altitude, y=turbo_power, mode='lines+markers', name='涡轮发动机', line=dict(color='orange', width=2)))
fig6.add_trace(go.Scatter(x=altitude, y=ev_power, mode='lines+markers', name='纯电', line=dict(color='blue', width=2)))

# 标记起点和终点
fig6.add_vline(x=2862, line_dash='dash', line_color='green', line_width=1, annotation_text='起点', annotation_position='top')
fig6.add_vline(x=4300, line_dash='dash', line_color='gray', line_width=1, annotation_text='终点', annotation_position='top')

fig6.update_layout(
    title=dict(text='<b>图6: 海拔-功率衰减曲线 (定性)</b><br><sub>NA每1000m掉~10% | 涡轮2500m后衰减 | 纯电完全免疫</sub>', font=dict(size=14)),
    xaxis_title='海拔 (m)', yaxis_title='可用功率 (海平面%)',
    height=450,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial'),
    legend=dict(x=0.02, y=0.02)
)

# ========== 图7: 改装级别 vs 残差 ==========
mod_order = ['原厂', '厂商改装', '私人改装']
mod_colors_map = {'原厂': '#27ae60', '厂商改装': '#e67e22', '私人改装': '#e74c3c'}
fig7 = go.Figure()

for mod_lv in mod_order:
    mask = np.array([m == mod_lv for m in mod_levels])
    if not any(mask): continue
    fig7.add_trace(go.Scatter(
        x=[mod_lv] * sum(mask), y=residuals[mask],
        mode='markers', name=mod_lv,
        marker=dict(size=13, color=mod_colors_map[mod_lv], line=dict(width=1, color='white')),
        text=[f"{n}<br>残差: {residuals[mask][i]:+.1f}%<br>{mod_details[mask][i]}" for i, n in enumerate(np.array(names)[mask])],
        hoverinfo='text'
    ))

fig7.add_hline(y=0, line_dash='dash', line_color='gray', line_width=1)
fig7.update_layout(
    title=dict(text='<b>图7: 改装级别 vs 残差</b><br><sub>负=高效 | 正=低效 | 绿=原厂 橙=厂商改装 红=私人改装</sub>', font=dict(size=14)),
    xaxis_title='改装级别', yaxis_title='残差 (%)',
    height=450,
    template='plotly_white', font=dict(family='Microsoft YaHei, SimHei, Arial')
)

# ========== 组合输出 ==========
charts = {
    'fig1_pw_vs_lap': fig1.to_json(),
    'fig2_weight_vs_lap': fig2.to_json(),
    'fig3_residuals': fig3.to_json(),
    'fig4_cross_scene': fig4.to_json(),
    'fig5_aero_box': fig5.to_json(),
    'fig6_altitude': fig6.to_json(),
    'fig7_mod_residual': fig7.to_json(),
}

# AeroMod系数（从回归结果中提取）
aero_coeff = next((c['value'] for c in reg['coeffs'] if c['name'] == 'AeroMod'), -0.093)
aero_pct = abs(100 * (np.exp(aero_coeff) - 1))
aero_p_val = next((c['p'] for c in reg['coeffs'] if c['name'] == 'AeroMod'), 0.02)

# 生成完整 HTML
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>派克峰登山赛性能分析 - 交互式可视化</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; background: #f5f5f5; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header p {{ font-size: 14px; opacity: 0.8; }}
        .summary {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #e74c3c; }}
        .card .label {{ font-size: 13px; color: #666; margin-top: 4px; }}
        .card .compare {{ font-size: 12px; color: #999; margin-top: 2px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px 40px; }}
        .chart {{ background: white; border-radius: 10px; margin: 20px 0; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .key-findings {{ background: white; border-radius: 10px; margin: 20px 0; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .key-findings h3 {{ margin-bottom: 15px; color: #1a1a2e; }}
        .key-findings ul {{ padding-left: 20px; }}
        .key-findings li {{ margin: 8px 0; line-height: 1.6; }}
        .highlight {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
<div class="header">
    <h1>Pikes Peak International Hill Climb</h1>
    <p>2011年后铺装路面时代 | 19.99km / 156弯 / 2862m→4302m / 7.2%坡度 | 分析与可视化</p>
</div>

<div class="summary">
    <div class="card">
        <div class="value">13</div>
        <div class="label">量产基础车辆</div>
        <div class="compare">+4台原型 +1台皮卡参照</div>
    </div>
    <div class="card">
        <div class="value">{reg['r2']:.0%}</div>
        <div class="label">R² (全量回归)</div>
        <div class="compare">调整R²={reg['r2_adj']:.0%}</div>
    </div>
    <div class="card">
        <div class="value">{reg['weight_penalty_ratio']:.1f}x</div>
        <div class="label">重量惩罚比</div>
        <div class="compare">纽北全量: 1.73x</div>
    </div>
    <div class="card">
        <div class="value">{reg['pw_elasticity_k']:.3f}</div>
        <div class="label">功重比弹性 k</div>
        <div class="compare">纽北全量: 0.15</div>
    </div>
</div>

<div class="container">
    <div class="chart" id="chart1"></div>
    <div class="chart" id="chart2"></div>

    <div class="key-findings" style="margin-top:-10px;">
        <p><b>看图说话</b>：派克峰下车重与圈速在原厂、同车手口径下大致<b>越重越慢</b>，但不是无一反例——几辆"重却快"的车（ZR1X、Ioniq 5 N TA、Model S Plaid改、宾利刷纪录的 Continental GT）都是改装空力或职业车手在起作用，图里已用空心圈标出改装空力。爬坡功率税（m·g·sinθ·v）是重量的直接体现：<b>每多100kg，无论马力多大，先被扣2-3hp用于克服重力</b>，没有下坡可以"回本"。对比纽北——起伏赛道上下坡重力互相抵消，重量只在弯道中造成二阶惩罚，因此重量-圈速关系远不如派克峰干净。注意：这笔税是<b>常数项减法</b>（相对海拔衰减的比例打折而言），它没有把回归弹性推高（派克峰惩罚比 1.75 ≈ 纽北全量 1.73）——税在"绝对功率口径"杀伤，不在"弹性口径"。</p>
    </div>

    <div class="key-findings">
        <h3>核心发现 #1: 重量惩罚比 <span class="highlight">{reg['weight_penalty_ratio']:.1f}（点估计）</span> 与纽北全量 1.73 几乎相同</h3>
        <ul>
            <li>重量惩罚比 = <span class="highlight">{reg['weight_penalty_ratio']:.1f}</span>（N=13，两系数均不显著）；纽北 43 车全量 1.73（双显著）——<b>"上坡放大惩罚"的直觉被数据否定</b>（2026-08 勘误：早期以过时口径"纽北 1.0"为基准的"1.75 倍"结论已作废）</li>
            <li>成因：爬坡税 P=m·g·sinθ·v 是<b>常数项减法</b>（不改变功重比排序），且 ln(重量) 项已隐式吸收爬坡惩罚——重车慢 → 均速低 → 爬坡扣除小（负反馈）</li>
            <li>每多 100kg 先被扣 2-3hp 克服重力——这笔税在<b>绝对功率口径</b>杀伤，不在弹性口径</li>
            <li>派克峰真正的独特：<b>马力弹性腰斩</b>（-0.036 vs 纽北 -0.066，p=0.46 不显著）+ <b>原厂同车手口径下车重-圈速单调递增</b>（改装空力/车手会打穿）</li>
            <li><b>纯电在派克峰与纯油打平</b> (0.0% vs 0.0%)——高海拔免疫刚好抵消重量劣势，与纽北"控制重量后打平"的原因不同</li>
        </ul>
    </div>

    <div class="chart" id="chart3"></div>

    <div class="key-findings">
        <h3>核心发现 #2: 马力在派克峰是"软通货" — <span class="highlight">k 仅 {pw_elasticity_k:.3f}</span></h3>
        <ul>
            <li>功重比弹性 k = <span class="highlight">{pw_elasticity_k:.3f}</span>，低于纽北的 0.15</li>
            <li>马力+10% 只能换 1.16% 圈速，比纽北的 1.5% 低 23%</li>
            <li>这还没算高海拔衰减：NA 账面马力在山顶实际掉了 <span class="highlight">35-40%</span></li>
            <li><b>派克峰考的不是马力大，是马力能剩多少</b> — 这也是纯电残差能和纯油打平的根本原因</li>
            <li>功重比非线性也很奇怪：轻量 <1800kg 区间 k = 0.008（近乎完全无效），中量 1800-2200kg k = 0.119，重量 >2200kg k = 0.140 — <b>越重功重比效率反而越高</b>（可能被空力混淆）</li>
        </ul>
    </div>

    <div class="chart" id="chart4"></div>

    <div class="key-findings">
        <h3>核心发现 #3: 改装空力带来 <span class="highlight">{aero_pct:.1f}%</span> 圈速提升 — 统计显著 (p={aero_p_val:.3f})</h3>
        <ul>
            <li>虽然 4300m 山顶空气密度只有海平面 60%，但改装空力仍然是派克峰最有效的性能杠杆</li>
            <li>Porsche GT2 RS Clubsport、Corvette ZR1X、Hyundai Ioniq 5 N TA 等改装车型显著快于原厂</li>
            <li><b>空力在稀薄空气中仍然有效</b> — 下压力和阻力等比例打折，但下压力的边际收益（弯速提升）不随空气密度线性下降</li>
        </ul>
    </div>

    <div class="chart" id="chart5"></div>
    <div class="chart" id="chart6"></div>
    <div class="chart" id="chart7"></div>

    <div class="key-findings">
        <h3>核心发现 #4: 纯电 vs 纯油 — <span class="highlight">在派克峰打平</span></h3>
        <ul>
            <li>全量回归中纯电 dummy = +3.6% (不显著 p=0.12) — 控制马力+重量+空力后差异不大</li>
            <li>纯电和纯油平均残差完全相同 (0.0%)</li>
            <li>这是两股力量的平衡：<b>纯电高海拔免疫</b>（优势）≈ <b>纯电重量更大</b>（劣势，派克峰放大）</li>
            <li>残差冠军是 Hyundai Ioniq 5 N TA (-3.5%) — 改装空力+电动免疫+AWD → 派克峰最优组合</li>
            <li>纯电的高海拔优势在派克峰被爬坡重力惩罚对冲 — 和纽北"纯电没系统性劣势"形成有趣对比</li>
        </ul>
    </div>

    <div class="key-findings">
        <h3>核心发现 #5: 派克峰 ≠ 纽北 × 高原 — <span class="highlight">它是独立物理场景</span></h3>
        <ul>
            <li>派克峰的重量惩罚比 ({reg['weight_penalty_ratio']:.1f}x，不显著估计) 与纽北全量 (1.73x) 几乎相同，小于纽北极限组 (4.34x)——差异在马力弹性与统计性质，不在惩罚比</li>
            <li>功重比转化效率更低 (k={pw_elasticity_k:.3f} vs 0.15) — 爬坡消耗了账面马力的可用部分</li>
            <li>和越野高原山路不同：派克峰不需要考虑保电/散热（7-10分钟一圈），核心约束是 <b>爬坡重力 + 高海拔功率衰减 + 悬架-路面耦合</b></li>
            <li>样本量小 (N=13) 是所有结论的 caveat — 后续需要更多量产车来验证这些初步发现</li>
        </ul>
    </div>

    <div class="key-findings">
        <h3>核心发现 #6: 欧洲平衡 vs 美国极端 — <span class="highlight">赛事文化决定数据能回答什么问题</span></h3>
        <table style="width:100%; border-collapse:collapse; margin:10px 0;">
            <tr style="background:#f0f0f0;"><th style="padding:8px; text-align:left;"></th><th style="padding:8px;">欧洲/国际体系</th><th style="padding:8px;">美国体系</th></tr>
            <tr><td style="padding:8px; font-weight:bold;">赛道</td><td style="padding:8px;">纽北：量产认证严谨，规则精细，42辆干净数据</td><td style="padding:8px;">派克峰：组别松散，奔放改装，13辆中仅8辆真原厂</td></tr>
            <tr style="background:#fafafa;"><td style="padding:8px; font-weight:bold;">越野</td><td style="padding:8px;">达喀尔：万公里综合耐力，考验全能平衡</td><td style="padding:8px;">巴哈1000：极端沙漠冲刺，要么赢要么碎</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">技术哲学</td><td style="padding:8px;"><b>工程师思维</b>：先定义"量产"，再在框内公平竞争</td><td style="padding:8px;"><b>牛仔思维</b>：先放开规则，谁能上山谁赢，规则是后补的</td></tr>
            <tr style="background:#fafafa;"><td style="padding:8px; font-weight:bold;">典型代表</td><td style="padding:8px;">919 Evo（平衡极致）、卫士 OCTA（全面防护）</td><td style="padding:8px;">I.D. R（纯电一击脱离）、SuperTruck（1600hp 野蛮暴力）</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">分析价值</td><td style="padding:8px;">数据干净：适合 <b>架构效率对比</b>（R2 达 0.91）</td><td style="padding:8px;">数据被改装/车手/规则污染：适合 <b>上限探索</b></td></tr>
        </table>
        <p>这种文化差异解释了派克峰分析的深层困境——我们试图用纽北那套"严格分类+对数回归"的方法来量化架构效率，但美国式的极端赛事本质上不鼓励"公平对比"。他们鼓励的是"你能造出多快的东西，我们就让你跑"。所以同一年你看到 I.D. R（7:57）和 Bentley Bentayga（10:49）同场竞技——这在纽北是不可想象的事。</p>
        <p><b>反向价值</b>：正因为规则松散，派克峰的数据包含了纽北永远看不到的组合——纯电 SUV 和燃油超跑在 4300m 海拔同场 pk、改装空力对民用山路圈速的实际贡献、皮卡在山路上到底比 SUV 慢多少。这些不是"噪声"，是<b>上限探索的价值</b>。两种文化各回答了不同的问题。</p>
    </div>
</div>

<script>
    document.getElementById('chart1').innerHTML = '';
    Plotly.newPlot('chart1', {charts['fig1_pw_vs_lap']});
    document.getElementById('chart2').innerHTML = '';
    Plotly.newPlot('chart2', {charts['fig2_weight_vs_lap']});
    document.getElementById('chart3').innerHTML = '';
    Plotly.newPlot('chart3', {charts['fig3_residuals']});
    document.getElementById('chart4').innerHTML = '';
    Plotly.newPlot('chart4', {charts['fig4_cross_scene']});
    document.getElementById('chart5').innerHTML = '';
    Plotly.newPlot('chart5', {charts['fig5_aero_box']});
    document.getElementById('chart6').innerHTML = '';
    Plotly.newPlot('chart6', {charts['fig6_altitude']});
    document.getElementById('chart7').innerHTML = '';
    Plotly.newPlot('chart7', {charts['fig7_mod_residual']});
</script>
</body>
</html>"""

with open('pikes-peak/charts/pikes_peak_analysis.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Charts generated: pikes-peak/charts/pikes_peak_analysis.html")
