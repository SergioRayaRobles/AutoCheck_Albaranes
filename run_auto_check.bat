@echo off
REM ====================================================
REM  Launcher for Auto Check Albaran
REM ====================================================

REM Navigate to the script directory
cd /d "%~dp0"

REM Activate Virtual Environment (if it exists)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

REM Run the Python Script and log output
echo [%DATE% %TIME%] Starting execution >> launcher.log
python main.py >> launcher.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Exit code %ERRORLEVEL% >> launcher.log
) else (
    echo [%DATE% %TIME%] Success >> launcher.log
)
