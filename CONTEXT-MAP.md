# rally_cars 上下文地图

本项目包含五个独立的分析上下文，共享部分工程方法论（多元对数回归、场景约束分析），各自术语和领域独立。

## 全景速查

| 上下文 | 路径 | 核心术语 | 一句话结论 | CONTEXT | ADR |
|------|------|------|------|:---:|:---:|
| **越野体系** | `offroad/` | 9场景 / SOC三状态 / 保电瓶颈 | P2并联+机械四驱=极限越野最优解 | [→](offroad/CONTEXT.md) | ✓ |
| **赛道体系** | `track/` | 功重比 / 重量惩罚比 / 残差 | 纯电落后100%来自车重，不来自电驱技术 | [→](track/CONTEXT.md) | — |
| **派克峰体系** | `pikes-peak/` | 净功重比 / 空力稀薄化 / 爬坡功率税 | 高海拔纯电免疫，车重被双重惩罚 | [→](pikes-peak/CONTEXT.md) | — |
| **家用体系** | `daily-touring/` | 续航三角 / 焦虑谱系 / 亏电衰减 | 亏电后机械直驱有无=焦虑唯一分割线 | [→](daily-touring/CONTEXT.md) | — |
| **完美电驱越野** | `perfect-e-offroad/` | 纯增程电四驱 / MGU05 / 分层限滑 | 亏电下限由P1持续发电功率决定 | [→](perfect-e-offroad/CONTEXT.md) | ✓ |

## 各上下文文件索引

### 越野体系 (`offroad/`)

| 文件 | 内容 |
|------|------|
| `offroad/CONTEXT.md` | 领域术语 / SOC 三状态 / 架构×速度域矩阵 / 7 一级指标 |
| `offroad/docs/越野车场景打分标准-核心结论.md` | 9 场景 × 架构适配矩阵 + 打分表格 |
| `offroad/docs/2026环塔拉力赛T2量产组 核心发现与技术总结.md` | 6 平台 + 4 赛段 + 电驱越野物理边界 |
| `offroad/docs/坦克700 环塔赛车改装清单.md` | Hi4-T P2 改装实战 |
| `offroad/docs/卫士OCTA达喀尔赛车：改装与性能总结.md` | 达喀尔冠军方案 |
| `offroad/docs/adr/` | 4 个架构决策（场景一维化、竞技强化等） |
| `offroad/docs/context-detail/柴油混动-架构适配性分析.md` | 柴油混动在越野场景的架构适配性 |
| `offroad/docs/context-detail/悬架技术全景-从巴哈到达喀尔到F1.md` | 被动位敏/模式解耦/液压互联/主动悬架全谱系对比 + 三条线框架 |
| `offroad/环塔2026_总成绩.csv` | 42 车 × 12 赛段用时（Excel 转换，含罚时字段） |
| `offroad/环塔2026_赛段成绩.csv` | 374 行赛段明细 |

### 赛道体系 (`track/`)

| 文件 | 内容 |
|------|------|
| `track/CONTEXT.md` | 车体类型 / 功重比弹性 / 重量惩罚比 / 残差 |
| `track/docs/赛道场景性能分析-核心结论.md` | 全量+分组回归 / 最优组合矩阵 |
| `track/charts/ring_analysis.html` | 交互式可视化（4 图表） |
| `track/scripts/` | Python 回归 + 图表生成 |

### 派克峰体系 (`pikes-peak/`)

| 文件 | 内容 |
|------|------|
| `pikes-peak/CONTEXT.md` | 空力等级 / 净功重比 / 爬坡功率税 / 高原衰减 |
| `pikes-peak/docs/派克峰性能分析-核心结论.md` | 全量回归 / 空力×海拔交互 |
| `pikes-peak/charts/pikes_peak_analysis.html` | 交互式可视化 |
| `pikes-peak/scripts/` | Python 回归 + 图表生成 |

### 家用体系 (`daily-touring/`)

| 文件 | 内容 |
|------|------|
| `daily-touring/CONTEXT.md` | 续航三角 / 焦虑谱系 / 14 维度 / 亏电体验衰减 |
| `daily-touring/docs/` | 车型决赛圈对比（SUV/轿车/硬派SUV 等 10+ 篇） |
| `daily-touring/charts/` | 雷达图等可视化 |

### 完美电驱越野 (`perfect-e-offroad/`)

| 文件 | 内容 |
|------|------|
| `perfect-e-offroad/CONTEXT.md` | 三版本架构 / MGU05 对标 / 三电机合计 102kg |
| `perfect-e-offroad/docs/adr/` | 架构决策（纯增程路线选择等） |

## 根目录文件

- `AGENTS.md`：全局规则 + 五体系骨架摘要（审查窗口可见）
- `CONTEXT-MAP.md`：本文件 — 完整上下文索引
- `PUBLISH-PLAN.md`：发布大纲（两线一附录：研究内核 4 篇 + 应用延伸 2 篇 + 术语附录；NGA/虎扑同文双发策略）
- `publish/`：**定稿文章产出**（与研究资产分离）——篇1《3400 公里之后，谁还在？》（越野）、篇2《2977 马力的真相》（纽北）；`publish/assets/` 配图 PNG、`publish/scripts/` 可复现图脚本
