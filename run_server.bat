@echo off
REM Set UTF-8 encoding for Python on Windows
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run Django server
python manage.py runserver
