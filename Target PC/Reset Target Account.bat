@echo off
setlocal
set "CRED=%APPDATA%\RemoteDesk\credentials.json"
if exist "%CRED%" (
 del /q "%CRED%"
 echo RemoteDesk account removed.
 echo Next time you start RemoteDesk, account setup will appear.
) else (
 echo No RemoteDesk account exists.
)
pause
