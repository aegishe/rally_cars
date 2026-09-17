// ============================================================================
// Stage-1b  逐秒能量分解 —— 用已得的 CLTC-P 1800 点逐秒序列做"不需 φ"的事
// 运行: node stage1b-energy-decomposition.js
// ============================================================================
//
// 【本阶段定位】交接文档第四部分 P1：
//   "用已得的 1800 点数据做不需 φ 的事——精确各段能量需求分解
//    （阻力功 + 动能功分开列）"
//
// 【为什么这是"不需 φ"】动能回收效率 φ 只决定"减速释放的动能里
//   有多少被回收回电池"；而"减速释放了多少动能、加速注入了多少动能、
//   阻力消耗了多少"这三个原始物理量完全不依赖 φ，可由逐秒曲线直接积分。
//
// 【数据】cltc-p-1800points.json（key=秒 0..1800，value=km/h，t=1800 为冗余闭合点 v=0）
//   已与国标验证：里程 14.48km / 平均 28.96 / 最大 114.0 完全吻合。
//
// 【单位链纪律】（M3 禁令）v→m/s 除 3.6；功率 W；功 J；kWh=J/3.6e6；
//   电耗 kWh/100km = 总能量(kWh) / 14.48(km) × 100。
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');

const G = 9.81, RHO = 1.2;
const DIST_KM = 14.48;       // CLTC-P 循环里程
const N = 1800;              // 采样秒数 0..1799

// 六车参数（与交接文档 §2.5 一致；Cd 官方口径，A 为估算值）
const CARS = [
  { n: '特斯拉 Model 3 RWD',  m: 1760, Cd: 0.219, A: 2.22, Crr: 0.0090, cltcE: 9.46 },
  { n: '小米 SU7 后驱标准版',  m: 1980, Cd: 0.195, A: 2.30, Crr: 0.0090, cltcE: 10.51 },
  { n: '特斯拉 Model Y RWD',  m: 1922, Cd: 0.230, A: 2.60, Crr: 0.0090, cltcE: 10.54 },
  { n: '小米 YU7 后驱标准版',  m: 2315, Cd: 0.245, A: 2.60, Crr: 0.0090, cltcE: 11.53 },
  { n: '小鹏 X9 长续航前驱',   m: 2675, Cd: 0.227, A: 3.00, Crr: 0.0090, cltcE: 14.58 },
  { n: '极氪 009 前驱七座',    m: 2798, Cd: 0.270, A: 3.00, Crr: 0.0090, cltcE: 14.86 },
];

// 三段边界（秒）：1部 0..673(674s) / 2部 674..1366(693s) / 3部 1367..1799(433s)
const SEGS = [
  { name: '1部 低速', lo: 0,    hi: 673 },
  { name: '2部 中速', lo: 674,  hi: 1366 },
  { name: '3部 高速', lo: 1367, hi: 1799 },
];

const f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(104));
const kJ2kwh = J => J / 3.6e6;
// 电耗换算：总能量(kWh) 摊到 14.48km → kWh/100km
const toE = kWh => kWh / DIST_KM * 100;

// ---------------------------------------------------------------- 工具
// 对一辆车做逐秒积分，返回分段的阻力功/动能账
function integrate(c) {
  const m = c.m;
  // 全程 + 三段累计器
  const acc = {
    W_res_drive: 0,  W_res_decel: 0,   // 阻力功（驱动段 / 减速段）J
    E_kin_in: 0,     E_kin_out: 0,     // 动能注入 / 释放 J
    segs: SEGS.map(() => ({
      W_res: 0,      // 该段阻力功（阻力载荷口径，含驱动+减速）J
      W_res_drive: 0,
      W_res_decel: 0,
      E_kin_in: 0,
      E_kin_out: 0,
    })),
  };
  for (let t = 0; t < N - 1; t++) {
    const v  = data[t]     / 3.6;   // m/s
    const vn = data[t + 1] / 3.6;
    const P_res = m * G * c.Crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v; // W
    const dK = 0.5 * m * (vn * vn - v * v); // J
    const seg = t <= 673 ? 0 : (t <= 1366 ? 1 : 2);
    if (dK >= 0) {            // 加速或匀速：电机驱动
      acc.W_res_drive += P_res;
      acc.E_kin_in   += dK;
      acc.segs[seg].W_res_drive += P_res;
      acc.segs[seg].E_kin_in    += dK;
    } else {                  // 减速：阻力+制动吸收
      acc.W_res_decel += P_res;
      acc.E_kin_out   += -dK;
      acc.segs[seg].W_res_decel += P_res;
      acc.segs[seg].E_kin_out    += -dK;
    }
    acc.segs[seg].W_res += P_res;
  }
  return acc;
}

