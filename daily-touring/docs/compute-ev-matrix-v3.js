// ============================================================================
// 六车电耗/续航矩阵 v3 —— 官方 Cd + 热管理两档化
// 运行: node compute-ev-matrix-v3.js
// 相对 v2 的两处实质修正:
//   (1) Cd 全部换成官方口径（逐一附来源），迎风面积仍为估算（厂商不公布）
//   (2) 热管理按"工作温域"分两档: 低温档(-10℃) / 超低温档(-30℃)
//       超低温档下，热泵温域不足的车型会被迫启用 PTC，附件功率显著上升
'use strict';

const RHO = 1.2, G = 9.81, ETA = 0.91;
const V_CLTC = 28.96;

// ---------------------------------------------------------------- 1. 车型库
// [名, 组, 电池kWh, 整备, 满载, Cd(官方), A m2(估), Crr, CLTC km, 热管理档]
// 热管理档: 'full' = 超低温仍可热泵 / 'limited' = 超低温需 PTC 介入
const CARS = [
  ['特斯拉 Model 3 RWD', '轿车',  60.0, 1760, 2192, 0.219, 2.22, 0.0085, 634, 'limited'],
  ['小米 SU7 后驱标准版', '轿车',  73.6, 1980, 2430, 0.195, 2.30, 0.0090, 700, 'full'],
  ['特斯拉 Model Y RWD', 'SUV',   62.5, 1922, 2432, 0.230, 2.60, 0.0090, 593, 'limited'],
  ['小米 YU7 后驱标准版', 'SUV',   96.3, 2315, 2765, 0.245, 2.60, 0.0090, 835, 'full'],
  ['小鹏 X9 长续航前驱',  'MPV',   94.8, 2675, 3210, 0.227, 3.00, 0.0095, 650, 'full'],
  ['极氪 009 前驱七座',   'MPV',  110.0, 2798, 3378, 0.270, 3.00, 0.0095, 740, 'full'],
];
// Cd 来源（官方或官方公布给媒体）:
//  Model 3 0.219 改款Highland官方 [DDCAR 2023-09]
//  Model Y 0.23 官方 / 焕新版 0.22
//  SU7 0.195 官方宣称全球最低
//  YU7 0.245 小米官网（注明"因配置不同有差异"）
//  X9 0.227Cd 小鹏官网
//  009 0.27 极氪官方公布 [新出行 2022-08]
// 热管理来源:
//  SU7 双模热泵: -15℃ 无需加热器, -20℃ 仍吸热, -30℃ 系统可应对 [小米热管理技术]
//  009 九源热泵: -40~50℃ 工作温域 [新华网 2025-01]
//  X9 X-HP 智能热管理(含热泵): 未查到具体温域下限 -> 按可用处理(存疑)
//  Model 3/Y 热泵: -20℃ 以下效率严重下降, -15℃ 以下可能失效 [特斯拉官方图表/召回公告]

const CdA    = c => c[5] * c[6];
const eCLTC  = c => c[2] / c[8] * 100;
const vms    = v => v / 3.6;
const kWh100 = (kW, v) => kW / v * 100;

const kW_road = (c, m, v) =>
  (m * G * c[7] * vms(v) + 0.5 * RHO * CdA(c) * Math.pow(vms(v), 3)) / 1000;

// ---------------------------------------------------------------- 2. 附件（两档）
// 低速档 (-10℃): 热泵普遍可用，各车差异小
// 超低温档 (-30℃): 热泵温域不足者启用 PTC
const ACC = {
  //           空调  电池加热  低压
  cool:      { ac: 1200, bat: 0,    low: 350 },   // 夏季制冷
  coolFull:  { ac: 1500, bat: 0,    low: 350 },
  winterLow: { ac: 1800, bat: 900,  low: 350 },   // -10℃, 热泵充足
  // -30℃: 按热管理档区分
  winterUltra: {
    full:    { ac: 2400, bat: 1500, low: 350 },   // 热泵仍工作
    limited: { ac: 4200, bat: 2000, low: 350 },   // PTC 强制介入
  },
};
const accW = (spec, m) => spec.ac + spec.bat + spec.low;
const LIGHT = 120;
const mk = (c, load) => load === 'full' ? c[4] : c[3] + LIGHT;

