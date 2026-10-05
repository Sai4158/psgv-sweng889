@echo off
setlocal
set "projectPython=%~dp0.venv\Scripts\python.exe"
if not exist "%projectPython%" (
    echo Create .venv with Python 3.11+ and install requirements.txt first. See README.md.
    exit /b 1
)
"%projectPython%" "%~dp0launch.py" %*
exit /b %errorlevel%
