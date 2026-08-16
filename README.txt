RemoteDesk v0.6 - Correct Login Architecture

TARGET PC:
- One-time account setup during installation.
- No normal login screen.
- Simple server GUI: status, client, Disconnect, Reconnect, Restart.
- Server listens on 5051 screen and 5052 input.
- Target does not contain or need Main PC IP.

MAIN PC:
- Enter Target IP, username and password/PIN.
- Remember me stores IP/username and encrypts the saved password with Windows DPAPI.
- Connect / Disconnect / Reconnect.
- Screen + mouse + keyboard are included.

This is still LAN-only. Do not expose ports 5051/5052 to the Internet yet.

Clipboard integration is NOT enabled in v0.6. It will be integrated after the core authenticated remote session is verified.


RemoteDesk v1.3.2 - Keyboard Shortcut Focus Fix

Fixed remote keyboard shortcut handling.

The Main PC remote screen now receives keyboard events with bind_all,
and clicking the remote screen gives it keyboard focus.

This fixes shortcuts such as:
Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+Z, Ctrl+S.

The IP/username/password fields remain local and are not sent to the Target.
Clipboard/file/folder sharing remains bidirectional.
