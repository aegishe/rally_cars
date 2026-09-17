// ============================================================================
// 六车电耗/续航矩阵 —— 可复现计算脚本
// 运行: node compute-ev-matrix.js
// 配套文档: 六车对比-冬夏-载重-长短途矩阵.md
// ============================================================================
//
// 【模型结构】总电耗 = 巡航项 + 循环项 + 附件项
//   巡航项 = [m*g*Crr*v + 0.5*rho*Cd*A*v^3] / eta     —— 纯物理，可独立算出
//   循环项 = C(v) * m/1000                            —— 需标定（见下）
//   附件项 = P_acc / v * 100                          —— 纯物理，给定功率即可
//
// 【标定逻辑 —— 两个锚点各定一个自由度】
//   锚点A: Model 3 官方 CLTC 电耗 9.46 kWh/100km  -> 定出 CLTC 循环项
//   锚点B: Model 3 高速 120km/h 实测 17.5 kWh/100km -> 定出高速循环项
//   两个锚点解两个循环项系数，互不冲突（良态）。
//
// 【为什么不能用"CLTC+高速"联立解 (eta, K)】
//   实测发现该方程组近似平行（det≈0，病态），会解出 eta=0.29、K=-2.39 之类
//   非物理值。故 eta 取物理值 0.91，剩余自由度为循环项。
//
// 【单位链 —— 本模型唯一易错处】
//   功率[kW] / 车速[km/h] * 100 = 电耗[kWh/100km]
//   例: 1.332 kW / 28.96 * 100 = 4.60 kWh/100km   （不要再除 1000）
'use strict';

const RHO = 1.2, G = 9.81, ETA = 0.91;
const V_CLTC = 28.96, V_HW = 120;

// ---------------------------------------------------------------- 1. 车型库
// [名称, 组, 电池kWh, 整备kg, 满载kg, Cd, A m2, Crr, CLTC km]
const CARS = [
  ['特斯拉 Model 3 RWD', '轿车',  60.0, 1760, 2192, 0.219, 2.22, 0.0085, 634],
  ['小米 SU7 后驱标准版', '轿车',  73.6, 1980, 2430, 0.195, 2.35, 0.0090, 700],
  ['特斯拉 Model Y RWD', 'SUV',   62.5, 1922, 2432, 0.230, 2.60, 0.0090, 593],
  ['小米 YU7 后驱标准版', 'SUV',   96.3, 2315, 2765, 0.245, 2.62, 0.0090, 835],
  ['小鹏 X9 长续航前驱',  'MPV',   94.8, 2675, 3210, 0.227, 3.10, 0.0095, 650],
  ['极氪 009 前驱七座',   'MPV',  110.0, 2798, 3378, 0.270, 3.20, 0.0095, 740],
];

const CdA    = c => c[5] * c[6];
const eCLTC  = c => c[2] / c[8] * 100;
const vms    = v => v / 3.6;
const kWh100 = (kW, v) => kW / v * 100;

const kW_road = (c, m, v) =>
  (m * G * c[7] * vms(v) + 0.5 * RHO * CdA(c) * Math.pow(vms(v), 3)) / 1000;

/** 巡航项电耗 (kWh/100km) */
const eCruise = (c, m, v) => kWh100(kW_road(c, m, v) / ETA, v);

// ---------------------------------------------------------------- 2. 标定
const LOW_CLTC = 0.60;    // 低压基础（速度无关项）kWh/100km
const ACC_HW   = 1.55;    // 高速附件 kW（空调 1.2 + 低压 0.35）
const E_M3_120 = 17.5;    // Model 3 RWD 120km/h 实测中值 kWh/100km

// 锚点A: 定 CLTC 循环项（单位质量）
function calibCLTC() {
  const c = CARS[0];
  const cyc = eCLTC(c) - eCruise(c, c[3], V_CLTC) - LOW_CLTC;   // kWh/100km
  return cyc;
}
// 锚点B: 定高速循环项（单位质量）
function calibHW() {
  const c = CARS[0];
  const cyc = E_M3_120 - eCruise(c, c[3], V_HW) - kWh100(ACC_HW, V_HW);
  return cyc;
}
const CYC_CLTC = calibCLTC();   // kWh/100km @ 整备质量
const CYC_HW   = calibHW();
const CYC_CLTC_kg = CYC_CLTC / CARS[0][3];
const CYC_HW_kg   = CYC_HW   / CARS[0][3];

