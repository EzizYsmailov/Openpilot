@echo off
title DBC Fayllary Gecirmek
color 0B
echo.
echo  ============================================
echo   opendbc-dan DBC Fayllary Gecirmek
echo  ============================================
echo.

set OPENDBC=D:\opendbc-master\opendbc-master\opendbc\dbc
set DEST=%~dp0

if not exist "%OPENDBC%" (
    echo [YALNYSHLYK] opendbc tapylmady: %OPENDBC%
    echo Yoly config.py-de uytget.
    pause
    exit /b 1
)

echo Geciriljek DBC fayllar:
echo.

REM ── Toyota/Lexus ────────────────────────────────────────
echo  [1] Toyota/Lexus
python "%~dp0merge_dbc.py"

REM ── Goni kopiyalanyan fayllar ───────────────────────────
echo  [2] Honda/Acura
for %%f in ("%OPENDBC%\acura_ilx_2016_nidec.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [3] BMW
for %%f in ("%OPENDBC%\bmw_e9x_e8x.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [4] Ford/Lincoln
for %%f in ("%OPENDBC%\ford_fusion_2018_pt.dbc" "%OPENDBC%\ford_lincoln_base_pt.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [5] GM (Chevrolet/Cadillac)
for %%f in ("%OPENDBC%\gm_global_a_powertrain_expansion.dbc" "%OPENDBC%\gm_global_a_chassis.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [6] Hyundai/Kia
for %%f in ("%OPENDBC%\hyundai_kia_generic.dbc" "%OPENDBC%\hyundai_2015_ccan.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [7] Mazda
for %%f in ("%OPENDBC%\mazda_2017.dbc" "%OPENDBC%\mazda_3_2019.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [8] Mercedes-Benz
for %%f in ("%OPENDBC%\mercedes_benz_e350_2010.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [9] Toyota Prius 2010
for %%f in ("%OPENDBC%\toyota_prius_2010_pt.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [10] Toyota ADAS/Radar
for %%f in ("%OPENDBC%\toyota_adas.dbc" "%OPENDBC%\toyota_tss2_adas.dbc" "%OPENDBC%\toyota_2017_ref_pt.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [11] Chrysler/Dodge/Jeep
for %%f in ("%OPENDBC%\chrysler_cusw.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo  [12] Nissan
for %%f in ("%OPENDBC%\nissan_xterra_2011.dbc") do (
    copy "%%f" "%DEST%" >nul && echo     [OK] %%~nxf
)

echo.
echo  Gecirilen DBC fayllar:
dir "%DEST%*.dbc" /b 2>nul | findstr /v "^$"
echo.
echo  ============================================
echo   Tamamlandy! run.bat bilen proyekti ac.
echo  ============================================
echo.
pause
