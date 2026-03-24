@echo off
title CAN Dashboard - Gurnamak
color 0A
echo.
echo  ============================================
echo   Universal CAN Dashboard - Gurnamak
echo  ============================================
echo.

REM Python barmy?
python --version >nul 2>&1
if errorlevel 1 (
    echo [YALNYSHLYK] Python tapylmady!
    echo python.org-dan yukle we PATH-a gos.
    pause
    exit /b 1
)
echo [OK] Python tapyldy

REM pip bilen gerekli kutuphaneleri gur
echo.
echo  Kutuphaneler gurulyar...
pip install python-can cantools --quiet
if errorlevel 1 (
    echo [YALNYSHLYK] pip gurmak basharmady!
    pause
    exit /b 1
)
echo [OK] python-can, cantools gurundy

REM DBC fayllary generate et
echo.
echo  Toyota DBC faylyny doretyar...
python merge_dbc.py
if errorlevel 1 (
    echo [DUYDURYS] DBC merge basharmady - el bilen goymaly
)

echo.
echo  ============================================
echo   Gurnamak tamamlandy!
echo   Isletmek ucin: run.bat
echo  ============================================
echo.
pause
