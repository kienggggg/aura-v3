@echo off
REM ============================================================
REM  start_aura_app.bat - Mo AURA v3 nhu mot ung dung may tinh
REM
REM  Ban cu tro vao localhost:8765/chat.html: 8765 la cong cua
REM  daemon v2, va v3 phuc vu man hinh chat o "/" chu khong co
REM  duong /chat.html -> bam vao la ra 404.
REM
REM  Moi viec that su nam trong aura_app.pyw: no CHO server tra
REM  loi that su roi moi mo cua so, thay vi ngu dai 1 giay.
REM ============================================================

cd /d "%~dp0"

set "PYW=venv\Scripts\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"

start "" "%PYW%" aura_app.pyw
exit /b 0
