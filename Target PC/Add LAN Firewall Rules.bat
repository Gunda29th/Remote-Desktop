@echo off
netsh advfirewall firewall add rule name="RemoteDesk Screen 5051" dir=in action=allow protocol=TCP localport=5051 >nul
netsh advfirewall firewall add rule name="RemoteDesk Input 5052" dir=in action=allow protocol=TCP localport=5052 >nul
echo LAN firewall rules added.
pause
