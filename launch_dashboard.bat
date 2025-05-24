@echo off
rem Universal launcher for Hardware Timing Dashboard
rem This is a simple wrapper that calls the Python script

rem Navigate to the directory containing this script
cd /d "%~dp0"

rem Execute the Python launcher
python dashboard.py
pause
