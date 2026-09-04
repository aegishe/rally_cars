# run_heat.ps1 -- hourly NGA board heat scan (append CSV only, no git ops)
# Logged output goes to run_heat.log next to this script.
$ErrorActionPreference = 'Continue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Join-Path $ScriptDir 'nga_fid_heat.py'
$Log = Join-Path $ScriptDir 'run_heat.log'

& python $Py --fid '-343809' --pages 2 2>&1 | ForEach-Object { $_.ToString() } | Out-File -FilePath $Log -Append -Encoding utf8