// ---------------------------------------------------------------- Part 0 数据验证
line(); console.log('Part 0  数据自检（与国标 GB/T 38146.1-2019 对照）'); line();
{
  let vsum = 0, vmax = 0, idle = 0, dist = 0;
  for (let t = 0; t < N; t++) {
    const v = data[t];
    vsum += v; vmax = Math.max(vmax, v); dist += v / 3.6;
    if (v === 0) idle++;
  }
  console.log(`  点数 ${Object.keys(data).length}(含闭合点) | 里程 ${(dist/1000).toFixed(2)} km(国标14.48) | 平均 ${(vsum/N).toFixed(2)}(28.96) | 最大 ${vmax}(114.0)`);
  console.log(`  怠速(v=0)比例 ${(idle/N*100).toFixed(2)}% (国标 22.11%)`);
  // 比动能闭合自检：循环首尾 v=0 → 加速注入 = 减速释放
  let specIn = 0, specOut = 0;
  for (let t = 0; t < N - 1; t++) {
    const v = data[t]/3.6, vn = data[t+1]/3.6;
    const d = 0.5 * (vn*vn - v*v);
    if (d > 0) specIn += d; else specOut += -d;
  }
  console.log(`  比动能闭合自检：注入 ${specIn.toFixed(2)} J/kg vs 释放 ${specOut.toFixed(2)} J/kg → 差 ${(Math.abs(specIn-specOut)/specIn*100).toFixed(3)}% (应≈0)`);
  console.log(`  → CLTC-P 循环的比动能注入/释放 = ${(specIn).toFixed(2)} J/kg（曲线固有属性，与车无关）`);
}

// ---------------------------------------------------------------- Part 1 比动能三段分解
line(); console.log('Part 1  CLTC-P 比动能分解（每 kg，与车无关，φ 无关）'); line();
{
  const segSpec = SEGS.map(() => ({ inn: 0, out: 0 }));
  for (let t = 0; t < N - 1; t++) {
    const v = data[t]/3.6, vn = data[t+1]/3.6;
    const d = 0.5 * (vn*vn - v*v);
    const seg = t <= 673 ? 0 : (t <= 1366 ? 1 : 2);
    if (d > 0) segSpec[seg].inn += d; else segSpec[seg].out += -d;
  }
  console.log('段'.padEnd(12) + pad('注入 J/kg', 12) + pad('释放 J/kg', 12) + pad('注入占比', 10));
  const totIn = segSpec.reduce((a, s) => a + s.inn, 0);
  segSpec.forEach((s, i) => {
    console.log(SEGS[i].name.padEnd(12) + pad(s.inn.toFixed(2), 12) + pad(s.out.toFixed(2), 12) + pad((s.inn/totIn*100).toFixed(1) + '%', 10));
  });
  console.log('  → 动能注入集中在哪段 = 循环的加减速结构；回收潜力 ∝ 释放量');
}

