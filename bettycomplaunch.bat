@echo off
title Betty Companion - Active Status
color 0B
echo =======================================
echo   Launching Betty Companion...
echo =======================================
echo.

:: Run the Python script
python betty_companion.py

:: If the script crashes or fails to start, pause so you can read the error
if %errorlevel% neq 0 (
    echo.
    echo [!] A critical error occurred. The script has stopped.
    pause
)