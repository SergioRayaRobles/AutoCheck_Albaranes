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

REM Run the Python Script
python main.py

REM Optional: Pause only if error occurred
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: The script encountered an error.
    pause
)
