// ============================================================================
// Stage-1e  六车能量账闭环 —— 用锚定的 φ/η 重算每车分解
// 运行: node stage1e-energy-ledger.js
// ============================================================================
//
// 【背景】φ 已由外部三重印证锚定在 0.6~0.7，η 厂商口径 0.90~0.93。
//   本脚本把这两个参数代入 P1 的逐秒积分，给每车一张"能量账"：
//     电池净输出 = (阻力功驱动段 + 动能注入)/η − φ×制动池 + 附件
//   对照官方 CLTC 电耗，看残差是否小（小 = 模型闭环自洽）。
//
// 【关键口径修正】CLTC 官方电耗用"试验质量 = 整备 + 65%×最大装载"测，
//   不是整备质量。本脚本全部用试验质量（此前 stage1b 用整备，为口径疏忽）。
//
// 【纪律】残差 = 净输出 − 官方，是"未建模项"（热管理/低压/测试条件差异），
//   不得命名成物理量、不得用于反解（M1 禁令）。
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');
const G = 9.81, RHO = 1.2, DIST = 14.48;

// 六车（整备/满载 一手，Cd 官方，A 估算，Crr 逐车=P2 查轮胎滚阻等级）
// Crr 依据（2026-09-18 P2 检索）：
//   米其林 Pilot Sport EV 官方实测 6.7 kg/t = 0.0067（EU B 级）
//   米其林 E-Primacy(e聆悦) 低滚阻 A 级 ≈0.0065
//   EV 认证胎(韩泰Ventus S1 AS/固特异e锐乘/普利司通TURANZA 6) B 级 ≈0.0067~0.0070
//   MPV 宽胎(佳通/X9) 略高 ≈0.0075
// A 用"宽×高×0.85"系统估算（2026-09-18 修正，替换旧拍脑袋值）
//   宽×高(mm)：Model3 1849×1442 / SU7 1963×1440 / ModelY 1921×1624
//              YU7 1996×1600 / X9 1988×1785 / 009 2024×1812
const CARS = [
  { n: 'Model 3 RWD', m0: 1760, mg: 2192, Cd: 0.219, A: 2.266, cltcE: 9.46,  crr: 0.0070 },
  { n: 'SU7 后驱标准', m0: 1980, mg: 2430, Cd: 0.195, A: 2.403, cltcE: 10.51, crr: 0.0065 },
  { n: 'Model Y RWD', m0: 1922, mg: 2432, Cd: 0.230, A: 2.652, cltcE: 10.54, crr: 0.0070 },
  { n: 'YU7 后驱标准', m0: 2315, mg: 2765, Cd: 0.245, A: 2.715, cltcE: 11.53, crr: 0.0070 },
  { n: 'X9 长续航前驱', m0: 2675, mg: 3210, Cd: 0.227, A: 3.016, cltcE: 14.58, crr: 0.0075 },
  { n: '009 前驱七座', m0: 2798, mg: 3378, Cd: 0.270, A: 3.117, cltcE: 14.86, crr: 0.0067 },
];

// 参数基准（可扫）
const ETA = 0.91;      // 电驱效率
const PHI = 0.65;      // 动能回收（锚定中点）
const P_ACC = 0.6;     // 低压常电 kWh/100km（CLTC 关空调）

const f1 = x => x.toFixed(1), f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(108));
const e = kWh => kWh / DIST * 100; // 全程 kWh → kWh/100km

// 逐秒积分（用试验质量），返回各项全程 kWh
function integrate(c) {
  const m = c.m0 + 0.65 * (c.mg - c.m0); // 试验质量
  let W_res_drive = 0, W_res_decel = 0, E_kin_in = 0, E_kin_out = 0;
  for (let t = 0; t < 1800 - 1; t++) {
    const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
    const P_res = m * G * c.crr * v + 0.5 * RHO * c.Cd * c.A * v * v * v;
    const dK = 0.5 * m * (vn * vn - v * v);
    if (dK >= 0) { W_res_drive += P_res; E_kin_in += dK; }
    else { W_res_decel += P_res; E_kin_out += -dK; }
  }
  return { m, W_res_drive, E_kin_in, brakePool: E_kin_out - W_res_decel };
}

