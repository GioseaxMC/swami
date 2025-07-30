@echo off

setlocal

set PYTHON_SCRIPT=%~dp0/src/swami.py
python %PYTHON_SCRIPT% %*

endlocal

