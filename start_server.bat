@echo off
echo Starting CoaiHome AI Dropshipping System...
cd /d "%~dp0"
call venv\Scripts\activate
set PYTHONDONTWRITEBYTECODE=1
python main.py
pause
