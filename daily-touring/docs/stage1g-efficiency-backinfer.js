// ============================================================================
// Stage-1g  从 CLTC 官方电耗反推每车"三电效率 η"（含减速器）
// 运行: node stage1g-efficiency-backinfer.js
// ============================================================================
//
// 【用户指出的正确定位】排除 YU7 异常值后，CLTC 官方电耗 + 物理模型
//   可以反推出每车的"电驱系统效率 η"（电池→车轮，含逆变器+电机+减速器），
//   这正是网友反复争论的"谁家三电效率高 / 谁电耗虚标"。
//
// 【为什么现在能反推】5 个未知量里，4 个已锚定：
//   φ=0.65(中点,可扫)  Crr=逐车查实  A=宽×高×0.85  U4附件=0.6
//   → 只剩 η 一个未知量，1 方程 1 未知量，可解。
//
// 【反推公式】
//   官方电耗 = (阻力功驱动段 + 动能注入)/η + 附件 − φ×制动池
//   → η = (阻力功 + 动能注入) / (官方 − 附件 + φ×制动池)
//
// 【纪律】反推的 η 是"三电效率残差出口"，物理区间 0.88~0.93。
//   若某车 η>0.93 → 要么官方电耗标低，要么参数(φ/Crr/A)仍偏；不是该车"超物理"。
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');
const G = 9.81, RHO = 1.2, DIST = 14.48;

const CARS = [
  { n: 'Model 3 RWD', m0: 1760, mg: 2192, Cd: 0.219, A: 2.266, cltcE: 9.46,  crr: 0.0070 },
  { n: 'SU7 后驱标准', m0: 1980, mg: 2430, Cd: 0.195, A: 2.403, cltcE: 10.51, crr: 0.0065 },
  { n: 'Model Y RWD', m0: 1922, mg: 2432, Cd: 0.230, A: 2.652, cltcE: 10.54, crr: 0.0070 },
  { n: 'YU7 后驱标准', m0: 2315, mg: 2765, Cd: 0.245, A: 2.715, cltcE: 11.53, crr: 0.0070 },  // 异常值，单列
  { n: 'X9 长续航前驱', m0: 2675, mg: 3210, Cd: 0.227, A: 3.016, cltcE: 14.58, crr: 0.0075 },
  { n: '009 前驱七座', m0: 2798, mg: 3378, Cd: 0.270, A: 3.117, cltcE: 14.86, crr: 0.0067 },
];

const P_ACC = 0.6;   // 低压常电 kWh/100km（CLTC 关空调）
const f3 = x => x.toFixed(3), pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(100));
const e = kWh => kWh / DIST * 100;

// 逐秒积分（试验质量），返回驱动段阻力功/动能注入/制动池（全程 kWh）
function integrate(c) {
  const m = c.m0 + 0.65 * (c.mg - c.m0);
  let W_res_drive = 0, E_kin_in = 0, W_res_decel = 0, E_kin_out = 0;
  for (let t = 0; t < 1800 - 1; t++) {
    const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
    const P_res = m * G * c.crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v;
    const dK = 0.5 * m * (vn * vn - v * v);
    if (dK >= 0) { W_res_drive += P_res; E_kin_in += dK; }
    else { W_res_decel += P_res; E_kin_out += -dK; }
  }
  return { res: e(W_res_drive/3.6e6), kin: e(E_kin_in/3.6e6), pool: e((E_kin_out - W_res_decel)/3.6e6) };
}

// 反推 η
const etaOf = (c, r, phi) => (r.res + r.kin) / (c.cltcE - P_ACC + phi * r.pool);

line(); console.log('Stage-1g  反推每车三电效率 η（含减速器）'); line();
console.log('  公式：η = (阻力功 + 动能注入) / (官方CLTC − 附件 + φ×制动池)');
console.log('  物理区间：η ∈ 0.88~0.93（厂商公开口径）；η>0.93 即"官方标低或参数仍偏"');
console.log('');

// 表头
const PHIS = [0.60, 0.65, 0.70, 0.75];
console.log('车型'.padEnd(22) + '官方CLTC'.padEnd(9) + PHIS.map(p => `φ=${p}→η`).join('  '));
console.log('-'.repeat(100));
const results = CARS.map(c => {
  const r = integrate(c);
  return { c, r, etas: PHIS.map(phi => etaOf(c, r, phi)) };
});
for (const { c, r, etas } of results) {
  console.log(c.n.padEnd(22) + pad(c.cltcE.toFixed(2), 9) + etas.map(v => pad(v.toFixed(3), 9)).join(' '));
}

console.log('');
line(); console.log('分析'); line();
// 找出让"五车(除YU7)η 都落在 0.88~0.93"的 φ
console.log('  → 逐 φ 看五车(除 YU7)反推 η 是否集体落进物理区间：');
for (let i = 0; i < PHIS.length; i++) {
  const normal = results.filter(r => r.c.n !== 'YU7 后驱标准');
  const ok = normal.every(r => r.etas[i] >= 0.88 && r.etas[i] <= 0.93);
  const range = normal.map(r => r.etas[i]);
  console.log(`    φ=${PHIS[i]}: 五车 η ∈ [${Math.min(...range).toFixed(3)}, ${Math.max(...range).toFixed(3)}]  ${ok ? '✓ 全部落进 0.88~0.93' : '✗ 有越界'}`);
}
console.log('');

// 用最自洽的 φ 给出排序
console.log('  → 三电效率排序（取 φ=0.70 作基准，YU7 标注异常）：');
const sorted = results
  .map(r => ({ n: r.c.n, eta: r.etas[2], isYu7: r.c.n.includes('YU7') }))
  .sort((a, b) => b.eta - a.eta);
sorted.forEach((s, i) => {
  const tag = s.isYu7 ? '  ⚠️异常' : '';
  console.log(`    ${i + 1}. ${pad(s.n, 20)} η = ${s.eta.toFixed(3)}${tag}`);
});
console.log('');
console.log('  → 注意：η 排序的"名次"高度依赖 φ/Crr/A 的假设值，±0.01 的假设差异就能换名次');
console.log('  → 只能给"区间 + 相对水平"，不能给"谁家第几名"的精确断言（否则就是造假）');
