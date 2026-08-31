# Helix SPX177：转子螺旋冷却电机案例（持续功率密度样板）

> **记录日期**：2026-08-31
> **来源**：B 站 policeman0077 搬运 Ryan Innis（0 to 100）深度调查视频 BV1Ah4f63EH9 + Helix 官网案例研究 + 两家行业媒体交叉印证
> **一句话结论**：SPX177 用**常规径向磁通结构 + 转子螺旋冷却**做到 650kW 持续 / 28.3kg（持续/峰值比 91%），证明"强化冷却换持续功率"是行业公认路线、Helix 只是把**转子冷却**这个细分做到极致；但它是 F1/FE 级工艺 + 小批量的**贵样板**，未破"零件墙"——对完美电驱架构的价值在**电机选型口径**（持续/峰值比 > 峰值密度），不在成本参考。

## 一、官方参数（口径：Helix 官网 case study + E-Mobility Engineering + APTI 三源互证）

| 参数 | 官方口径 | 备注 |
|---|---|---|
| 持续功率 | **650 kW**（客户 REB 项目要求的稳态规格，台架达成） | "most powerful pure battery EV motor"（Helix 自称） |
| 峰值功率 | **>700 kW**（台架实测 711kW，"obvious potential for more"） | 视频"950hp"=708kW 即此口径 |
| 电机重量 | **28.3 kg**（电机本体） | 视频"28kg"即此 |
| 系统重量 | **41 kg = 电机 28.3 + 双逆变器 ~13 kg** | 6 根高压电缆；不含减速器 |
| 最大转速 | **25,000 rpm** | 需碳纤维套筒约束磁铁 |
| 绕组 | 6 相 = 2×三相，双逆变器分流电流，**低电感** | 低电感换低阻损，但逆变器谐波控制难，需专属软件 |
| 制造定位 | "top end in materials, similar to an F1 or Formula E power unit, small batches" | 官方原话 |
| 开发 | REB 项目，12 人团队 2 年，初始小批量生产中 | 已交付客户 |

**功率密度账**（口径分层）：
- 峰值密度（电机本体）：711 / 28.3 = **25.1 kW/kg**
- 持续密度（电机本体）：650 / 28.3 = **23.0 kW/kg**
- **持续/峰值比 = 650/711 = 91%** ← 核心指标（一般电机仅 40-60%）
- 系统含双逆变器：711/41 = 17.3 kW/kg；650/41 = 15.9 kW/kg

## 二、行业谱系："强化冷却 → 高持续功率"是共识方向

| 路线 | 代表 | 冷却方案 | 持续/峰值表现 |
|---|---|---|---|
| 定子直接冷却（可量产） | **Lucid** | 微喷射冷却：ATF 经定子中缝歧管喷向槽底近端 | 电机 30kg 出 500kW → 16.4 kW/kg 峰值；主打持续表现 |
| 转子约束 + 液冷 | 特斯拉 Plaid | 液冷 + 碳纤维包裹转子（碳纤是**约束磁铁**，非冷却） | 三电机 1020hp；Rawlinson 吐槽碳纤壳量产很贵 |
| 轴向磁通 + 油冷 | YASA | 直接油冷 | 200kW 径向持续仅 50%；200kW YASA 持续 150kW（**75%**） |
| 转子轴心冷却 | Audi | 冷却液穿转子轴心 | 先行者，深度不及 Helix |
| **转子螺旋通道冷却** | **Helix SPX177** | 双管套合 + 螺旋槽贴磁铁底 + 同轴旋转接头 + 末端折返消温差 | **91% 持续/峰值，650kW 持续** |

**Helix 的差异化**：方向是行业共识（Lucid/YASA/Plaid 同路），独门在**把冷却贴到磁铁底下**——解决的是转子发热（谐波/环流损耗随转速上涨、磁铁过热退磁）这个别人没解决彻底的细分。

## 三、成本口径（算不清的地方明说）

**F1 侧公开口径（互相打架，仅数量级）**：
- 整套动力单元（ICE+MGU-K+MGU-H+电池+电控）客户采购价 **$10-15M**（grandprix247，含研发摊销）；另一口径 $20M 整车中动力单元约占 1/3（Motor Sport Magazine 引 Pat Symonds）；FIA 主席 Ben Sulayem 说单台发动机约 **€150 万**、研发超 **€2 亿/年**
- **MGU-K 单件无公开定价**；F1 MGU-K 规格：旧规 120kW / 50,000rpm，2026 新规 350kW（Honda 官方 + raceteq）

