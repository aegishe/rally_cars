# run_heat.ps1 -- hourly NGA board heat scan + dual-machine git sync
# Flow: flush pending -> pull --rebase -> python scan -> commit -> push

$ErrorActionPreference = 'Continue'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path   # ...\nga-heat
$Repo      = Split-Path -Parent $ScriptDir                     # ...\dsh_rally_cars
$Py        = Join-Path $ScriptDir 'nga_fid_heat.py'
$Branch    = 'master'
$Fid       = '-343809'
$Pages     = 2

function Line { Write-Output ("== [{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $args[0]) }
function Run-Git($cmd) {
    & cmd /c "git -C `"$Repo`" $cmd 2>&1" | ForEach-Object { $_.ToString() } | Write-Output
}

Line "start machine=$env:COMPUTERNAME"

$tok = [System.Environment]::GetEnvironmentVariable('GITHUB_TOKEN_PROJ', 'User')
$url = "https://x-access-token:$tok@github.com/aegishe/rally_cars.git"

# 0. flush pending changes (from a previous failed run) so rebase starts clean
$pre = git -C $Repo status --porcelain -- nga-heat 2>$null
if ($pre) {
    git -C $Repo add nga-heat 2>&1 | Out-Null
    git -C $Repo commit -m "nga-heat: flush pending @ $env:COMPUTERNAME" 2>&1 | Out-Null
    Line "flushed pending changes"
}

# 1. pull remote (bidirectional sync)
if ($tok) {
    Run-Git "pull --rebase `"$url`" $Branch"
    Line "pull --rebase done"
} else {
    Line "warning: GITHUB_TOKEN_PROJ not found, skip pull (local record still works)"
}

# 2. scan and append CSV
$pyout = & python $Py --fid $Fid --pages $Pages 2>&1
$pyout | ForEach-Object { $_.ToString() } | Write-Output

# 3. commit + push
$dirty = git -C $Repo status --porcelain -- nga-heat 2>$null
if ($dirty) {
    git -C $Repo add nga-heat 2>&1 | Out-Null
    git -C $Repo commit -m "nga-heat: hourly $(Get-Date -Format 'yyyy-MM-dd HH:mm') @ $env:COMPUTERNAME" 2>&1 | Out-Null
    if ($tok) {
        Run-Git "push `"$url`" HEAD:$Branch"
        Line "push done"
    } else {
        Line "no token, committed locally only"
    }
} else {
    Line "no new data (this machine already recorded this hour), skip commit"
}

Line "end"