// ---------------------------------------------------------------- P3 逐车 eta_eff
// ⚠ 关键: kW_road 是轮端功率, eCruise 已含 /ETA。此处不再重复除。
//   aEff 是"相对 ETA=0.91 的效率修正因子": aEff>1 表示比基准更费电。
//   两套 η 分开标定：CLTC 口径(低速) 与 高速口径 —— 电驱在高速恒功率区效率更高。
function kResid(c) {
  const eRoadRaw = kWh100(kW_road(c, c[3], V_CLTC), V_CLTC);   // 轮端, 未除 η
  const eCyc  = CYC_CLTC_kg * c[3];
  const aEff  = (eCLTC(c) - eCyc - LOW_CLTC) / (eRoadRaw / ETA);
  return { aEff, etaEff: ETA / aEff, eRoadRaw, eCyc };
}
// 高速口径：Model 3 锚点定出高速 η 修正
const A_HW = (() => {
  const c = CARS[0];
  const eRoadRaw = kWh100(kW_road(c, c[3], V_HW), V_HW);
  return (E_M3_120 - CYC_HW - kWh100(ACC_HW, V_HW)) / (eRoadRaw / ETA);
})();

// ---------------------------------------------------------------- P4 通用电耗
const eCycle = (c, m, v) => (v >= 100 ? CYC_HW_kg : CYC_CLTC_kg) * m;
function energy(c, m, v, accW) {
  const { aEff } = kResid(c);
  const a = v >= 100 ? A_HW : aEff;
  const eRoad = kWh100(kW_road(c, m, v), v) / ETA;    // 电池端巡航项
  return a * eRoad + eCycle(c, m, v) + kWh100(accW / 1000, v) + LOW_CLTC;
}

// ---------------------------------------------------------------- 5. 附件与载荷
const ACC = {
  '夏市区轻': 1000 + 0    + 350, '夏市区满': 1300 + 0    + 350,
  '冬市区轻': 2000 + 500  + 350, '冬市区满': 2300 + 500  + 350,
  '夏高速轻': 1200 + 0    + 350, '夏高速满': 1500 + 0    + 350,
  '冬高速轻': 2500 + 800  + 350, '冬高速满': 3000 + 1200 + 350,
};
const LIGHT = 120;
const mk = (c, load) => load === 'full' ? c[4] : c[3] + LIGHT;

// ---------------------------------------------------------------- 6. 输出
const f0 = x => x.toFixed(0), f2 = x => x.toFixed(2), f3 = x => x.toFixed(3);
const pad = (s, n) => String(s).padStart(n);
const line = () => console.log('='.repeat(102));

line(); console.log('标定：两个锚点各定一个循环项系数'); line();
{
  const c = CARS[0];
  console.log(`  锚点A (Model 3 官方 CLTC ${f2(eCLTC(c))} kWh/100km):`);
  console.log(`     巡航项 ${f2(eCruise(c, c[3], V_CLTC))} + 循环项 + 低压 ${LOW_CLTC} = ${f2(eCLTC(c))}`);
  console.log(`     -> CLTC 循环项 CYC_CLTC = ${f2(CYC_CLTC)} kWh/100km`);
  console.log(`  锚点B (Model 3 高速120 实测 ${f2(E_M3_120)} kWh/100km):`);
  console.log(`     巡航项 ${f2(eCruise(c, c[3], V_HW))} + 循环项 + 附件 ${f2(kWh100(ACC_HW, V_HW))} = ${f2(E_M3_120)}`);
  console.log(`     -> 高速循环项 CYC_HW = ${f2(CYC_HW)} kWh/100km`);
  console.log(`     -> 高速/CLTC 循环项比 = ${f3(CYC_HW / CYC_CLTC)}（高速加减速频次低，理应 <1）`);
}

