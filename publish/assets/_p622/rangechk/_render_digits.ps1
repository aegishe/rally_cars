param([string]$Img, [string]$Label)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap($Img)
$chars = ' .:-=+*#%@'
$regions = @(
  @{ n = 'd1'; x = 180; w = 96 },
  @{ n = 'd2'; x = 345; w = 152 },
  @{ n = 'd3'; x = 560; w = 90 }
)
foreach ($r in $regions) {
  Write-Output "==== $Label $($r.n) (x $($r.x)-$($r.x + $r.w), y 230-380) ===="
  for ($jy = 0; $jy -lt 38; $jy++) {
    $row = ''
    for ($jx = 0; $jx -lt [int]($r.w / 2); $jx++) {
      $c = $bmp.GetPixel($r.x + $jx * 2, 230 + $jy * 4)
      $lum = ($c.R + $c.G + $c.B) / 3
      $idx = [int](($lum / 255) * ($chars.Length - 1))
      $row += $chars[$idx]
    }
    Write-Output $row
  }
}
$bmp.Dispose()
