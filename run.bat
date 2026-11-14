@echo off
cd /d "%~dp0"

if exist "C:\msys64\ucrt64\bin\pythonw.exe" (
    start "" "C:\msys64\ucrt64\bin\pythonw.exe" "%~dp0app.py"
    exit /b 0
)

where pyw >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" pyw "%~dp0app.py"
    exit /b 0
)

where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" pythonw "%~dp0app.py"
    exit /b 0
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" python "%~dp0app.py"
    exit /b 0
)

echo Python 3 with Tkinter was not found on this computer.
echo Please install Python 3 from https://www.python.org/downloads/ (check "Add Python to PATH"),
echo or download the standalone GrowYourForest.exe from the GitHub Releases page.
pause
exit /b 1
