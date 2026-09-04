@echo off
rem NGA heat hourly scan wrapper for Windows Task Scheduler
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_heat.ps1" >> "%~dp0run_heat.log" 2>&1
