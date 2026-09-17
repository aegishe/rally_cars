// ============================================================================
// Stage-1 反推阶段 v2 —— 显式方程数/未知数审计
// 运行: node stage1-inference.js
// ============================================================================
//
// 【本版的核心改变】不再把"官方总电耗反解"包装成效率，而是显式清点：
//     有几个观测（方程）  vs  有几个未知量
//   只有方程数 >= 未知数，反推才成立。
//
// 【数据来源】
//   GB/T 38146.1-2019 表1（CLTC-P 特征参数，一手）
//   各车官方 CLTC 续航与电池容量（申报口径）
//   高速 120km/h 实测电耗区间（媒体横评）
//
// 【纪律】本阶段只在 CLTC 标准条件下反推：23±5℃ / 空调关闭 / 统一参数
'use strict';

// ---------------------------------------------------------------- 一手特征表
const CLTC = {
  total: { time: 1800, dist: 14.48, vmax: 114.00, aAcc: 0.45, rAcc: 0.2878, vAvg: 28.96, vRun: 37.18 },
  segs: [
    { n: '1部 低速', time: 674, dist: 2.45, vmax: 48.10, aAcc: 0.42, rAcc: 0.2255, vAvg: 13.09, vRun: 20.20, rIdle: 0.3516 },
    { n: '2部 中速', time: 693, dist: 5.91, vmax: 71.20, aAcc: 0.46, rAcc: 0.3045, vAvg: 30.68, vRun: 38.24, rIdle: 0.1977 },
    { n: '3部 高速', time: 433, dist: 6.12, vmax: 114.00, aAcc: 0.46, rAcc: 0.3580, vAvg: 50.90, vRun: 53.89, rIdle: 0.0550 },
  ],
};

// ---------------------------------------------------------------- 统一参数
const ETA = 0.91;        // 电驱系统效率（厂商公开口径 0.90~0.93）
const PHI = 0.60;        // 动能回收效率（待定，见审计）
const LOW = 0.60;        // 低压/常电 kWh/100km（标准条件）
const G = 9.81, RHO = 1.2;

// CLTC 动能当量（逐秒增量平方和，需精确曲线；此处用质量比例传递）
// Model 3 基准: 由官方电耗 - 阻力 - 低压 = 净动能项
const CARS = [
  { n: '特斯拉 Model 3 RWD',  wh: 60.0,  m: 1760, Cd: 0.219, A: 2.22, Crr: 0.0090, cltc: 634 },
  { n: '小米 SU7 后驱标准版',  wh: 73.6,  m: 1980, Cd: 0.195, A: 2.30, Crr: 0.0090, cltc: 700 },
  { n: '特斯拉 Model Y RWD',  wh: 62.5,  m: 1922, Cd: 0.230, A: 2.60, Crr: 0.0090, cltc: 593 },
  { n: '小米 YU7 后驱标准版',  wh: 96.3,  m: 2315, Cd: 0.245, A: 2.60, Crr: 0.0090, cltc: 835 },
  { n: '小鹏 X9 长续航前驱',   wh: 94.8,  m: 2675, Cd: 0.227, A: 3.00, Crr: 0.0090, cltc: 650 },
  { n: '极氪 009 前驱七座',    wh: 110.0, m: 2798, Cd: 0.270, A: 3.00, Crr: 0.0090, cltc: 740 },
];

const vms = v => v / 3.6;
const f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(108));

// ---------------------------------------------------------------- 物理量
const kW_res = (c, v) => (c.m * G * c.Crr * vms(v) + 0.5 * RHO * c.Cd * c.A * Math.pow(vms(v), 3)) / 1000;
const eCLTC  = c => c.wh / c.cltc * 100;
const kW_off = c => eCLTC(c) * CLTC.total.vAvg / 100;
// 净动能项（余项，非独立推导）
const kW_kinNet = c => kW_off(c) - kW_res(c, CLTC.total.vAvg) - LOW * CLTC.total.vAvg / 100;

line(); console.log('Stage-1 v2  方程数 / 未知数 审计'); line();

// ---------------------------------------------------------------- 审计表
console.log('【观测（方程）清单】');
console.log('  编号  观测                        数量        来源');
console.log('  O1    CLTC 总电耗（每车1个）       6          官方申报（电池/续航）');
console.log('  O2    CLTC 分段电耗（每车3个）     0（未获取）  中汽研缩短法可给分段续航');
console.log('  O3    120km/h 实测电耗            0（未获取）  媒体横评（区间值）');
console.log('  O4    逐秒速度曲线                0（未获取）  GB/T 38146.1 表A.1');
console.log('');

console.log('【未知量清单】');
console.log('  编号  未知量                  每车数量   性质');
console.log('  U1    电驱系统效率 eta        1          可查厂商口径（0.90~0.93）');
console.log('  U2    动能回收效率 phi        1          无公开口径');
console.log('  U3    滚阻系数 Crr            1          轮胎属性，可查标签');
console.log('  U4    热管理/低压基线         1          有量级，无精确值');
console.log('  U5    动能当量 sum(dv^2)/2    1          需逐秒曲线');
console.log('');

