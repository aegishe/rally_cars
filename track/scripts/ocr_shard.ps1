# 全圈 OCR 分片并行版
# 用法: powershell.exe -File ocr_shard.ps1 -Idx 0 -Total 8
# 每进程只处理 (段序号 % Total == Idx) 的段; 日志独立写文件, 无竞争
param([int]$Idx = 0, [int]$Total = 1)

$skill = 'C:\Users\Administrator\.agents\skills\batch-ocr\batch_ocr.ps1'
$base = 'G:\Capture\youtube\resample'
$regU = "$base\regions_u9x.json"
$regS = "$base\regions_su7.json"
$log = "$base\ocr_progress_$Idx.log"
if (Test-Path $log) { Remove-Item $log -Force }

$segs = @(
  @('u9x_lap1',$regU), @('u9x_lap2',$regU), @('u9x_lap3',$regU), @('u9x_lap4',$regU),
  @('u9x_lap5',$regU), @('u9x_lap6',$regU), @('u9x_lap7',$regU), @('u9x_lap8',$regU),
  @('su7_lap1',$regS), @('su7_lap2',$regS), @('su7_lap3',$regS), @('su7_lap4',$regS),
  @('su7_lap5',$regS), @('su7_lap6',$regS), @('su7_lap7',$regS), @('su7_lap8',$regS)
)
for ($i = 0; $i -lt $segs.Count; $i++) {
  if ($i % $Total -ne $Idx) { continue }
  $s = $segs[$i]
  $dir = Join-Path $base $s[0]
  $out = Join-Path $base ($s[0] + '.txt')
  powershell -ExecutionPolicy Bypass -File $skill -Dir $dir -Regions $s[1] -Out $out -Label -Scale 5 -Pattern "*.jpg" | Out-Null
  Add-Content -Path $log -Value "$($s[0]) done $(Get-Date -Format 'HH:mm:ss')" -Encoding ASCII
}
Add-Content -Path $log -Value "SHARD $Idx DONE $(Get-Date -Format 'HH:mm:ss')" -Encoding ASCII