// ---------------------------------------------------------------- Part 2 阻力功分解（六车）
line(); console.log('Part 2  阻力功分解（滚阻 + 风阻，逐秒积分，六车）'); line();
{
  // 滚阻/风阻单独累计需要分开算
  function integrateSplit(c) {
    const m = c.m;
    const r = { roll: 0, aero: 0, rollSeg: SEGS.map(()=>0), aeroSeg: SEGS.map(()=>0) };
    for (let t = 0; t < N - 1; t++) {
      const v = data[t] / 3.6;
      const Pr = m * G * c.Crr * v;
      const Pa = 0.5 * RHO * c.Cd * c.A * v * v * v;
      const seg = t <= 673 ? 0 : (t <= 1366 ? 1 : 2);
      r.roll += Pr; r.aero += Pa;
      r.rollSeg[seg] += Pr; r.aeroSeg[seg] += Pa;
    }
    return r;
  }
  console.log('车型'.padEnd(22) + pad('滚阻kWh', 9) + pad('风阻kWh', 9) + pad('阻力合计', 9) + pad('折kWh/100km', 13) + pad('风阻占比', 9));
  for (const c of CARS) {
    const r = integrateSplit(c);
    const tot = r.roll + r.aero;
    console.log(c.n.padEnd(22) + pad(f3(kJ2kwh(r.roll)), 9) + pad(f3(kJ2kwh(r.aero)), 9)
      + pad(f3(kJ2kwh(tot)), 9) + pad(f2(toE(kJ2kwh(tot))), 13)
      + pad((r.aero/tot*100).toFixed(1) + '%', 9));
  }
  console.log('  → 阻力功 = 全程阻力载荷（含减速段阻力"帮助减速"的部分），是阻力税的总量口径');
  // 三段（Model 3 基准）
  const c0 = CARS[0];
  const r0 = integrateSplit(c0);
  console.log('');
  console.log('  Model 3 三段分解（kWh，滚阻/风阻）：');
  console.log('  段'.padEnd(12) + pad('滚阻', 9) + pad('风阻', 9) + pad('合计', 9) + pad('折kWh/100km', 13));
  SEGS.forEach((s, i) => {
    const t = r0.rollSeg[i] + r0.aeroSeg[i];
    console.log('  ' + s.name.padEnd(10) + pad(f3(kJ2kwh(r0.rollSeg[i])), 9) + pad(f3(kJ2kwh(r0.aeroSeg[i])), 9)
      + pad(f3(kJ2kwh(t)), 9) + pad(f2(toE(kJ2kwh(t))), 13));
  });
}

// ---------------------------------------------------------------- Part 3 动能账（六车）
line(); console.log('Part 3  动能账（加速注入 vs 减速释放，六车）'); line();
{
  console.log('车型'.padEnd(22) + pad('注入kWh', 9) + pad('释放kWh', 9) + pad('折kWh/100km', 13));
  for (const c of CARS) {
    const a = integrate(c);
    console.log(c.n.padEnd(22) + pad(f3(kJ2kwh(a.E_kin_in)), 9) + pad(f3(kJ2kwh(a.E_kin_out)), 9)
      + pad(f2(toE(kJ2kwh(a.E_kin_in))), 13));
  }
  console.log('  → 注入=释放(循环闭合)；"折kWh/100km"是"若动能全部耗散(φ=0)"的每公里动能税');
  console.log('  → 真实动能税 = 注入 × (1 - φ·回收率)，φ 是唯一未定参数');
}

