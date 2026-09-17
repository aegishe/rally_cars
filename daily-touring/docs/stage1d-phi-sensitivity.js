// ============================================================================
// Stage-1d  φ 反推的敏感性扫描 —— 对照外部"回收比例"口径
// 运行: node stage1d-phi-sensitivity.js
// ============================================================================
//
// 【背景】分享的 DeepSeek 回答称 Model 3 "回收比例 24%(SOC<80%) / 城市36% / 高速10%"
//   （阿贡实验室 Argonne 测试，美国循环）。我们模型反推的 φ 却是 ~0.6~0.9。
//   本脚本扫描 (质量口径, Crr, η, 附件) 组合，看 φ 反推值能否与外部口径调和。
//
// 【方程】（P1 精确账，Model 3，CLTC 循环，全程 kWh）
//   e_bat(官方) = 驱动需求/η_drive − φ×制动池/η_regen + 附件
//   反推 φ = [驱动需求/η + 附件 − e_bat] × η_regen / 制动池
//
// 【质量口径】CLTC 官方电耗用"试验质量 = 整备 + 65%×最大装载"测，
//   不是整备质量。Model 3: 整备1760 / 满载2192 → 试验质量 2040.8 kg。
//   质量项(滚阻+动能) ∝ m，风阻项不 ∝ m。
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');
const G = 9.81, RHO = 1.2;

// Model 3 参数
const Cd = 0.219, A = 2.22;
const M_kerb = 1760, M_gross = 2192;
const M_test = M_kerb + 0.65 * (M_gross - M_kerb); // 试验质量 ≈ 2040.8

// 官方 CLTC 全程电耗 kWh = 9.46 kWh/100km × 14.48km
const E_BAT = 9.46 * 14.48 / 100;

const f3 = x => x.toFixed(3), pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(100));

// 逐秒积分：给定质量 m 和 Crr，返回 {W_res_drive, E_kin_in, brakePool}
// brakePool = 减速释放动能 − 减速段阻力帮减（= φ 作用的回收池）
function integrate(m, crr) {
  let W_res_drive = 0, E_kin_in = 0, W_res_decel = 0, E_kin_out = 0;
  for (let t = 0; t < 1800 - 1; t++) {
    const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
    const P_res = m * G * crr * v + 0.5 * RHO * Cd * A * v * v * v;
    const dK = 0.5 * m * (vn * vn - v * v);
    if (dK >= 0) { W_res_drive += P_res; E_kin_in += dK; }
    else { W_res_decel += P_res; E_kin_out += -dK; }
  }
  const drive = W_res_drive + E_kin_in;          // 轮端驱动需求 kWh
  const brakePool = E_kin_out - W_res_decel;      // 制动吸收池 kWh
  return { drive, brakePool };
}

// 反推 φ（drive/brakePool 为 J，需 /3.6e6 转 kWh）★ J→kWh 除 3.6e6
const phi = (driveJ, brakePoolJ, eta, pAcc) => {
  const drive = driveJ / 3.6e6, brakePool = brakePoolJ / 3.6e6;
  const eAcc = pAcc * 14.48 / 100; // kWh
  return (drive / eta + eAcc - E_BAT) * eta / brakePool;
};

line(); console.log('Stage-1d  φ 反推敏感性扫描（Model 3）'); line();
console.log(`  官方 CLTC 电耗 ${E_BAT.toFixed(3)} kWh（9.46 kWh/100km × 14.48km）`);
console.log(`  质量口径：整备 ${M_kerb} / 试验 ${M_test.toFixed(1)}（+65%装载）`);
console.log('');
console.log('  反推 φ 表格（行=质量口径×Crr，列=η，附件统一低压 0.6 kWh/100km）：');
console.log('');

const cols = [0.88, 0.91, 0.94];
console.log('  口径×Crr'.padEnd(26) + cols.map(c => pad('η=' + c, 14)).join(''));
for (const [mName, m] of [['整备质量', M_kerb], ['试验质量', M_test]]) {
  for (const crr of [0.008, 0.009]) {
    const { drive, brakePool } = integrate(m, crr);
    const row = cols.map(eta => phi(drive, brakePool, eta, 0.6).toFixed(3));
    console.log('  ' + pad(`${mName} Crr=${crr}`, 24) + row.map(r => pad(r, 14)).join(''));
  }
}
console.log('');
console.log('  → 外部口径对照：阿贡"回收比例24%" 若指"回收/制动吸收池"，则 φ≈0.24');
console.log('  → 若指"回收/减速释放动能"，换算 φ = 24% × (减速释放/制动池) ≈ 0.37~0.41');
console.log('');

line(); console.log('结论'); line();
const { drive, brakePool } = integrate(M_test, 0.009);
console.log(`  试验质量 Crr=0.009：驱动需求 ${(drive/3.6e6/14.48*100).toFixed(1)}、制动池 ${(brakePool/3.6e6/14.48*100).toFixed(1)} kWh/100km`);
console.log('  φ 反推值落在 [x]；与外部"24%/36%"口径是否重合，见下方文字分析');
console.log('');

// 额外输出：把 φ 固定到外部口径，反推需要的 η 或 Crr
line(); console.log('反向检验：若 φ=0.40（外部口径换算），需要什么 η？'); line();
for (const [mName, m] of [['整备质量', M_kerb], ['试验质量', M_test]]) {
  for (const crr of [0.008, 0.009]) {
    const d = integrate(m, crr);
    const drive = d.drive / 3.6e6, brakePool = d.brakePool / 3.6e6;
    // φ=0.40 时，解 η：drive/η + pAcc - φ*brakePool/η = E_BAT
    // => (drive - φ*brakePool)/η = E_BAT - pAcc
    const etaNeed = (drive - 0.40 * brakePool) / (E_BAT - 0.6 * 14.48 / 100);
    console.log(`  ${mName} Crr=${crr}: φ=0.40 需要 η = ${etaNeed.toFixed(3)}`);
  }
}
console.log('');
console.log('  → η 需 >1（超物理）即说明"φ=0.40 无法复现官方 9.46"，矛盾真实存在');
console.log('  → η 需 <0.93 则说明可调和（参数偏差能解释口径差）');
