// ============================================================================
// Stage-1h  用反推的三电效率 η，推六车实际续航（城市/高速 × 夏/冬）
// 运行: node stage1h-range-matrix.js
// ============================================================================
//
// 【承接 stage1g】从 CLTC 官方电耗反推每车 η（三电效率，含减速器）。
//   本脚本用反推的 η，把电耗外推到非 CLTC 工况，再算续航 = 电池/电耗。
//
// 【口径】
//   高速 120：稳态巡航，P_road(120)/η + 空调税（物理精确，无加减速）
//   市区 30 ：沿用 CLTC 动能账（平均 28.96≈30），仅附件税按 30km/h 重算
//   附件税  = P_AC(kW) / v(km/h) × 100  kWh/100km
//   空调功率：夏制冷 轿车/SUV 1.5kW · MPV 2.5kW；冬热泵 轿车/SUV 2.5kW · MPV 3.5kW
//   质量口径：试验质量（整备+65%装载），与 CLTC 官方一致
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');
const G = 9.81, RHO = 1.2;

const CARS = [
  { n: 'Model 3 RWD', m0: 1760, mg: 2192, Cd: 0.219, A: 2.266, crr: 0.0070, wh: 60.0,  cltcE: 9.46,  suv: false },
  { n: 'SU7 后驱标准', m0: 1980, mg: 2430, Cd: 0.195, A: 2.403, crr: 0.0065, wh: 73.6,  cltcE: 10.51, suv: false },
  { n: 'Model Y RWD', m0: 1922, mg: 2432, Cd: 0.230, A: 2.652, crr: 0.0070, wh: 62.5,  cltcE: 10.54, suv: false },
  { n: 'YU7 后驱标准', m0: 2315, mg: 2765, Cd: 0.245, A: 2.715, crr: 0.0070, wh: 96.3,  cltcE: 11.53, suv: false },
  { n: 'X9 长续航前驱', m0: 2675, mg: 3210, Cd: 0.227, A: 3.016, crr: 0.0075, wh: 94.8,  cltcE: 14.58, suv: true },
  { n: '009 前驱七座', m0: 2798, mg: 3378, Cd: 0.270, A: 3.117, crr: 0.0067, wh: 110.0, cltcE: 14.86, suv: true },
];

const PHI = 0.75;   // 自洽点（反推 η 落进物理区间）
const P_ACC_LOW = 0.6;  // 低压常电
const f1 = x => x.toFixed(0), f2 = x => x.toFixed(1), pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(104));

// 高速 120 稳态电耗（kWh/100km，轮端→电池，含附件）
function eHighway(c, eta, pAC) {
  const m = c.m0 + 0.65 * (c.mg - c.m0);
  const v = 120 / 3.6;
  const P = m * G * c.crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v; // W
  return P / 1000 / 120 * 100 / eta + pAC / 120 * 100;
}
// 市区 30 电耗 = CLTC 官方 + 空调税（CLTC 平均 28.96≈30）
function eCity(c, pAC) {
  return c.cltcE + pAC / 30 * 100;
}

line(); console.log('Stage-1h  六车实际续航矩阵（反推 η，φ=0.75 自洽）'); line();

// 先反推 η（复用 stage1g 逻辑）
console.log('【Step 1】反推三电效率 η（φ=0.75）'); line();
const rows = [];
for (const c of CARS) {
  // 逐秒积分（试验质量）
  const m = c.m0 + 0.65 * (c.mg - c.m0);
  let W_res_drive = 0, E_kin_in = 0, W_res_decel = 0, E_kin_out = 0;
  for (let t = 0; t < 1800 - 1; t++) {
    const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
    const P = m * G * c.crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v;
    const dK = 0.5 * m * (vn * vn - v * v);
    if (dK >= 0) { W_res_drive += P; E_kin_in += dK; }
    else { W_res_decel += P; E_kin_out += -dK; }
  }
  const res = W_res_drive / 3.6e6 / 14.48 * 100;
  const kin = E_kin_in / 3.6e6 / 14.48 * 100;
  const pool = (E_kin_out - W_res_decel) / 3.6e6 / 14.48 * 100;
  const eta = (res + kin) / (c.cltcE - P_ACC_LOW + PHI * pool);
  rows.push({ c, eta });
  console.log(`  ${pad(c.n, 20)} η = ${eta.toFixed(3)}${c.n.includes('YU7') ? '  ⚠️' : ''}`);
}

line(); console.log('【Step 2】电耗矩阵（kWh/100km）'); line();
const pAC_s = c => c.suv ? { summer: 2.5, winter: 3.5 } : { summer: 1.5, winter: 2.5 };
console.log('车型'.padEnd(20) + pad('高速·夏', 9) + pad('高速·冬', 9) + pad('市区·夏', 9) + pad('市区·冬', 9));
for (const { c, eta } of rows) {
  const ac = pAC_s(c);
  console.log(pad(c.n, 20) + pad(f2(eHighway(c, eta, ac.summer)), 9) + pad(f2(eHighway(c, eta, ac.winter)), 9)
    + pad(f2(eCity(c, ac.summer)), 9) + pad(f2(eCity(c, ac.winter)), 9));
}

line(); console.log('【Step 3】续航矩阵（km = 电池 ÷ 电耗 × 100）'); line();
console.log('车型'.padEnd(20) + pad('电池', 6) + pad('CLTC', 7) + pad('高速·夏', 9) + pad('高速·冬', 9) + pad('市区·夏', 9) + pad('市区·冬', 9) + pad('冬满达成率', 11));
for (const { c, eta } of rows) {
  const ac = pAC_s(c);
  const hwS = eHighway(c, eta, ac.summer), hwW = eHighway(c, eta, ac.winter);
  const ctS = eCity(c, ac.summer), ctW = eCity(c, ac.winter);
  const r = e => c.wh / e * 100;
  console.log(pad(c.n, 20) + pad(f1(c.wh), 6) + pad(f1(c.cltcE ? c.wh / c.cltcE * 100 : 0), 7)
    + pad(f1(r(hwS)), 9) + pad(f1(r(hwW)), 9) + pad(f1(r(ctS)), 9) + pad(f1(r(ctW)), 9)
    + pad((Math.min(r(hwW), r(ctW)) / (c.wh / c.cltcE * 100) * 100).toFixed(0) + '%', 11));
}

line(); console.log('读法'); line();
console.log('  1. 高速电耗是稳态巡航（无加减速），实测"平均120"会更高（含加速+超车）');
console.log('  2. 市区电耗 = CLTC 官方 + 空调税，30km/h 附件税被速度放大（夏+5、冬+8.3）');
console.log('  3. YU7 反推 η=0.959 超物理上限，续航偏乐观，是"官方标低或效率真的高"的异常值');
console.log('  4. 冬满达成率 = 冬季最低续航 ÷ CLTC，对照媒体实测纯电 40~55%');
