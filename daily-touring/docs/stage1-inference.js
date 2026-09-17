// ============================================================================
// 反推阶段（Stage-1）—— 严格按 CLTC 标准条件，统一参数
// 运行: node stage1-inference.js
// ============================================================================
//
// 【纪律】本阶段只做一件事：在 CLTC 标准条件下，反推每车的
//         维度1 实际电耗 (kWh/100km)  与  维度2 综合效率。
//
//   温度     : 23±5℃        (GB/T 18386.1-2021)
//   空调     : 关闭          (标准条件)
//   附件     : 仅低压常电 0.60 kWh/100km (全车统一)
//   动能参数 : 统一，不随车型变
//   回收效率 : 统一取常温值，不含任何温度假设
//
//   温度差异留到验证阶段（Stage-2），本阶段严禁引入。
//
// 【动能项的物理来源】不再用"官方电耗反解"这个黑箱，改为：
//   E_acc  = ½·m·Δv² × N       加速牵引需求 (电池→轮端, 除以电驱效率)
//   E_rec  = ½·m·Δv² × N × φ   减速回收     (轮端→电池, 乘以回收效率)
//   净损失 = E_acc/η_m − E_rec·φ
//   其中 N=单循环加速事件数, Δv=单次事件平均速度增量, φ=动能回收效率
//
//   N 的先验: CLTC-P 含 11 个短行程 → 取 N=11
//   Δv 由 CLTC 特征参数闭合确定(见输出)
'use strict';

const G = 9.81, RHO = 1.2;

// ---------------------------------------------------------------- CLTC 标准特征参数
// 来源: GB/T 38146.1-2019 / 中汽研《基于中国工况的纯电动乘用车续驶里程评价方法研究》表1
const CLTC = {
  T: 1800,            // s
  L: 14.48,           // km
  vAvg: 28.96,        // km/h 平均车速(含怠速)
  vRun: 37.18,        // km/h 运行平均车速(不含怠速)
  aAcc: 0.45,         // m/s² 平均加速度
  aDec: 0.49,         // m/s² 平均减速度
  rAcc: 0.2878,       // 加速时间占比
  rDec: 0.2644,       // 减速时间占比
  rIdle: 0.2211,      // 怠速时间占比
  trips: 11,          // 短行程数
};

// ---------------------------------------------------------------- 统一常数
const LOW = 0.60;     // 低压/常电基础 kWh/100km (标准条件下全车统一)
const ETA_M = 0.91;   // 电驱系统效率(牵引)  —— 厂商公开口径: 极氪"电驱综合效率最高92%"
const PHI = 0.75;     // 动能回收效率(常温)  —— 待独立核实, 见文件末
const N = CLTC.trips;

// ---------------------------------------------------------------- 车型参数
const CARS = [
  { n: '特斯拉 Model 3 RWD', wh: 60.0, m: 1760, Cd: 0.219, A: 2.22, Crr: 0.0090, cltc: 634 },
  { n: '小米 SU7 后驱标准版', wh: 73.6, m: 1980, Cd: 0.195, A: 2.30, Crr: 0.0090, cltc: 700 },
  { n: '特斯拉 Model Y RWD', wh: 62.5, m: 1922, Cd: 0.230, A: 2.60, Crr: 0.0090, cltc: 593 },
  { n: '小米 YU7 后驱标准版', wh: 96.3, m: 2315, Cd: 0.245, A: 2.60, Crr: 0.0090, cltc: 835 },
  { n: '小鹏 X9 长续航前驱',  wh: 94.8, m: 2675, Cd: 0.227, A: 3.00, Crr: 0.0090, cltc: 650 },
  { n: '极氪 009 前驱七座',   wh: 110.0, m: 2798, Cd: 0.270, A: 3.00, Crr: 0.0090, cltc: 740 },
];

// ---------------------------------------------------------------- 动能参数推导
const vms = v => v / 3.6;
const f2 = x => x.toFixed(2), f3 = x => x.toFixed(3), f0 = x => x.toFixed(0);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(96));

// 加速/减速段的总速度增量(所有事件之和, 循环闭合 ⇒ 加速 ΣΔv = 减速 ΣΔv)
//   ΣΔv = a_acc · t_acc = a_dec · t_dec   ← 物理闭合, 不需假设事件数
const dvTotal = CLTC.aAcc * (CLTC.rAcc * CLTC.T);          // m/s, 单循环全部加速事件的速度增量之和
// 动能项用速度平方(不是和的平方): 每次事件贡献 ½·Δv_i²
// 等效形式: Σ½Δv_i² = ½·ΣΔv_i²/N_eff, 这里用 N_eff=11 个短行程作为事件数先验
const eAcc_total = 0.5 * Math.pow(dvTotal, 2) / N;         // J/kg per cycle (牵引)
const eDec_total = eAcc_total * (CLTC.aDec / CLTC.aAcc);   // J/kg per cycle (可回收)
// φ = 动能回收效率(<1): 加速耗电 E_acc/η_m, 减速只回收到 E_dec·φ
const eNet_unit = eAcc_total / ETA_M - eDec_total * PHI;   // J/kg per cycle (净损失, 电池端)