**SPX177 侧**：无公开报价。制造定位推断 = 定制 + 小批量 + F1/FE 级工艺 → **六位数美元量级（纯推断，非可追溯数字）**。

**对比结论**：
- 低于 F1 **整套 PU**（$10M+）——废话，那含 ICE+电池+研发摊销
- 相对 **MGU-K 单件**无显著优势——同为定制赛车件，量级同级
- 不便宜的原因：工艺 F1/FE 级、小批量无规模效应、12 人团队 2 年研发全摊销、螺旋槽/双管套合/旋转接头全是精加工
- **Helix 商业逻辑**：SPX177 是 X-Division 立标杆的技术样板，量产便宜货走 SCT（Scalable Core Technology）平台——官方口径 SCT "easily manufactured in large production runs"

## 四、对完美电驱架构的启示（电机选型口径）

1. **持续/峰值比是比峰值密度更重要的选型指标**——SPX177 的 91% vs YASA 75% vs 一般径向 50%。对应电驱越野 >350km 纯沙漠断崖掉速问题的电机侧解法方向：**持续能力靠冷却，不靠峰值标称**。
2. **MGU05 对标的口径修正**：MGU05（F1/FE 级，~30kW/kg 级峰值密度、赛事寿命）是"峰值机器+极端轻量化"逻辑；SPX177 证明**径向磁通 + 强化冷却也能到 F1 级持续功率密度**——但成本仍是 F1/FE 级（六位数美元），**未破"零件墙"**（CONTEXT 状态声明中的零件墙=MGU 民用买不起，SPX177 佐证而非推翻）。
3. **可量产持续路线参考 Lucid 微喷射定子冷却**（16.4 kW/kg 峰值 + 可规模化工艺），不是 Helix 的螺旋转子——P1 190kW 持续的民用方案可行性调研应优先看 Lucid 这类"可量产工艺做强化冷却"的路子。
4. **口径纪律**：SPX177 视频宣称"950hp"是峰值（台架 >700kW 未拉满），持续 650kW 才是规格；且官方自认"当前电池难以维持 650kW 持续输出"——**电机能力 ≠ 整车能力**，装车后实际持续上限由电池放电和整车散热共同决定。

## 五、来源

- Helix 官网 case study：https://www.ehelix.com/x-division/case-study-spx177-1/
- E-Mobility Engineering：https://www.emobility-engineering.com/helix-develops-650kw-continuous-output-low-inductance-motor/
- Automotive Powertrain Technology International：https://www.automotivepowertraintechnologyinternational.com/news/electric-motors/helix-produces-electric-motor-with-650kw-of-continuous-power-for-unnamed-hypercar.html
- Lucid 微喷射冷却（greencarreports）：https://www.greencarreports.com/news/1137141_lucid-motors-more-power-dense-easier-to-build-than-tesla
- YASA 油冷对比（官网）：https://yasa.com/technology/
- Tesla Plaid 液冷+碳纤转子（车主手册）：https://www.tesla.com/ownersmanual/models/en_tw/GUID-E414862C-CFA1-4A0B-9548-BE21C32CAA58.html
- F1 动力单元成本：https://www.grandprix247.com/formula-1-news/the-most-expensive-engines-in-formula-1-history-how-much-do-f1-power-units-really-cost
- F1 MGU-K 规格（Honda 官方）：https://global.honda/en/tech/motorsports/Formula-1/Powertrain_MGU-H_MGU-K/
- F1 2026 MGU-K 350kW：https://www.raceteq.com/articles/2026/05/f1s-2026-energy-system-explained

## 六、口径备注（存疑项）

- 官网 case study 规格表另有 "Power continuous 398kW" 一组数字（research 工具抓取摘要所见，正文与两家媒体均为 650kW 持续）——**398 语义不明，存疑不引用**，主口径 650kW
- Whisper 识别错误：视频中 "McMurtry Spéirling" 被听成 "MOOC Mercury Spearling"（Helix 前身 Integral Powertrain 历史装机：Aston Martin Valkyrie + McMurtry Spéirling）
- YASA 新样机 750kW/12.7kg=59kW/kg（IEEE Spectrum，2025-10）为**实验室样机**口径，非交付产品，与 SPX177 不构成同级对比
