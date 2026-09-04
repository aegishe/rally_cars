# NGA 车版热度监测

每小时抓一次 NGA 车版（`fid=-343809`）主题列表，统计回帖数等热度指标，追加一行 CSV。
游客态访问（guestJs），无需登录、无账号风险。数据随 rally_cars 仓库双机 git 同步。

## 数据设计（为什么每机一个文件）

CSV 是**追加型文件**，两台机器各自往同一个文件追加、再靠 git 同步，合并时必然冲突
（与 dsh 会话 jsonl 双机追加冲突同理）。所以：

- 每台机器写自己的 `data/nga_fid-343809_heat_<机器名>.csv`，git 同步**永不冲突**。
- `merge.py` 把两台机器的文件合成一份 `..._heat_merged.csv`。
- 去重按**自然小时**（YYYY-MM-DD HH 相同视为重复）：扫描时若任意源文件已有本小时
  记录则跳过写入；merge 时同一小时的多条只保留第一条。两机同时在线、任务延迟、
  手动补跑产生的同小时重复都会被去掉，正常数据（天然间隔 1 小时）永不误删。

`merged.csv` 是本地合成产物，已 gitignore，不入库、不参与同步。

## 文件

| 文件 | 作用 |
|---|---|
| `nga_fid_heat.py` | 扫描脚本：抓前 N 页主题，算指标，追加本机 CSV，按自然小时去重 |
| `merge.py` | 合并各机 CSV → 单份 merged CSV（按 ts 排序 + 自然小时去重） |
| `run_heat.ps1` | 计划任务入口：隐藏窗口调用扫描脚本，只追加 CSV，**不做 git 操作** |
| `data/nga_fid-343809_heat_<机器名>.csv` | 各机数据（随 git 同步） |
| `data/nga_fid-343809_heat_merged.csv` | 合并去重产物（本地，gitignore） |
| `run_heat.log` | 运行日志（本地，gitignore，UTF-8） |

## CSV 指标含义

| 列 | 含义 |
|---|---|
| `ts` / `machine` | 采样时间 / 机器名 |
| `total_threads` | 版面总主题数 |
| `scanned` | 本次实际抓到的主题数 |
| `replies_sum` / `replies_avg` / `replies_max` | 回帖总和 / 平均 / 最大 |
| `top_tid` / `top_subject` | 当前第一热帖（回帖最多）的 tid / 标题；历史数据升级前的旧行这两列为空 |
| `new_1h` | 最近 1 小时新发主题数 |
| `active_5m` / `active_1h` | 最近 5 分钟 / 1 小时内有新回帖的主题数 |
| `lastpost_ts` | 最新最后回复时间（unix 秒） |

热度趋势看 `replies_sum`、`active_5m`、`new_1h` 随时间变化即可。

## 同步方式

计划任务每小时**只本地追加 CSV，不做任何 git 操作**（隐藏窗口运行，不弹黑窗）。
数据提交/推送交给既有的 dsh-sync（每日 23:00 自动）或手动同步，不污染仓库历史。

## 部署（家里电脑接续）

1. 家里机 rally_cars 仓库随 dsh-sync 同步后，`nga-heat/` 目录自动出现（或 `git pull` 拉取）。
2. 确认 python + `requests` 就绪（`pip install requests`）。
3. 注册同名计划任务（隐藏窗口，路径按家里实际仓库路径）：

```bat
schtasks /create /tn "NGA-Heat-Scan" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\Project\dsh_rally_cars\nga-heat\run_heat.ps1" /sc HOURLY /mo 1 /st 00:05 /f
```

4. 两机各自每小时采样一次（`machine` 列不同），数据文件随 dsh-sync 合并到两端；
   需要看整体趋势时跑一次 `python merge.py --fid -343809` 生成去重后的 merged CSV。

## 风险说明

- 游客态访问，不带任何登录 cookie，不涉及个人账号风控。
- 频率每小时 1 次（每次 2 页 ≈ 3 个请求），远低于人工刷帖，遵守反爬纪律（页间隔 1.5–2.5s、不并行）。
- 脚本失败如实退出，不影响仓库其他内容。

## 手动跑

```bat
python nga_fid_heat.py --fid -343809 --pages 2            rem 正常扫描（同小时已有记录则跳过）
python nga_fid_heat.py --fid -343809 --force              rem 忽略去重，强制补录一条
python merge.py --fid -343809                             rem 合并各机 CSV 并去重
```
