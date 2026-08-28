@echo off
chcp 65001 > nul
echo ========================================================
echo   🏛️  AURA COMMAND CENTER - APP DIEU HANH 7 DAC NHIEM v3
echo ========================================================
echo.
echo   ⚡ Dang khoi dong may chu noi bo tren cong 8890...
echo   🛡️ 7 Dac Nhiem: AURA, Alpha, Beta, Delta, Gamma, Omega, Zeta
echo   🌐 Truy cap trinh duyet tai: http://127.0.0.1:8890/
echo.
echo ========================================================
pushd "%~dp0"
"%~dp0venv\Scripts\python.exe" -m interface.noi_bo_app --port 8890
popd
pause
