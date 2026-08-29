param(
    [string]$HtmlFile,
    [string]$OutFile
)
$ErrorActionPreference = 'Stop'
$c = [System.IO.File]::ReadAllText($HtmlFile, [System.Text.Encoding]::UTF8)

# 拆出每个楼层块：<div id="post_XXXXX" ...> ... </div>
$postBlocks = [regex]::Matches($c, '<div id="post_(\d+)".*?(?=<div id="post_|</div>\s*</div>\s*</div>\s*<div id="hd">|<div id="f_pst"|$)', 'Singleline')

$sb = New-Object System.Text.StringBuilder
foreach ($blk in $postBlocks) {
    $blockHtml = $blk.Groups[0].Value
    $postId = $blk.Groups[1].Value

    # 作者
    $author = ''
    $am = [regex]::Match($blockHtml, 'class="authi">\s*<a[^>]*>([^<]+)</a>', 'Singleline')
    if (-not $am.Success) { $am = [regex]::Match($blockHtml, '<a[^>]*class="xw1"[^>]*>([^<]+)</a>') }
    if ($am.Success) { $author = $am.Groups[1].Value.Trim() }

    # 楼层号：楼主帖显示"楼主"，普通楼层 <em>3</em><sup>#</sup>
    $floor = ''
    if ($blockHtml -match 'postnum\d+"[^>]*>[\s\S]*?楼主') { $floor = '1' }
    if ($floor -eq '') {
        $fm = [regex]::Match($blockHtml, '<em>(\d+)</em><sup>#</sup>')
        if ($fm.Success) { $floor = $fm.Groups[1].Value }
    }

    # 时间
    $time = ''
    $tm = [regex]::Match($blockHtml, '发表于\s*([\d\-: ]+)')
    if ($tm.Success) { $time = $tm.Groups[1].Value.Trim() }

    # 正文：id="postmessage_XXXX" 的 td
    $body = ''
    $bm = [regex]::Match($blockHtml, 'id="postmessage_' + $postId + '"[^>]*>(.*?)</td>', 'Singleline')
    if (-not $bm.Success) { $bm = [regex]::Match($blockHtml, '<td class="t_f"[^>]*>(.*?)</td>', 'Singleline') }
    if ($bm.Success) {
        $body = $bm.Groups[1].Value
        # 去掉引用块前缀标记（保留文字）
        $body = [regex]::Replace($body, '<div class="quote">', "`n[QUOTE] ")
        $body = [regex]::Replace($body, '</div>', "`n")
        # 去 HTML 标签
        $body = [regex]::Replace($body, '<br\s*/?>', "`n")
        $body = [regex]::Replace($body, '<[^>]+>', '')
        $body = [System.Net.WebUtility]::HtmlDecode($body)
        # 压缩多余空行
        $body = [regex]::Replace($body, '[ \t]+\n', "`n")
        $body = [regex]::Replace($body, '\n{3,}', "`n`n")
        $body = $body.Trim()
    }

    if ($author -eq '' -and $body -eq '') { continue }
    [void]$sb.AppendLine("===== FLOOR $floor | $author | $time | pid=$postId =====")
    if ($body -ne '') { [void]$sb.AppendLine($body) }
    [void]$sb.AppendLine('')
}

[System.IO.File]::WriteAllText($OutFile, $sb.ToString(), [System.Text.Encoding]::UTF8)
"WROTE $OutFile chars=$($sb.Length)"
