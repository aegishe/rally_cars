# run_heat.ps1 -- hourly NGA board heat scan (append CSV only, no git ops)
# python runs via Start-Process -WindowStyle Hidden so NO console window pops.
# Output is redirected to temp files then merged into run_heat.log.
$ErrorActionPreference = 'Continue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Join-Path $ScriptDir 'nga_fid_heat.py'
$Log = Join-Path $ScriptDir 'run_heat.log'
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

try {
    $tmp = Join-Path $env:TEMP ('nga_heat_' + [guid]::NewGuid().ToString('N'))
    $p = Start-Process -FilePath 'python' `
        -ArgumentList @($Py, '--fid', '-343809', '--pages', '2') `
        -WindowStyle Hidden -Wait -PassThru `
        -RedirectStandardOutput ($tmp + '.out') `
        -RedirectStandardError ($tmp + '.err')
    foreach ($suffix in '.out', '.err') {
        $f = $tmp + $suffix
        if (Test-Path $f) {
            Get-Content $f -Encoding UTF8 | Out-File -FilePath $Log -Append -Encoding utf8
            Remove-Item $f -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
    Add-Content -Path $Log -Value ("{0} [error] {1}" -f $Stamp, $_.Exception.Message) -Encoding utf8
}
