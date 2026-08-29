$ErrorActionPreference = 'Stop'
$cookies = Get-Content "D:\Project\dsh_rally_cars\_tmp_s1_cookies.txt" | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }
$cookieStr = ($cookies | ForEach-Object { $f = $_ -split "`t"; "$($f[5])=$($f[6])" }) -join '; '
$h = @{
    'Cookie'    = $cookieStr
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    'Referer'   = 'https://stage1st.com/2b/forum.php?mod=viewthread&tid=2288635&page=1'
}

function Get-Page([int]$page, [string]$outHtml, [string]$outTxt) {
    $url = "https://stage1st.com/2b/thread-2288635-$page-1.html"
    $r = Invoke-WebRequest -Uri $url -Headers $h -TimeoutSec 30 -UseBasicParsing
    [System.IO.File]::WriteAllText($outHtml, $r.Content, [System.Text.Encoding]::UTF8)
    powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Project\dsh_rally_cars\_tmp_s1_parse_bom.ps1" -HtmlFile $outHtml -OutFile $outTxt
    "PAGE $page OK HTTP $($r.StatusCode) size=$($r.RawContentLength)"
}

foreach ($p in 2..6) {
    Get-Page $p "D:\Project\dsh_rally_cars\_tmp_s1_thread2288635_p$p.html" "D:\Project\dsh_rally_cars\_tmp_s1_p$p.txt"
    if ($p -lt 6) {
        "sleeping 15s before page $($p+1)..."
        Start-Sleep -Seconds 15
    }
}
"ALL DONE"
