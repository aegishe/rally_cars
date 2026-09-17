// ============================================================================
// Stage-1i  扩展到更多车型：反推三电效率 η + 续航矩阵
// 运行: node stage1i-more-cars.js
// ============================================================================
// 【参数口径】Cd/尺寸/电池/CLTC 为官方公布值；整备/满载为工信部申报口径，
//   未经逐台复核，误差 ±50kg → η 误差约 ±0.02。精确名次需再核，排序大方向可靠。
// 【Crr】默认 EV 低滚阻胎 0.0070（轿车/SUV）、0.0075（MPV），沿用 stage1h。
// ============================================================================
'use strict';

const data = require('./cltc-p-1800points.json');
const G = 9.81, RHO = 1.2, DIST = 14.48;

// { n, m0整备, mg满载, W宽mm, H高mm, Cd, wh电池, cltc续航, crr }
const CARS = [
  // —— 原六车（参数已复核，Crr 为 P2 查实值）——
  { n: 'Model 3 RWD',     m0:1760, mg:2192, W:1849, H:1442, Cd:0.219, wh:60.0,  cltc:634, crr:0.0070 },
  { n: 'SU7 后驱标准',    m0:1980, mg:2430, W:1963, H:1440, Cd:0.195, wh:73.6,  cltc:700, crr:0.0065 },
  { n: 'Model Y RWD',     m0:1922, mg:2432, W:1921, H:1624, Cd:0.230, wh:62.5,  cltc:593, crr:0.0070 },
  { n: 'YU7 后驱标准',    m0:2315, mg:2765, W:1996, H:1600, Cd:0.245, wh:96.3,  cltc:835, crr:0.0070 },
  { n: 'X9 长续航前驱',   m0:2675, mg:3210, W:1988, H:1785, Cd:0.227, wh:94.8,  cltc:650, crr:0.0075 },
  { n: '009 前驱七座',    m0:2798, mg:3378, W:2024, H:1812, Cd:0.270, wh:110.0, cltc:740, crr:0.0067 },
  // —— 新车型（参数待复核，Crr 默认 EV 低滚阻胎）——
  { n: '比亚迪汉 EV',     m0:1940, mg:2320, W:1910, H:1495, Cd:0.233, wh:76.14, cltc:705, crr:0.0080 }, // 2026闪充版：整备1940/电耗10.8；原配马牌MC6(操控胎)/Primacy/GitiControl，非低滚阻EV胎→Crr 0.0080
  { n: '极氪 007 后驱',   m0:2290, mg:2665, W:1900, H:1450, Cd:0.219, wh:100.0, cltc:870, crr:0.0070 },
  { n: '小鹏 G6',         m0:1995, mg:2390, W:1920, H:1650, Cd:0.248, wh:87.5,  cltc:755, crr:0.0070 },
  { n: '智己 LS6',        m0:2432, mg:2900, W:1988, H:1660, Cd:0.237, wh:100.0, cltc:702, crr:0.0070 }, // 高配整备2432(2023款)，CLTC 702
  { n: '理想 MEGA',       m0:2790, mg:3360, W:1965, H:1850, Cd:0.215, wh:102.7, cltc:710, crr:0.0075 },
  { n: '问界 M9 纯电',    m0:3020, mg:3600, W:1999, H:1800, Cd:0.264, wh:120.0, cltc:750, crr:0.0075 }, // 2026款整备超3吨、120kWh、CLTC750
  // —— 补充 SUV（参数待复核；ES6/M9 为双电机四驱，反推 η 会因双电机损耗偏低约 0.02~0.03）——
  { n: '蔚来 ES6 100kWh', m0:2330, mg:2850, W:1995, H:1703, Cd:0.250, wh:100.0, cltc:650, crr:0.0070 },
  { n: '小鹏 G9 625',    m0:2196, mg:2650, W:1937, H:1680, Cd:0.272, wh:78.2,  cltc:625, crr:0.0070 },
  { n: '极氪 7X 后驱',   m0:2280, mg:2800, W:1930, H:1665, Cd:0.247, wh:75.0,  cltc:605, crr:0.0070 },
  // —— 蔚来横截面（全系双电机四驱+换电，验证"系统性低"）——
  { n: '蔚来 ET5 100kWh', m0:2214, mg:2700, W:1960, H:1499, Cd:0.240, wh:100.0, cltc:740, crr:0.0070 },
  { n: '蔚来 ET7 100kWh', m0:2379, mg:2900, W:1987, H:1509, Cd:0.208, wh:100.0, cltc:705, crr:0.0070 },
  { n: '蔚来 ES8 100kWh', m0:2500, mg:3099, W:2002, H:1756, Cd:0.290, wh:100.0, cltc:635, crr:0.0070 },
];

