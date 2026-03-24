@echo off
title CAN Dashboard - DEMO
python main.py --demo
if errorlevel 1 (
    echo.
    echo YALNYSHLYK! setup.bat islet.
    pause
)
