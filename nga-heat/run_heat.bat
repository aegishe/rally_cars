@echo off
rem NGA heat hourly scan - append CSV only (git sync handled by dsh-sync daily)
python "%~dp0nga_fid_heat.py" --fid -343809 --pages 2 >> "%~dp0run_heat.log" 2>&1
