@echo off
chcp 65001 > nul
echo ========================================================
echo   AURA - App Lap trinh bang THE (ban DAY DU)
echo ========================================================
echo.
echo   Ban nay BAT chay ma/test, nen dung duoc:
echo     - nut DO DONG DU LIEU  (xem gia tri bien qua tung buoc)
echo     - nut TIM LOI NHAN QUA (E1 tu do 5 ho loi so sanh/logic)
echo.
echo   LUU Y: tien trinh chay test CHUA duoc cach ly khoi tep/mang/RAM.
echo   Chi dung tren may cua ban, voi ma cua ban. Dong cua so nay de dung.
echo.
echo   Muon ban CHI DOC (khong chay ma) thi bam start_the_app.bat
echo ========================================================
echo.
pushd "%~dp0"
"%~dp0venv\Scripts\python.exe" -m interface.the_app --port 8088 --allow-exec
popd
pause
