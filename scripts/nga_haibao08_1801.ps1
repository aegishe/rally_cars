# 一次性定时任务：2026-09-21 18:01 抓取 NGA 海豹08电耗帖（tid=47501750）
# 由 Windows 计划任务 dsh_nga_haibao08_1801 调用
$ErrorActionPreference = 'Continue'

$ws     = 'D:\Project\dsh_rally_cars'
$logDir = Join-Path $ws '.tmp'
$outDir = Join-Path $ws 'knowledge\nga'
$log    = Join-Path $logDir 'nga_tid47501750_1801.log'
$out    = Join-Path $outDir 'nga_tid47501750_replies_1801.txt'
$py     = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe'
$scraper = 'C:\Users\Administrator\.agents\skills\nga-scraper\nga_scraper.py'

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

# 18:01 时点的读秒日志：便于事后确认任务确实准点启动
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')] trigger fired" | Out-File -FilePath $log -Append -Encoding utf8

# 子进程输出按 UTF-8 解码，避免 python(GBK) 与 Out-File(UTF-8) 混用导致日志乱码
# （2026-09-21 首次运行发现：日志中文乱码，内容可读但不宜留档）
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

& $py $scraper thread 47501750 -o $out *>> $log
$code = $LASTEXITCODE

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')] scraper exit=$code out=$out" | Out-File -FilePath $log -Append -Encoding utf8
