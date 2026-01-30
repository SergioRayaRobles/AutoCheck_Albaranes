@echo off
cd /d "%~dp0"

REM Logging setup
set LOGFILE=launcher.log
echo [%DATE% %TIME%] Starting execution >> %LOGFILE%

REM 1. Check for Virtual Environment
if exist "venv\Scripts\activate.bat" (
    echo [%DATE% %TIME%] Activating VENV >> %LOGFILE%
    call venv\Scripts\activate.bat
    set PYTHON_CMD=python
    goto :RUN
)

REM 2. Check for System Python
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [%DATE% %TIME%] Using system 'python' >> %LOGFILE%
    set PYTHON_CMD=python
    goto :RUN
)

REM 3. Check for Py Launcher
py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [%DATE% %TIME%] Using 'py' launcher >> %LOGFILE%
    set PYTHON_CMD=py
    goto :RUN
)

REM 4. FAILURE
echo [%DATE% %TIME%] CRITICAL ERROR: Python is not installed or not in PATH. >> %LOGFILE%
echo ---------------------------------------------------
echo CRITICAL ERROR: Python is not installed on this system.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo ---------------------------------------------------
exit /b 1

:RUN
REM Run the script
%PYTHON_CMD% main.py >> %LOGFILE% 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Unknown failure. Exit code %ERRORLEVEL% >> %LOGFILE%
    exit /b %ERRORLEVEL%
) else (
    echo [%DATE% %TIME%] Success >> %LOGFILE%
    exit /b 0
)