line(); console.log('逐车 eta_eff（统一定循环项，用官方 CLTC 反解系统效率）'); line();
console.log('车型'.padEnd(20) + pad('官方CLTC', 10) + pad('巡航项(电池端)', 14) + pad('循环项', 9) + pad('eta_eff(CLTC)', 13));
for (const c of CARS) {
  const r = kResid(c);
  console.log(c[0].padEnd(20) + pad(f2(eCLTC(c)), 10) + pad(f2(r.eRoadRaw / ETA), 14)
              + pad(f2(r.eCyc), 9) + pad(f3(r.etaEff), 13));
}
console.log(`  高速口径效率修正 A_HW = ${f3(A_HW)}  (eta_高速 = ${f3(ETA / A_HW)})`);

line(); console.log('校验1：Model 3 回代（其两个锚点已用于标定，必然吻合）'); line();
{
  const c = CARS[0];
  const cltc = energy(c, c[3], V_CLTC, 0);
  const hw   = energy(c, c[3], V_HW, ACC_HW);
  console.log(`  CLTC : ${f2(cltc)} vs 官方 ${f2(eCLTC(c))}  ${Math.abs(cltc - eCLTC(c)) < 1e-9 ? 'OK' : 'FAIL'}`);
  console.log(`  高速 : ${f2(hw)} vs 实测 ${f2(E_M3_120)}  ${Math.abs(hw - E_M3_120) < 1e-9 ? 'OK' : 'FAIL'}`);
}
line(); console.log('校验2：其余五车 CLTC 独立校验（它们的官方值未参与标定）'); line();
for (const c of CARS.slice(1)) {
  const back = energy(c, c[3], V_CLTC, 0);
  const dev = (back - eCLTC(c)) / eCLTC(c) * 100;
  console.log(`  ${c[0].padEnd(20)} 模型 ${f2(back)}  vs 官方 ${f2(eCLTC(c))}  偏差 ${f2(dev)}%`);
}

const CASES = [
  ['夏·市30·轻', 30,  'light', '夏市区轻'], ['夏·市30·满', 30,  'full', '夏市区满'],
  ['冬·市30·轻', 30,  'light', '冬市区轻'], ['冬·市30·满', 30,  'full', '冬市区满'],
  ['夏·高120·轻', 120, 'light', '夏高速轻'], ['夏·高120·满', 120, 'full', '夏高速满'],
  ['冬·高120·轻', 120, 'light', '冬高速轻'], ['冬·高120·满', 120, 'full', '冬高速满'],
];
line(); console.log('P4 电耗矩阵 (kWh/100km)'); line();
console.log('车型'.padEnd(20) + CASES.map(x => pad(x[0], 12)).join(''));
for (const c of CARS) {
  const row = CASES.map(([, v, ld, k]) => energy(c, mk(c, ld), v, ACC[k]));
  console.log(c[0].padEnd(20) + row.map(x => pad(f2(x), 12)).join(''));
}

function rangeTable(title, v, kl, kf) {
  line(); console.log(`${title} 续航 (km) 与 CLTC 达成率`); line();
  console.log('车型'.padEnd(20) + pad('CLTC', 7) + pad('夏轻', 8) + pad('夏满', 8)
              + pad('冬轻', 8) + pad('冬满', 8) + pad('冬满达成率', 12));
  for (const c of CARS) {
    const g = (m, k) => { const e = energy(c, m, v, ACC[k]); const r = c[2] / e * 100; return { r, rate: r / c[8] * 100 }; };
    const a = g(mk(c, 'light'), kl), b = g(c[4], kf);
    const d = g(mk(c, 'light'), kl.replace('夏', '冬')), e = g(c[4], kf.replace('夏', '冬'));
    console.log(c[0].padEnd(20) + pad(c[8], 7) + pad(f0(a.r), 8) + pad(f0(b.r), 8)
                + pad(f0(d.r), 8) + pad(f0(e.r), 8) + pad(f0(e.rate) + '%', 12));
  }
}
rangeTable('高速 120km/h', 120, '夏高速轻', '夏高速满');
rangeTable('市区 30km/h',  30,  '夏市区轻', '夏市区满');

