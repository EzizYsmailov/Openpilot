@echo off
title CAN Dashboard
python main.py
if errorlevel 1 (
    echo.
    echo YALNYSHLYK! setup.bat islet.
    pause
)