// ---------------------------------------------------------------- 3. 标定
const LOW_CLTC = 0.60, ACC_HW = 1.55, E_M3_120 = 17.5;
function calibrate() {
  const c = CARS[0], m = c[3];
  const eCLTC_road = kWh100(kW_road(c, m, V_CLTC), V_CLTC);
  const e120_road  = kWh100(kW_road(c, m, 120), 120);
  const CYC_C = eCLTC(c) - eCLTC_road / ETA - LOW_CLTC;
  const CYC_H = E_M3_120 - e120_road / ETA - kWh100(ACC_HW, 120);
  return { CYC_C, CYC_H, CYC_C_kg: CYC_C / m, CYC_H_kg: CYC_H / m };
}
const CAL = calibrate();
const A_HW = (() => {
  const c = CARS[0];
  const eR = kWh100(kW_road(c, c[3], 120), 120);
  return (E_M3_120 - CAL.CYC_H - kWh100(ACC_HW, 120)) / (eR / ETA);
})();
function kResid(c) {
  const eR = kWh100(kW_road(c, c[3], V_CLTC), V_CLTC);
  const aEff = (eCLTC(c) - CAL.CYC_C_kg * c[3] - LOW_CLTC) / (eR / ETA);
  return { aEff, etaEff: ETA / aEff };
}
const eCycle = (c, m, v) => (v >= 100 ? CAL.CYC_H_kg : CAL.CYC_C_kg) * m;
function energy(c, m, v, a) {
  const eff = v >= 100 ? A_HW : kResid(c).aEff;
  return eff * kWh100(kW_road(c, m, v), v) / ETA + eCycle(c, m, v) + kWh100(a / 1000, v) + LOW_CLTC;
}

// ---------------------------------------------------------------- 4. 输出
const f0 = x => x.toFixed(0), f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(104));

line(); console.log('修正1：官方 Cd 与估算迎风面积'); line();
console.log('车型'.padEnd(20) + pad('Cd(官方)', 10) + pad('A(估)', 8) + pad('Cd·A', 8) + pad('热管理档', 10));
for (const c of CARS) {
  console.log(c[0].padEnd(20) + pad(f3(c[5]), 10) + pad(f2(c[6]), 8)
              + pad(f3(CdA(c)), 8) + pad(c[9] === 'full' ? '全温域' : '低温受限', 10));
}

line(); console.log('修正2：附件功率两档化 (W)'); line();
console.log('车型'.padEnd(20) + pad('夏季', 9) + pad('-10℃', 9) + pad('-30℃', 9) + pad('超低温增量', 11) + '  原因');
for (const c of CARS) {
  const sum = accW(ACC.cool, 0), lo = accW(ACC.winterLow, 0);
  const u = accW(c[9] === 'full' ? ACC.winterUltra.full : ACC.winterUltra.limited, 0);
  console.log(c[0].padEnd(20) + pad(sum, 9) + pad(lo, 9) + pad(u, 9) + pad('+' + (u - lo) + 'W', 11)
              + '  ' + (c[9] === 'full' ? '热泵够用' : '**PTC 介入**'));
}

line(); console.log('标定与逐车效率'); line();
console.log(`  CYC_CLTC = ${f3(CAL.CYC_C)}  CYC_HW = ${f3(CAL.CYC_H)}  比值 ${f3(CAL.CYC_H / CAL.CYC_C)}`);
console.log('车型'.padEnd(20) + pad('官方CLTC', 10) + pad('模型CLTC', 10) + pad('偏差', 8) + pad('η_eff', 8));
for (const c of CARS) {
  const back = energy(c, c[3], V_CLTC, 0);
  console.log(c[0].padEnd(20) + pad(f2(eCLTC(c)), 10) + pad(f2(back), 10)
              + pad(f2((back - eCLTC(c)) / eCLTC(c) * 100) + '%', 8) + pad(f3(kResid(c).etaEff), 8));
}

