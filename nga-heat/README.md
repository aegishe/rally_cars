# NGA 车版热度监测

每小时抓一次 NGA 车版（`fid=-343809`）主题列表，统计回帖数等热度指标，追加一行到 CSV。
游客态访问（guestJs），无需登录、无账号风险。数据随 rally_cars 仓库双机 git 同步。

## 文件

| 文件 | 作用 |
|---|---|
| `nga_fid_heat.py` | 扫描脚本：抓前 N 页主题，算指标，追加 CSV |
| `run_heat.ps1` | 定时入口：pull → 扫描 → commit → push（双机同步） |
| `run_heat.bat` | 计划任务包装（重定向日志） |
| `data/nga_fid-343809_heat.csv` | 数据（每小时一行，`machine` 列区分两台机器） |
| `run_heat.log` | 运行日志（本地，已 gitignore） |

## CSV 指标含义

| 列 | 含义 |
|---|---|
| `ts` / `machine` | 扫描时间 / 机器名 |
| `total_threads` | 版面总主题数 |
| `scanned` | 本次实际抓到的主题数 |
| `replies_sum` / `replies_avg` / `replies_max` | 抓取主题的回帖总和 / 平均 / 最大 |
| `new_1h` | 最近 1 小时新发主题数 |
| `active_5m` / `active_1h` | 最近 5 分钟 / 1 小时内有新回帖的主题数 |
| `lastpost_ts` | 抓取范围内最新最后回复时间（unix 秒） |

热度趋势看 `replies_sum`、`active_5m`、`new_1h` 随时间的变化即可。

## 依赖

- Python 3 + `requests`（`pip install requests`）
- git，且 `GITHUB_TOKEN_PROJ` 用户级环境变量已配置（推 rally_cars 仓库用）

## 部署（家里电脑接续）

1. 家里机 rally_cars 仓库已随 dsh-sync 同步，`nga-heat/` 目录会自动出现（或 `git pull` 拉取）。
2. 确认 git 身份为 `AegisH`、`GITHUB_TOKEN_PROJ` 已配、`python` 在 PATH。
3. 注册同名计划任务（路径按家里实际仓库路径）：

```bat
schtasks /create /tn "NGA-Heat-Scan" /tr "D:\Project\dsh_rally_cars\nga-heat\run_heat.bat" /sc HOURLY /mo 1 /st 00:05 /f
```

4. 两台机器每小时各追加一行（`machine` 列不同），`run_heat.ps1` 先 pull 再 push，实现数据合并同步。

## 风险说明

- 游客态访问，不带任何登录 cookie，不涉及个人账号风控。
- 频率每小时 1 次（每次 2 页 = 约 3 个请求），远低于人工刷帖，遵守反爬纪律（页间隔 1.5–2.5s、不并行）。
- 脚本失败如实退出，不影响仓库其他内容。

## 手动跑一次

```bat
python nga_fid_heat.py --fid -343809 --pages 2 --force
```

`--force` 忽略"本机本小时已有记录"去重，便于补录或测试。
