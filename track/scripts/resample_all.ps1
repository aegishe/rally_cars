# 重采一键管道: 抽帧 -> OCR -> (清洗/分析由 Python 完成)
# 用法: pwsh -File track\scripts\resample_all.ps1
# 配置: track\scripts\resample_config.json
# 依赖: ffmpeg (PATH), batch-ocr skill, 无 token 消耗 (纯本机)
param(
  [string]$Config = "D:\Project\dsh_rally_cars\track\scripts\resample_config.json"
)

$ErrorActionPreference = "Stop"
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg) { $ffmpeg = "C:\Program Files\ffmpeg\bin\ffmpeg.exe" }
$div = [int]$cfg.fps_div
$vfps = [int]$cfg.video_fps

foreach ($seg in $cfg.segments) {
  $car = $seg.car
  $name = "$($car)_$($seg.name)"
  $video = $cfg.videos.$car
  $regions = $cfg.regions.$car
  $dir = Join-Path $cfg.out_base $name
  New-Item -ItemType Directory -Force -Path $dir | Out-Null

  # ---- Step 1: 抽帧 (帧号口径, 规避 VFR/PTS 漂移) ----
  & $ffmpeg -hide_banner -loglevel error -y -i $video `
    -vf "trim=start_frame=$($seg.frame_start):end_frame=$($seg.frame_end),select='not(mod(n,$div))',setpts=N/($vfps*TB)" `
    -vsync 0 -q:v 2 (Join-Path $dir "f_%04d.jpg")
  $nFrames = (Get-ChildItem $dir -Filter *.jpg).Count
  $expect = [math]::Ceiling(($seg.frame_end - $seg.frame_start) / $div)
  if ($nFrames -ne $expect) {
    Write-Warning "$name : 抽帧 $nFrames 帧 (预期 $expect) —— 检查视频帧数/trim 边界"
  }

  # ---- Step 2: OCR ----
  $outTxt = Join-Path $cfg.out_base "$name.txt"
  powershell -ExecutionPolicy Bypass -File $cfg.batch_ocr_script `
    -Dir $dir -Regions $regions -Out $outTxt -Label -Scale $cfg.ocr_scale -Pattern "*.jpg" | Out-Null
  Write-Output "$name : $nFrames 帧, OCR 完成 -> $outTxt"
}

Write-Output ""
Write-Output "全部区段完成。下一步 (清洗+校准+输出 CSV):"
Write-Output "  py -3.14 track\scripts\resample_clean.py"