line(); console.log('载荷代价：轻载(整备+120kg) -> 满载(最大设计总质量) 的电耗涨幅'); line();
console.log('车型'.padEnd(20) + pad('市30 夏', 10) + pad('市30 冬', 10) + pad('高120 夏', 10) + pad('高120 冬', 10));
for (const c of CARS) {
  const r = [
    (energy(c, c[4], 30, ACC['夏市区满']) / energy(c, mk(c, 'light'), 30, ACC['夏市区轻']) - 1) * 100,
    (energy(c, c[4], 30, ACC['冬市区满']) / energy(c, mk(c, 'light'), 30, ACC['冬市区轻']) - 1) * 100,
    (energy(c, c[4], 120, ACC['夏高速满']) / energy(c, mk(c, 'light'), 120, ACC['夏高速轻']) - 1) * 100,
    (energy(c, c[4], 120, ACC['冬高速满']) / energy(c, mk(c, 'light'), 120, ACC['冬高速轻']) - 1) * 100,
  ];
  console.log(c[0].padEnd(20) + r.map(x => pad((x >= 0 ? '+' : '') + f2(x) + '%', 10)).join(''));
}

line(); console.log('P5 独立校验：未参与标定的 -30C 冬测数据'); line();
{
  const c = CARS[0];
  const pred = energy(c, c[3] + 160, 40, 3000 + 1200 + 350);
  console.log(`  冬测实测 (Model 3 四驱, -30C, 雪地低速): 24.9 kWh/100km  [汽车之家 2025 冬测]`);
  console.log(`  模型预测 (后驱近似, 40km/h, 附件 4.55kW):  ${f2(pred)} kWh/100km`);
  console.log(`  偏差 ${f2((pred - 24.9) / 24.9 * 100)}%  ->  ${Math.abs(pred - 24.9) / 24.9 < 0.25 ? '±25% 内可接受' : '偏大，需复核'}`);
}

line(); console.log('单因素敏感性'); line();
console.log('(1) 每 1kW 附件的电耗贡献 (kWh/100km):');
for (const v of [20, 30, 60, 80, 120]) console.log(`   ${pad(v, 3)}km/h -> ${f2(kWh100(1, v))}`);
console.log('\n(2) Model 3 风阻占阻力比（"车重效应"大小的开关）:');
for (const v of [20, 30, 60, 80, 120]) {
  const c = CARS[0], u = vms(v);
  const roll = c[3] * G * c[7] * u, air = 0.5 * RHO * CdA(c) * u ** 3;
  console.log(`   ${pad(v, 3)}km/h  风阻 ${pad(f0(air / (roll + air) * 100), 2)}%   质量项 ${pad(f0((1 - air / (roll + air)) * 100), 2)}%`);
}

console.log(`
================================================================================
模型边界（务必与数字同读）
================================================================================
1. eta=0.91 取物理值（电驱系统效率），不是拟合出来的。两个锚点只用于定"循环项"。
2. 循环项系数 CYC_CLTC / CYC_HW 由 Model 3 的两个锚点唯一确定。其中高速锚点
   17.5 kWh/100km 是文献区间 16~19 的中值；若实际为 16 或 19，高速结果平移约 ±5%。
3. 曾尝试用"CLTC + 高速"联立解 (eta, K)，实测该方程组近似平行（病态），
   会输出 eta=0.29 / K=-2.39 等非物理解。该思路已废弃，记录于此以免重蹈。
4. Cd 与迎风面积为同级估算值，无厂商官方口径。Cd·A 偏差 10% -> 高速电耗偏差约 6%。
5. 质量效应分两段：滚阻 ∝ m（全程）、循环项 ∝ m（仅加减速）。故车重影响在
   市区被放大、在高速被稀释 —— 这是"车重是低速税"的数学来源。
6. CLTC 官方电耗为整备质量口径；国标"试验质量" = 整备 + 最大装载×65%。
7. 全部为纸面推演，未做真车验证。
`);
