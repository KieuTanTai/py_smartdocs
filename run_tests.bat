@echo off
cd /d D:\DAPYT\py_smartdocs
call venv311\Scripts\activate.bat
python -c "exec(open('tests/comprehensive_test.py').read())"
