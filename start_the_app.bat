@echo off
chcp 65001 > nul
echo ========================================================
echo  🚀 Khởi động AURA — App Lập trình bằng THẺ (bản v1)
echo ========================================================
echo.
pushd "%~dp0"
"%~dp0venv\Scripts\python.exe" -m interface.the_app --port 8088
popd
pause
