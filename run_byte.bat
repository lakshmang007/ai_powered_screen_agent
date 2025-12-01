@echo off
REM Byte Smart Launcher
REM This script runs Byte Smart using Windows Python (not MSYS2)

echo.
echo ========================================
echo    Starting Byte Smart...
echo ========================================
echo.

C:\Python313\python.exe "%~dp0byte_smart.py"

echo.
echo ========================================
echo    Byte Smart has stopped
echo ========================================
echo.
pause

