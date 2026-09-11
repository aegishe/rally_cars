# fix_heat_schedule.ps1 -- rebuild NGA-Heat-Scan with 24 FIXED daily triggers (HH:05)
#
# Why: the old task used "One Time Only, Hourly" repetition, which is a RELATIVE
# interval. When the machine slept/missed a fire, Windows re-based the next run on
# the delayed start, so sampling drifted (observed: company box -> :43, home box -> :26).
# Daily triggers at absolute HH:05 never drift.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File fix_heat_schedule.ps1
# Safe to re-run (overwrites the task).

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $ScriptDir 'run_heat.ps1'
$TaskName = 'NGA-Heat-Scan'

if (-not (Test-Path $Target)) { throw "not found: $Target" }

$me = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$sid = $me.User.Value
$user = $me.Name

# first trigger day: tomorrow (avoids a burst of catch-up runs for today's past slots)
$startDay = (Get-Date).Date.AddDays(1).ToString('yyyy-MM-dd')

$triggers = ''
foreach ($h in 0..23) {
    $hh = '{0:D2}' -f $h
    $triggers += "    <CalendarTrigger>`r`n      <StartBoundary>${startDay}T${hh}:05:00</StartBoundary>`r`n      <Enabled>true</Enabled>`r`n      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>`r`n    </CalendarTrigger>`r`n"
}

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Author>$user</Author>
    <Description>NGA board heat scan - 24 fixed daily triggers at HH:05</Description>
  </RegistrationInfo>
  <Triggers>
$triggers  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$sid</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File $Target</Arguments>
    </Exec>
  </Actions>
</Task>
"@

$tmp = Join-Path $env:TEMP ('nga_heat_task_' + [guid]::NewGuid().ToString('N') + '.xml')
try {
    $xml | Out-File -FilePath $tmp -Encoding Unicode
    schtasks /create /tn $TaskName /xml $tmp /f | Write-Output
    if ($LASTEXITCODE -ne 0) { throw "schtasks /create failed (exit $LASTEXITCODE)" }
} finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

schtasks /query /tn $TaskName /v /fo LIST | Select-String -Pattern 'Task To Run|Next Run Time|Status|Scheduled Task State' | Write-Output
$triggerCount = (schtasks /query /tn $TaskName /xml | Select-String -Pattern '<CalendarTrigger>' -AllMatches).Matches.Count
Write-Output "triggers installed: $triggerCount (expect 24)"