line(); console.log('Stage-1e  六车能量账闭环（试验质量口径，φ/η 锚定，逐车 Crr）'); line();
console.log(`  参数：η=${ETA}  φ=${PHI}(锚定中点)  附件低压=${P_ACC} kWh/100km  Crr 逐车(0.0065~0.0075，P2 查轮胎)`);
console.log('');

const HDR = ['车型', '试验质量', '阻力功', '动能注入', '制动池', '毛消耗', '回收', '净输出', '官方CLTC', '残差', '回收贡献率'];
const W = [22, 8, 8, 8, 8, 8, 8, 8, 9, 8, 10];
console.log(HDR.map((h, i) => pad(h, W[i])).join(''));
console.log('-' .repeat(108));

const rows = [];
for (const c of CARS) {
  const r = integrate(c);
  const res_kwh  = e(r.W_res_drive / 3.6e6);       // 阻力功 kWh/100km
  const kin_kwh  = e(r.E_kin_in / 3.6e6);          // 动能注入
  const pool_kwh = e(r.brakePool / 3.6e6);         // 制动池
  const gross    = (res_kwh + kin_kwh) / ETA + P_ACC; // 毛消耗（驱动/η + 附件）
  const regen    = PHI * pool_kwh;                 // 回收贡献
  const net      = gross - regen;                  // 净输出
  const resid    = net - c.cltcE;                  // 残差（未建模项）
  const ratio    = regen / gross * 100;            // 回收贡献率%
  rows.push({ c, r, res_kwh, kin_kwh, pool_kwh, gross, regen, net, resid, ratio });
  console.log(
    pad(c.n, W[0]) + pad(f1(r.m), W[1]) + pad(f2(res_kwh), W[2]) + pad(f2(kin_kwh), W[3])
    + pad(f2(pool_kwh), W[4]) + pad(f2(gross), W[5]) + pad(f2(regen), W[6])
    + pad(f2(net), W[7]) + pad(f2(c.cltcE), W[8]) + pad(f2(resid), W[9]) + pad(f1(ratio) + '%', W[10])
  );
}

line(); console.log('读法'); line();
console.log('  1. 残差 = 净输出 − 官方CLTC，是"未建模项"（热管理/低压精度/测试条件），不是效率排名');
console.log('  2. 回收贡献率 = 回收 ÷ 毛消耗，对照外部口径：Model 3 阿贡车队 = 24%');
console.log('  3. 若六车回收贡献率都落在 20~30% 附近 → 模型结构与 φ=0.65 自洽');
console.log('  4. 残差若系统性地随车型变化 → 说明 Crr 统一 0.009 掩盖了真实差异（P2 要补的）');
console.log('');

line(); console.log('敏感性：φ 扫 0.60~0.70 的残差带（η 固定 0.91）'); line();
for (const row of rows) {
  const { res_kwh, kin_kwh, pool_kwh } = row;
  const g = (res_kwh + kin_kwh) / ETA + P_ACC;
  const r0 = g - 0.60 * pool_kwh - row.c.cltcE;
  const r1 = g - 0.70 * pool_kwh - row.c.cltcE;
  console.log(`  ${pad(row.c.n, 22)} 残差 [${r0.toFixed(2)}, ${r1.toFixed(2)}] kWh/100km（φ↑ → 残差↓）`);
}

line(); console.log('敏感性：η 扫 0.88~0.93 的残差（φ 固定 0.65）'); line();
for (const row of rows) {
  const { res_kwh, kin_kwh, pool_kwh } = row;
  const nums = [0.88, 0.91, 0.93].map(eta => {
    const g = (res_kwh + kin_kwh) / eta + P_ACC;
    return (g - PHI * pool_kwh - row.c.cltcE).toFixed(2);
  });
  console.log(`  ${pad(row.c.n, 22)} η=0.88/0.91/0.93 → 残差 [${nums[0]}, ${nums[1]}, ${nums[2]}]`);
}
console.log('');
console.log('  → η 每 +0.02 压掉约 0.3 kWh/100km；η=0.93 时六车残差是否普遍收进 ±0.7');
console.log('');
console.log('  → 残差带若包含 0 附近 = 该车能量账闭合；若整体偏正 = Crr/A 高估（阻力功虚高）');
console.log('  → 若整体偏负 = Crr/A 低估 或 附件被低估');