// ---------------------------------------------------------------- 5. 工况矩阵
const SCEN = [
  ['夏·市30',   30,  'light', 'cool',      'low'],
  ['夏·高120',  120, 'light', 'cool',      'high'],
  ['夏·高120满',120, 'full',  'coolFull',  'high'],
  ['-10·市30',  30,  'light', 'winterLow', 'low'],
  ['-10·高120', 120, 'light', 'winterLow', 'high'],
  ['-10·高120满',120,'full',  'winterLow', 'high'],
  ['-30·市30',  30,  'light', 'ultra',     'low'],
  ['-30·高120', 120, 'light', 'ultra',     'high'],
  ['-30·高120满',120,'full',  'ultra',     'high'],
];
const pick = (c, key) => {
  if (key === 'cool') return ACC.cool;
  if (key === 'coolFull') return ACC.coolFull;
  if (key === 'winterLow') return ACC.winterLow;
  return c[9] === 'full' ? ACC.winterUltra.full : ACC.winterUltra.limited;
};
line(); console.log('电耗矩阵 (kWh/100km)'); line();
console.log('车型'.padEnd(20) + SCEN.map(x => pad(x[0], 12)).join(''));
for (const c of CARS) {
  const row = SCEN.map(([, v, ld, ak]) => energy(c, mk(c, ld), v, accW(pick(c, ak), 0)));
  console.log(c[0].padEnd(20) + row.map(x => pad(f2(x), 12)).join(''));
}

function rangeRow(title, v) {
  line(); console.log(`${title} 续航 (km) 与 CLTC 达成率`); line();
  const cols = [
    ['夏轻', 'cool', 'light'], ['夏满', 'coolFull', 'full'],
    ['-10轻', 'winterLow', 'light'], ['-10满', 'winterLow', 'full'],
    ['-30轻', 'ultra', 'light'], ['-30满', 'ultra', 'full'],
  ];
  console.log('车型'.padEnd(20) + pad('CLTC', 7) + cols.map(x => pad(x[0], 9)).join('') + pad('-30满达成率', 13));
  for (const c of CARS) {
    const rs = cols.map(([, ak, ld]) => {
      const e = energy(c, mk(c, ld), v, accW(pick(c, ak), 0));
      return c[2] / e * 100;
    });
    console.log(c[0].padEnd(20) + pad(c[8], 7) + rs.map(x => pad(f0(x), 9)).join('')
                + pad(f0(rs[5] / c[8] * 100) + '%', 13));
  }
}
rangeRow('高速 120km/h', 120);
rangeRow('市区 30km/h', 30);

// 极寒下 PTC 介入造成的分化
line(); console.log('关键：-30℃ 高速 超低温档，PTC 介入造成的分化'); line();
console.log('车型'.padEnd(20) + pad('附件W', 9) + pad('-30℃电耗', 11) + pad('-10℃电耗', 11) + pad('增量', 9));
for (const c of CARS) {
  const u = accW(pick(c, 'ultra'), 0), l = accW(ACC.winterLow, 0);
  const eu = energy(c, c[3] + LIGHT, 120, u), el = energy(c, c[3] + LIGHT, 120, l);
  console.log(c[0].padEnd(20) + pad(u, 9) + pad(f2(eu), 11) + pad(f2(el), 11)
              + pad('+' + f2((eu - el) / el * 100) + '%', 9));
}

console.log(`
================================================================================
本版修正了什么、还差什么
================================================================================
【已修正】
1. Cd 全部替换为官方口径（逐一附来源），不再是"同级估算"。
   但迎风面积 A 仍为估算 —— 厂商普遍不公布，误差带约 ±5~8%。
2. 热管理分两档：-10℃（热泵普遍可用）与 -30℃（按热泵温域分 full/limited）。
   limited 档（Model 3 / Model Y）在 -30℃ 会被迫启用 PTC，附件 +1500W。

【仍未解决】
1. X9 的 X-HP 热管理未查到具体温域下限，本版按"全温域可用"处理 —— 存疑项。
2. 官方 Cd 常对应特定轮毂配置（小米官网自注"因配置不同有差异"），
   量产车实际 Cd 可能高于宣传值。
3. 各车热泵的低温功率曲线仍是黑箱，"PTC 介入阈值"是定性判断而非实测。
4. 低温/超低温档的电池加热功率为工程估值，未逐车核实。
5. 仍未做真车验证。
`);
