Add-Type -AssemblyName System.Drawing

foreach ($n in @('s015','s016')) {
  $src = New-Object System.Drawing.Bitmap("D:\Project\dsh_rally_cars\publish\assets\_p622\rangechk\$n`_zoom.png")
  $x0 = 150; $y0 = 210; $W = 700; $H = 180
  $bw = New-Object 'System.Drawing.Bitmap'($W, $H, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $H; $y++) {
      $c = $src.GetPixel($x0 + $x, $y0 + $y)
      $lum = ($c.R + $c.G + $c.B) / 3
      if ($lum -ge 150) { $bw.SetPixel($x, $y, [System.Drawing.Color]::Black) }
      else { $bw.SetPixel($x, $y, [System.Drawing.Color]::White) }
    }
  }
  $fill = New-Object 'bool[,]' $W, $H
  $q = New-Object System.Collections.Generic.Queue[int]
  # seed flood from all border white pixels
  for ($x = 0; $x -lt $W; $x++) {
    foreach ($yy in @(0, $H - 1)) {
      $pix = $bw.GetPixel($x, $yy)
      if ($pix.R -eq 255 -and -not $fill[$x, $yy]) { $fill[$x, $yy] = $true; $q.Enqueue($yy * $W + $x) }
    }
  }
  for ($y = 0; $y -lt $H; $y++) {
    foreach ($xx in @(0, ($W - 1))) {
      $pix = $bw.GetPixel($xx, $y)
      if ($pix.R -eq 255 -and -not $fill[$xx, $y]) { $fill[$xx, $y] = $true; $q.Enqueue($y * $W + $xx) }
    }
  }
  while ($q.Count -gt 0) {
    $v = $q.Dequeue()
    $yy = [int][math]::Floor($v / $W); $xx = $v % $W
    foreach ($d in @(@(-1, 0), @(1, 0), @(0, -1), @(0, 1))) {
      $nx = $xx + $d[0]; $ny = $yy + $d[1]
      if ($nx -ge 0 -and $nx -lt $W -and $ny -ge 0 -and $ny -lt $H -and -not $fill[$nx, $ny]) {
        $pix = $bw.GetPixel($nx, $ny)
        if ($pix.R -eq 255) { $fill[$nx, $ny] = $true; $q.Enqueue($ny * $W + $nx) }
      }
    }
  }
  # any white pixel not reached by flood = enclosed hole -> fill black
  for ($x = 0; $x -lt $W; $x++) {
    for ($y = 0; $y -lt $H; $y++) {
      $pix = $bw.GetPixel($x, $y)
      if ($pix.R -eq 255 -and -not $fill[$x, $y]) { $bw.SetPixel($x, $y, [System.Drawing.Color]::Black) }
    }
  }
  $bw.Save("D:\Project\dsh_rally_cars\publish\assets\_p622\rangechk\_filled_$n`.png", [System.Drawing.Imaging.ImageFormat]::Png)
  $bw.Dispose(); $src.Dispose()
  Write-Output "filled $n"
}
