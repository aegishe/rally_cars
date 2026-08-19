# 全圈 16 段 OCR 批量 (后台跑, 进度写日志)
$skill = 'C:\Users\Administrator\.agents\skills\batch-ocr\batch_ocr.ps1'
$base = 'G:\Capture\youtube\resample'
$regU = "$base\regions_u9x.json"
$regS = "$base\regions_su7.json"
$log = "$base\ocr_progress.log"
if (Test-Path $log) { Remove-Item $log -Force }

$segs = @(
  @('u9x_lap1',$regU), @('u9x_lap2',$regU), @('u9x_lap3',$regU), @('u9x_lap4',$regU),
  @('u9x_lap5',$regU), @('u9x_lap6',$regU), @('u9x_lap7',$regU), @('u9x_lap8',$regU),
  @('su7_lap1',$regS), @('su7_lap2',$regS), @('su7_lap3',$regS), @('su7_lap4',$regS),
  @('su7_lap5',$regS), @('su7_lap6',$regS), @('su7_lap7',$regS), @('su7_lap8',$regS)
)
foreach ($s in $segs) {
  $dir = Join-Path $base $s[0]
  $out = Join-Path $base ($s[0] + '.txt')
  powershell -ExecutionPolicy Bypass -File $skill -Dir $dir -Regions $s[1] -Out $out -Label -Scale 5 -Pattern "*.jpg" | Out-Null
  Add-Content -Path $log -Value "$($s[0]) done $(Get-Date -Format 'HH:mm:ss')" -Encoding ASCII
}
Add-Content -Path $log -Value "ALL OCR DONE $(Get-Date -Format 'HH:mm:ss')" -Encoding ASCII
