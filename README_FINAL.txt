RemoteDesk v1.3.2 - Keyboard Shortcut Focus Fix

Fixed remote keyboard shortcut handling.

The Main PC remote screen now receives keyboard events with bind_all,
and clicking the remote screen gives it keyboard focus.

This fixes shortcuts such as:
Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+Z, Ctrl+S.

The IP/username/password fields remain local and are not sent to the Target.
Clipboard/file/folder sharing remains bidirectional.
