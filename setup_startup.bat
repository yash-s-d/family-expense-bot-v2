@echo off
title Setup Auto-Start for Family Finance Dashboard
cd /d "%~dp0"

echo ====================================================================
echo Setting up Family Finance Dashboard to run silently at Windows boot
echo ====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $startup = [Environment]::GetFolderPath('Startup'); $s = $ws.CreateShortcut(\"$startup\FamilyFinanceDashboard.lnk\"); $s.TargetPath = '%~dp0run_background.vbs'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Family Finance Neo-Fintech Dashboard (Silent Background Server)'; $s.Save(); Write-Host '[SUCCESS] Auto-start shortcut created in Windows Startup folder.' -ForegroundColor Green"

echo.
echo ====================================================================
echo Done! Whenever you open or restart your laptop, the dashboard
echo will run silently in the background. 
echo You can open http://localhost:5050 anytime!
echo ====================================================================
pause
