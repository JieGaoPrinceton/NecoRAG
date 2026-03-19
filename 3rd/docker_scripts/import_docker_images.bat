@echo off
REM NecoRAG Docker Image Import Tool Launcher
REM This script bypasses PowerShell execution policy restrictions

echo ============================================================
echo   NecoRAG Docker Image Import Tool
echo ============================================================
echo.

REM Use -ExecutionPolicy Bypass to bypass execution policy
PowerShell -ExecutionPolicy Bypass -File "%~dp0import_docker_images.ps1" %*

REM If PowerShell script returns error, pause to show error message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Script execution failed with error code: %ERRORLEVEL%
    pause
)
