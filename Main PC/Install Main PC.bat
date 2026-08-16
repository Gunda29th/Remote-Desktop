@echo off
setlocal
cd /d "%~dp0"
title RemoteDesk v1.2 Main PC Installer
where py >nul 2>&1
if errorlevel 1 (
 echo Python 3.12 was not found.
 pause
 exit /b 1
)
echo Installing RemoteDesk dependencies...
py -m pip install Pillow pywin32
if errorlevel 1 (
 echo Dependency installation failed.
 pause
 exit /b 1
)
echo.
echo Main PC installation complete.
pause