line(); console.log('结论：当前状态下，每车 1 个观测(O1) vs 5 个未知量 → 严重欠定'); line();
console.log('  可做的近似：U1 取厂商口径、U3 统一取 0.0090、U4 统一取 0.60');
console.log('              → 仍剩 U2 与 U5 两个未知量，1 个方程解不出');
console.log('  → 因此"官方电耗反解效率"在数学上不成立；此前的综合效率实为恒等式');
console.log('');

// ---------------------------------------------------------------- 可确定量
line(); console.log('可确定量 A：分段阻力功率（纯物理，不依赖任何标定）'); line();
const c0 = CARS[0];
console.log('段'.padEnd(12) + pad('运行车速', 10) + pad('阻力kW', 9) + pad('时间占比%', 11) + pad('里程占比%', 11) + pad('阻力功占比%', 12));
const totDist = CLTC.segs.reduce((a, s) => a + s.dist, 0);
let totWork = 0;
const works = CLTC.segs.map(s => { const w = kW_res(c0, s.vRun) * s.time; totWork += w; return w; });
CLTC.segs.forEach((s, i) => {
  const w = kW_res(c0, s.vRun);
  console.log(s.n.padEnd(12) + pad(f2(s.vRun), 10) + pad(f3(w), 9)
    + pad((s.time / 1800 * 100).toFixed(1), 11) + pad((s.dist / totDist * 100).toFixed(1), 11)
    + pad((works[i] / totWork * 100).toFixed(1), 12));
});
console.log('  → 高速段占 24.1% 时间、42.3% 里程，却贡献 ' + (works[2] / totWork * 100).toFixed(1) + '% 的阻力功（Model 3）');
console.log('  → 这是 CLTC 的"隐含高速税"，被总体平均车速 28.96 掩盖');
console.log('');

line(); console.log('可确定量 B：附件税（纯数学，无参数自由度）'); line();
console.log('  每 1kW 附件的电耗 = 100/v  kWh/100km');
for (const v of [20, 30, 60, 80, 120]) {
  console.log('    ' + pad(v, 3) + ' km/h -> ' + f2(100 / v) + ' kWh/100km');
}
console.log('  → 低速工况的附件"每公里代价"是高速的 6 倍');
console.log('');

// ---------------------------------------------------------------- 欠定示范
line(); console.log('欠定示范：余项动能项与质量不成比例（说明 U2/U5 未被分离）'); line();
console.log('车型'.padEnd(22) + pad('整备kg', 8) + pad('阻力kW', 9) + pad('净动能kW', 10) + pad('净动能/kg', 12));
for (const c of CARS) {
  const k = kW_kinNet(c);
  console.log(c.n.padEnd(22) + pad(c.m, 8) + pad(f3(kW_res(c, CLTC.total.vAvg)), 9)
    + pad(f3(k), 10) + pad((k / c.m * 1000).toFixed(3), 12));
}
console.log('  → 若动能项纯由质量决定，最后一列应恒定；实际在 ' +
  (Math.min(...CARS.map(c => kW_kinNet(c) / c.m * 1000)).toFixed(3)) + ' ~ ' +
  (Math.max(...CARS.map(c => kW_kinNet(c) / c.m * 1000)).toFixed(3)) + ' 之间浮动');
console.log('  → 浮动部分 = 各车 U2/U4 的真实差异，但当前无法从 1 个观测中分离');

// ---------------------------------------------------------------- 缺口方案
console.log('');
line(); console.log('补观测方案：每加一个观测，就解锁一个未知量'); line();
console.log('  要解出的东西              需要补的观测                        可行性');
console.log('  ----------------------------------------------------------------');
console.log('  分段动能项 U5             O4 逐秒曲线                        国标表A.1（已在你手上）');
console.log('  动能回收效率 U2           O3 高速实测电耗（+已知Crr）        媒体横评可得');
console.log('  分段效率差异              O2 分段电耗/分段续航               中汽研缩短法');
console.log('  真实滚阻 U3              轮胎 EU 标签 / 滚阻试验             部分车型可查');
console.log('');
console.log('  最小可行组合：O1 + O3 + Crr  → 可解 eta 与 phi（两方程两未知量）');
console.log('  完全解：O1 + O2 + O3 + O4    → 可解分段效率曲线');

console.log('');
console.log('='.repeat(108));
console.log('本阶段可交付的三条硬结论');
console.log('='.repeat(108));
console.log('  1. CLTC-P 特征表闭合（14.48km / 1800s / 518s加速），拥堵集中在一部(怠速35.16%)');
console.log('  2. 分段阻力功率：低速0.923 / 中速2.000 / 高速3.305 kW；高速段占24%时间却占42%里程');
console.log('  3. 附件税 = 100/v (kWh/100km per kW)，低速代价是高速的6倍');
console.log('');
console.log('  不能交付：任何形式的"整车效率排名"——欠定，且综合效率为恒等式');
console.log('');