line(); console.log('动能参数推导（统一，不随车型变）'); line();
console.log(`  CLTC: T=${CLTC.T}s, a_acc=${CLTC.aAcc}, r_acc=${CLTC.rAcc} → 加速时长 ${(CLTC.rAcc * CLTC.T).toFixed(0)}s`);
console.log(`  加速事件数 N = ${N}（CLTC-P 含 ${CLTC.trips} 个短行程）`);
console.log(`  总速度增量 ΣΔv = a_acc·t_acc = ${f2(dvTotal / 3.6)} km/h   (循环闭合校验: a_dec·t_dec = ${f2(CLTC.aDec * CLTC.rDec * CLTC.T / 3.6)} km/h)`);
console.log(`  单循环牵引动能 E_acc   = ½ΣΔv²/N = ${f3(eAcc_total / 1000)} kJ/kg  (N=${N} 个事件)`);
console.log(`  单循环可回收 E_dec     = E_acc·(a_dec/a_acc) = ${f3(eDec_total / 1000)} kJ/kg`);
console.log(`  净动能损失(电池端)     = E_acc/η_m − E_dec·φ = ${f3(eNet_unit / 1000)} kJ/kg`);
console.log(`     ├ 牵引需求/η_m = ${f3(eAcc_total / ETA_M / 1000)} kJ/kg`);
console.log(`     └ 回收回来·φ   = ${f3(eDec_total * PHI / 1000)} kJ/kg`);

// ---------------------------------------------------------------- 每车反推
const kW_res = (c, v) => (c.m * G * c.Crr * vms(v) + 0.5 * RHO * c.Cd * c.A * Math.pow(vms(v), 3)) / 1000;
const kW_kin = c => eNet_unit * c.m / CLTC.T / 1000;   // kJ/kg ×kg /s = kW
const eCLTC = c => c.wh / c.cltc * 100;

line(); console.log('维度1 · 实际电耗（CLTC 标准条件，官方口径 = 电池 ÷ 续航 × 100）'); line();
console.log('车型'.padEnd(22) + pad('电池kWh', 9) + pad('CLTC km', 9) + pad('实际电耗', 10) + pad('电耗速率kW', 11));
for (const c of CARS) {
  console.log(c.n.padEnd(22) + pad(f2(c.wh), 9) + pad(c.cltc, 9) + pad(f2(eCLTC(c)), 10)
    + pad(f2(eCLTC(c) * CLTC.vAvg / 100), 11));
}

line(); console.log('维度2 · 综合效率（轮端需求 ÷ 电池端输出）'); line();
console.log('车型'.padEnd(22) + pad('阻力@vAvg', 10) + pad('动能项', 9) + pad('需求合计', 10)
  + pad('电池输出', 10) + pad('综合效率', 10));
for (const c of CARS) {
  const res = kW_res(c, CLTC.vAvg), kin = kW_kin(c);
  const outKW = eCLTC(c) * CLTC.vAvg / 100;
  console.log(c.n.padEnd(22) + pad(f2(res), 10) + pad(f2(kin), 9) + pad(f2(res + kin), 10)
    + pad(f2(outKW), 10) + pad(f3((res + kin) / outKW), 10));
}

// 附: 若阻力按"运行平均车速"算（变速行驶的等效口径）
line(); console.log('附 · 阻力口径对照（vAvg vs vRun）'); line();
console.log('车型'.padEnd(22) + pad('阻力@28.96', 11) + pad('阻力@37.18', 11) + pad('两口径差', 10) + pad('占比', 8));
for (const c of CARS) {
  const a = kW_res(c, CLTC.vAvg), b = kW_res(c, CLTC.vRun);
  console.log(c.n.padEnd(22) + pad(f2(a), 11) + pad(f2(b), 11) + pad(f2(b - a), 10)
    + pad(f3((b - a) / b), 8));
}

console.log(`
================================================================================
本阶段的口径声明与缺口
================================================================================
【统一参数】23±5℃ / 空调关闭 / 低压 0.60 / η_m=0.91 / φ=0.75 / N=11
            全部与车型无关，也【不含任何温度假设】。

【为什么 η_m 与 φ 要分开】厂商公布的是"电驱效率"（η_m, 0.90~0.93），
  而整车能耗还多一层"动能回收效率"（φ）。两者混在一起就无法与厂商口径对照。

【动能项的残余不确定性】
  N=11（短行程数）与 Δv（单事件速度增量）的乘积才是可辨识量。
  本版用 N=11 作为先验（CLTC-P 短行程数），等效单事件速度增量 ≈ 76 km/h。
  若 N 实际为 13，动能项下降约 15%，综合效率上升约 0.04（N 越大, 同样的 ΣΔv 摊到更多事件上, Σ½Δv² 越小）。

【待独立核实的参数】
  1. φ=0.75 —— 目前是估参。锂电池低温充电接受功率有公开数据，常温 φ 需查。
     注意 φ 在能量流上 = η_电机发电 × η_电池充电，两者都可查。
  2. Crr=0.0090 全车统一 —— 滚阻是轮胎属性；若能查到各车原配胎的 EU 标签
     滚阻等级，可替换为分车值。

【本阶段不做的事】
  - 不引入温度（留到 Stage-2）
  - 不用任何一台车去标定动能参数
  - 不用"官方电耗反解"动力学黑箱
`);