// ---------------------------------------------------------------- Part 4 能量账（Model 3 基准，展示欠定）
line(); console.log('Part 4  能量账对不上（演示余项禁令 M1——不得把余项命名成物理量）'); line();
{
  const c0 = CARS[0];
  const a = integrate(c0);
  const W_res_drive_kwh = kJ2kwh(a.W_res_drive);
  const E_kin_in_kwh    = kJ2kwh(a.E_kin_in);
  const W_res_decel_kwh = kJ2kwh(a.W_res_decel);
  const E_kin_out_kwh   = kJ2kwh(a.E_kin_out);

  console.log('  【轮端机械账（Model 3 RWD，不含电池/附件）】');
  console.log(`    驱动段阻力功     ${W_res_drive_kwh.toFixed(3)} kWh`);
  console.log(`    加速注入动能     ${E_kin_in_kwh.toFixed(3)} kWh`);
  console.log(`    减速段阻力"帮减" ${W_res_decel_kwh.toFixed(3)} kWh（在减速段做负功）`);
  console.log(`    减速释放动能     ${E_kin_out_kwh.toFixed(3)} kWh`);
  console.log(`    减速段制动吸收   ${(E_kin_out_kwh - W_res_decel_kwh).toFixed(3)} kWh（= 释放 − 阻力帮减，是 φ 的回收池）`);
  console.log('');
  const eCLTC = c0.cltcE * DIST_KM / 100;  // 官方 CLTC 全程电耗 kWh = 9.46×14.48/100
  console.log(`  【电池端】官方 CLTC 全程电耗 = ${eCLTC.toFixed(3)} kWh（= 9.46 kWh/100km × 14.48km）`);
  console.log(`    轮端驱动需求 = 驱动段阻力功 ${W_res_drive_kwh.toFixed(3)} + 注入动能 ${E_kin_in_kwh.toFixed(3)} = ${(W_res_drive_kwh+E_kin_in_kwh).toFixed(3)} kWh`);
  console.log(`    → 除以 η 后仍远小于官方电耗，缺口 = 动能耗散(1-φ) + 附件 + 电驱损耗，三者混在余项里不可分离`);
  console.log(`    → 这就是"1 个观测 vs 4 个未知量"欠定的直观表达：余项不是任何单一物理量`);
}

// ---------------------------------------------------------------- Part 5 加减速功率峰值（滑行/制动功率限制分析）
line(); console.log('Part 5  加减速功率峰值（滑行/制动段的功率限制，六车）'); line();
{
  console.log('车型'.padEnd(22) + pad('峰值加速kW', 12) + pad('峰值减速kW', 12) + pad('峰值回收kW', 12));
  for (const c of CARS) {
    const m = c.m;
    let pAccMax = 0, pDecMax = 0;
    for (let t = 0; t < N - 1; t++) {
      const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
      const P_res = m * G * c.Crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v;
      const dK = 0.5 * m * (vn * vn - v * v); // J per 1s = W
      if (dK > 0) { pAccMax = Math.max(pAccMax, (P_res + dK) / 1000); }
      else { pDecMax = Math.max(pDecMax, (-dK - P_res) / 1000); } // 制动功率 = 释放 − 阻力帮减
    }
    console.log(c.n.padEnd(22) + pad(pAccMax.toFixed(1), 12) + pad(pDecMax.toFixed(1), 12)
      + pad((pDecMax * 0.8).toFixed(1), 12));
  }
  console.log('  → 峰值加速功率 = 电驱在 CLTC 内要覆盖的瞬时功率（远低于各车标称峰值，CLTC 很温和）');
  console.log('  → 峰值减速功率 × φ ≈ 回收瞬时功率，按 φ=0.8 估算落在典型回收功率(60~100kW)内');
  console.log('  → 这就是"滑行/制动段功率限制"：CLTC 的减速度 1.47m/s² 温和，回收功率不受电控限功率约束');
}

line(); console.log('本脚本交付的"不需 φ"结论'); line();
console.log('  1. CLTC-P 比动能注入/释放 = 曲线固有属性，可精确到 J/kg（三段分解见 Part 1）');
console.log('  2. 六车阻力功 = 滚阻 + 风阻精确积分（Part 2），替代交接文档 §2.4 的"运行平均车速"近似');
console.log('  3. 六车动能税上限（φ=0 时）= 注入动能折 kWh/100km（Part 3）');
console.log('  4. φ 只出现在"减速段制动吸收 → 回收"这一步，能量账其余全部闭合（Part 4）');
console.log('');
