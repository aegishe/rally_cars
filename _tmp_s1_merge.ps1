$ErrorActionPreference = 'Stop'
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("===== S1 THREAD 2288635 | BBA正在坠入一场罕见大萧条 | 归墟(2b) =====")
[void]$sb.AppendLine("===== URL: https://stage1st.com/2b/thread-2288635-1-1.html =====")
[void]$sb.AppendLine('')
foreach ($p in 1..6) {
    $f = "D:\Project\dsh_rally_cars\_tmp_s1_p$p.txt"
    if (-not (Test-Path $f)) { "MISSING $f"; continue }
    $lines = Get-Content $f -Encoding UTF8
    [void]$sb.AppendLine("########## PAGE $p ##########")
    foreach ($l in $lines) { [void]$sb.AppendLine($l) }
    [void]$sb.AppendLine('')
}
$out = "D:\Project\dsh_rally_cars\s1_thread2288635_全楼.txt"
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.UTF8Encoding]::new($true))
"WROTE $out chars=$($sb.Length)"
