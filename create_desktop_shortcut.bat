@echo off
title Create Desktop Shortcut for Family Finance Dashboard
cd /d "%~dp0"

echo ====================================================================
echo Creating Desktop Shortcut for Family Finance Dashboard
echo ====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut(\"$desktop\Family Finance Dashboard.lnk\"); $s.TargetPath = '%~dp0run_dashboard.bat'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll,13'; $s.Description = 'Launch Family Finance Dashboard & open in browser'; $s.Save(); Write-Host '[SUCCESS] Shortcut created on your Desktop!' -ForegroundColor Green"

echo.
echo ====================================================================
echo Done! You can now double-click the shortcut on your Desktop to launch
echo the dashboard and automatically open http://localhost:5050 in Chrome/Edge.
echo ====================================================================
pause
