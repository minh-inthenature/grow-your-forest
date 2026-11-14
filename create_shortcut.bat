@echo off
cd /d "%~dp0"

set "APP_DIR=%~dp0"
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"

if exist "%APP_DIR%\GrowYourForest.exe" (
    set "TARGET=%APP_DIR%\GrowYourForest.exe"
) else (
    set "TARGET=%APP_DIR%\run.bat"
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desktop = [Environment]::GetFolderPath('Desktop');" ^
  "$lnk = Join-Path $desktop 'Grow Your Forest.lnk';" ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$sc = $ws.CreateShortcut($lnk);" ^
  "$sc.TargetPath = '%TARGET%';" ^
  "$sc.WorkingDirectory = '%APP_DIR%';" ^
  "if (Test-Path '%APP_DIR%\forest.ico') { $sc.IconLocation = '%APP_DIR%\forest.ico' };" ^
  "$sc.Description = 'Grow Your Forest - Cozy Focus Timer';" ^
  "$sc.Save();" ^
  "Write-Host ('Created Desktop shortcut: ' + $lnk)"

if %ERRORLEVEL% NEQ 0 (
    echo Failed to create Desktop shortcut.
    pause
    exit /b 1
)

pause
