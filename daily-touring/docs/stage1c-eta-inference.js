// ============================================================================
// Stage-1c  用"通用空调功率"补足高速方程，解 η 的示范 + 敏感性分析
// 运行: node stage1c-eta-inference.js
// ============================================================================
//
// 【背景】P0 的第二个障碍：高速实测都开空调，方程 e_120 = e_road/η + e_空调
//   有 η 与 P_空调 两个未知量。本脚本用"通用空调功率"固定 P_空调，
//   把方程降到 1 未知量（η），看解出的 η 是否物理合理、对假设有多敏感。
//
// 【空调功率来源】（2026-09-17 检索，见 P0 文档 §附录）
//   夏季制冷稳态（24℃设定、28~33℃外温）：
//     轿车/SUV  1.0 ~ 1.5 kW   （Model 3 车主实测 21℃=1.03 / 24℃=1.44 / 26℃=0.94）
//     MPV(大空间) 1.5 ~ 2.5 kW
//   易车夏测"空调24℃自动、满载"→ 轿车/SUV 取 1.5、MPV 取 2.0 为基准，做 ± 敏感带
//
// 【数据】易车 2024 夏测「平均 120km/h 极限续航」：Model Y 单电机 19.2、X9 单电机 24.94
//   （满载+空调24℃+动能回收最低+28℃；其余车是双电机版，不参与本示范）
//
// 【纪律】η 的解对 Crr / A / P_空调 高度敏感 → 只给范围，不给假精确的单值。
// ============================================================================
'use strict';

const G = 9.81, RHO = 1.2, V = 120 / 3.6; // 33.33 m/s

// 能对上易车口径的两台（满载质量 + 官方 Cd + 估算 A）
const CARS = [
  { n: 'Model Y 单电机(易车)', e120: 19.2,  m: 2432, Cd: 0.230, A: 2.60, pAC: [1.0, 1.25, 1.5],       kind: 'SUV'  },
  { n: '小鹏 X9 单电机(易车)', e120: 24.94, m: 3210, Cd: 0.227, A: 3.00, pAC: [1.5, 2.0, 2.5],         kind: 'MPV'  },
];

const f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(96));

// 轮端阻力电耗（kWh/100km）不含 η
const eRoad = (c, crr) => {
  const P = c.m * G * crr * V + 0.5 * RHO * c.Cd * c.A * V * V * V; // W
  return P / 1000 / 120 * 100; // kWh/100km（= P[kW] ÷ 120km/h × 100）★ W→kW 除 1000
};
// 空调电耗（kWh/100km）
const eAC = p => p / 120 * 100;
// 解 η = e_road / (e_120 − e_空调)
const eta = (c, crr, pAC) => eRoad(c, crr) / (c.e120 - eAC(pAC));

line(); console.log('Stage-1c  用通用空调功率解 η（敏感性分析）'); line();
console.log('  公式：e_120 = e_road(Crr,A)/η + e_空调(P_AC)  →  η = e_road / (e_120 − e_空调)');
console.log('  物理合理区间：电驱系统 η ≈ 0.88 ~ 0.93（厂商公开口径）');
console.log('');

for (const c of CARS) {
  console.log(`${c.n}  实测 e_120 = ${c.e120} kWh/100km  满载 ${c.m}kg  Cd ${c.Cd}  A ${c.A}`);
  console.log('  轮端阻力电耗 e_road（随 Crr）：');
  console.log('  Crr'.padEnd(8) + 'e_road'.padEnd(12) + c.pAC.map(p => `P_AC=${p}kW→η`).join('    '));
  for (const crr of [0.007, 0.008, 0.009, 0.010]) {
    const er = eRoad(c, crr);
    const row = c.pAC.map(p => eta(c, crr, p).toFixed(3));
    console.log('  ' + pad(crr.toFixed(3), 6) + pad(f2(er), 12) + row.map(r => pad(r, 12)).join(' '));
  }
  console.log('  → η 落在 0.88~0.93 的组合 = 该车的 (Crr, P_AC) 可行域');
  console.log('');
}

line(); console.log('结论'); line();
console.log('  1. 固定空调功率后，方程从 2 未知量降到 1 未知量（η），方法可行');
console.log('  2. 但 η 对 Crr(±0.001) 和 P_AC(±0.5kW) 都敏感，解是一个"带"不是"点"');
console.log('  3. 各车可行域交叠在 η≈0.88~0.93 附近 → 通用空调功率 + 官方 Cd + Crr≈0.008~0.009 自洽');
console.log('  4. 反推的 φ 必须建立在"η 已由高速方程确定"上；在 Crr/A/P_AC 仍假设时，φ 仍是区间值');
console.log('');
console.log('  → 这正是 P2（补真实 Crr）的价值：把 η 的带压窄，φ 才能跟着压窄');