const PHI = 0.75, P_ACC_LOW = 0.6;
const f1 = x => x.toFixed(0), f2 = x => x.toFixed(1), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(108));

function solve(c) {
  const A = c.W / 1000 * c.H / 1000 * 0.85;
  const crr = c.crr;
  const m = c.m0 + 0.65 * (c.mg - c.m0);
  let Wd = 0, Ek = 0, Wdec = 0, Eo = 0;
  for (let t = 0; t < 1800 - 1; t++) {
    const v = data[t] / 3.6, vn = data[t + 1] / 3.6;
    const P = m * G * crr * v + 0.5 * RHO * c.Cd * A * v * v * v;
    const dK = 0.5 * m * (vn * vn - v * v);
    if (dK >= 0) { Wd += P; Ek += dK; } else { Wdec += P; Eo += -dK; }
  }
  const res = Wd / 3.6e6 / DIST * 100;
  const kin = Ek / 3.6e6 / DIST * 100;
  const pool = (Eo - Wdec) / 3.6e6 / DIST * 100;
  const cltcE = c.wh / c.cltc * 100;
  const eta = (res + kin) / (cltcE - P_ACC_LOW + PHI * pool);
  // 续航
  const eHigh = (pAC) => {
    const v = 120 / 3.6;
    const P = m * G * crr * v + 0.5 * RHO * c.Cd * A * v * v * v;
    return P / 1000 / 120 * 100 / eta + pAC / 120 * 100;
  };
  const ac = c.mpv ? { s: 2.5, w: 3.5 } : { s: 1.5, w: 2.5 };
  return { eta, cltcE, eH_s: eHigh(ac.s), eH_w: eHigh(ac.w), eC_s: cltcE + ac.s / 30 * 100, eC_w: cltcE + ac.w / 30 * 100 };
}

const rows = CARS.map(c => ({ c, ...solve(c) }));

line(); console.log('Stage-1i  12 车反推三电效率 η + 续航（φ=0.75 自洽）'); line();
console.log('  标 ⚠️ = 参数未经逐台复核（新车型）；标 ⚠️η = η 超物理上限(异常)');
console.log('');

line(); console.log('【三电效率 η 排序】'); line();
console.log('排名'.padEnd(5) + '车型'.padEnd(20) + 'CLTC电耗'.padEnd(9) + '反推η'.padEnd(9) + '备注');
const sorted = [...rows].sort((a, b) => b.eta - a.eta);
sorted.forEach((r, i) => {
  const flags = [];
  if (!['Model 3 RWD','SU7 后驱标准','Model Y RWD','YU7 后驱标准','X9 长续航前驱','009 前驱七座'].includes(r.c.n)) flags.push('⚠️');
  if (r.eta > 0.93) flags.push('⚠️η超上限');
  console.log(pad(i + 1, 5) + pad(r.c.n, 20) + pad(f2(r.cltcE), 9) + pad(f3(r.eta), 9) + flags.join(''));
});

line(); console.log('【续航矩阵 km】'); line();
console.log('车型'.padEnd(20) + pad('电池', 6) + pad('CLTC', 7) + pad('高速夏', 8) + pad('高速冬', 8) + pad('市区夏', 8) + pad('市区冬', 8));
for (const r of rows) {
  const c = r.c;
  const R = e => c.wh / e * 100;
  console.log(pad(c.n, 20) + pad(f1(c.wh), 6) + pad(f1(c.cltc), 7) + pad(f1(R(r.eH_s)), 8)
    + pad(f1(R(r.eH_w)), 8) + pad(f1(R(r.eC_s)), 8) + pad(f1(R(r.eC_w)), 8));
}

line(); console.log('读法'); line();
console.log('  η∈0.88~0.93 为物理区间；>0.93 = 官方电耗标低或参数(质量/Cd)偏');
console.log('  新车型整备/满载 ±50kg 误差 → η ±0.02，排序大方向可靠、精确名次需复核');
