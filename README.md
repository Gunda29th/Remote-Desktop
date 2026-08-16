# RemoteDesk

**Windows LAN Remote Desktop + Clipboard + File/Folder Sharing**

RemoteDesk is a Windows LAN remote-desktop application that lets one PC connect to and control another PC on the same trusted local network.

> **Version: 1.0**  
> **Author & Maintainer: Gunda29th**

## Features

### Remote Desktop
- Live remote screen
- Mouse control
- Keyboard control
- Keyboard shortcuts including `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+A`, `Ctrl+Z`, and `Ctrl+S`
- Connect, disconnect, and reconnect

### Authentication
- Username + password/PIN authentication
- One-time account creation on the Target PC
- Remember Me support on the Main PC
- Saved Main PC password protected with Windows DPAPI

### Bidirectional Clipboard
- Text clipboard sharing
- Image clipboard sharing
- Copy and paste between Main PC and Target PC
- Uses the existing authenticated RemoteDesk connection

### File and Folder Sharing
- Main PC → Target PC
- Target PC → Main PC
- File copy/paste
- Folder copy/paste

### Target PC Server GUI
- Start Server
- Stop Server
- Restart Server
- Connection status

## How It Works

```text
MAIN PC                              TARGET PC
Client / Controller                  Server / Remote PC

┌───────────────────┐                ┌───────────────────┐
│    RemoteDesk     │     LAN        │    RemoteDesk     │
│      Client       │ ─────────────> │      Server       │
│                   │                │                   │
│ Screen / Input    │                │ Screen / Input    │
│ Clipboard         │                │ Clipboard         │
│ File Transfer     │                │ File Transfer     │
└───────────────────┘                └───────────────────┘
```

The Main PC connects using the Target PC's LAN IPv4 address. The Target PC does not need the Main PC's IP address.

After authentication, the same RemoteDesk session handles screen, mouse, keyboard, clipboard, and file/folder transfers.

## Network Ports

| Port | Purpose |
|---|---|
| `5051/TCP` | Screen streaming |
| `5052/TCP` | Input, clipboard, and file/folder transfer |

### Security Warning

RemoteDesk is intended for use on a trusted LAN.

**Do not expose TCP ports `5051` or `5052` directly to the public Internet.**

RemoteDesk provides remote keyboard and mouse control, so successful authentication gives the connected user significant control over the Target PC.

## Requirements

- Windows
- Python 3.x
- Python Launcher (`py`)

### Main PC packages
- Pillow
- pywin32

### Target PC packages
- mss
- Pillow
- pyautogui
- pywin32

The included installer `.bat` files install the required Python packages.

## Project Structure

```text
Remote-Desktop/
│
├── Main PC/
│   ├── Install Main PC.bat
│   ├── Start RemoteDesk.vbs
│   ├── Start RemoteDesk.bat
│   ├── remote_client.py
│   └── clipboard_bridge.py
│
├── Target PC/
│   ├── Install Target PC.bat
│   ├── Start RemoteDesk.bat
│   ├── Launch RemoteDesk.vbs
│   ├── target_launcher.py
│   ├── target_setup.py
│   ├── target_gui.py
│   ├── remote_server_core.py
│   ├── clipboard_bridge.py
│   ├── Reset Target Account.bat
│   └── Add LAN Firewall Rules.bat
│
├── README.md
├── README.txt
├── LICENSE
└── CREDITS.md
```

## Installation

### Target PC

1. Copy the project to the Target PC.
2. Open the `Target PC` folder.
3. Run `Install Target PC.bat`.
4. Start RemoteDesk using `Start RemoteDesk.bat`.
5. On first launch, create the Target PC username and password/PIN.
6. The Target Server GUI will open.

### Main PC

1. Copy the project to the Main PC.
2. Open the `Main PC` folder.
3. Run `Install Main PC.bat`.
4. Start RemoteDesk using `Start RemoteDesk.vbs`.
5. Enter the Target PC's LAN IPv4 address.
6. Enter the username and password/PIN created on the Target PC.
7. Click **Connect**.

## Windows Firewall

If the Main PC cannot connect, Windows Firewall may be blocking the server.

On the Target PC, run:

```text
Add LAN Firewall Rules.bat
```

This adds inbound TCP rules for ports `5051` and `5052`.

Only do this on a trusted LAN.

## Clipboard Usage

After connecting, copy text or an image on either PC and paste it on the other PC. No additional clipboard IP address is required.

## File and Folder Transfer

### Main → Target
1. Copy a file or folder on the Main PC.
2. Select the destination on the Target PC.
3. Press `Ctrl+V`.

### Target → Main
1. Copy a file or folder on the Target PC.
2. Select the destination on the Main PC.
3. Press `Ctrl+V`.

For large files, transfer speed depends on the LAN connection and disk speed.

## Troubleshooting

### Main PC cannot connect

Check that:
- RemoteDesk is running on the Target PC.
- The Target server is started.
- The Target PC IP address is correct.
- Both PCs are on the same LAN.
- Windows Firewall allows TCP `5051` and `5052`.
- Username and password/PIN are correct.

### Ctrl+V or another shortcut does not work

Click once inside the remote screen to give it keyboard focus, then try again.

### Clipboard works in only one direction

Make sure both PCs are running the same RemoteDesk version. Do not mix files from different versions.

### Authentication fails

Verify the username and password/PIN created on the Target PC.

To intentionally create a new Target account, use `Reset Target Account.bat`, then start RemoteDesk again.

## Version 1.0

RemoteDesk **v1.0** includes:

- Remote screen viewing
- Mouse and keyboard control
- Keyboard shortcuts
- Authentication
- Remember Me
- Bidirectional text clipboard
- Bidirectional image clipboard
- Bidirectional file transfer
- Bidirectional folder transfer
- Target PC server GUI
- Connect / Disconnect / Reconnect
- LAN firewall setup support

## Author and Attribution

**RemoteDesk is developed and maintained by [Gunda29th](https://github.com/Gunda29th).**

The repository's Git history preserves the development work and changes made by the project author.

If you reuse, modify, or redistribute this project or substantial portions of it, retain the copyright and license notice and credit the original project:

> **RemoteDesk by Gunda29th**  
> https://github.com/Gunda29th/Remote-Desktop

See [`LICENSE`](LICENSE) and [`CREDITS.md`](CREDITS.md) for attribution and license information.

## License

RemoteDesk is licensed under the **MIT License**.

Copyright © 2026 Gunda29th.

See [`LICENSE`](LICENSE) for the complete license text.

## Disclaimer

RemoteDesk is a personal LAN remote-desktop project. Use it only on systems and networks where you have permission to remotely control the machine.

The current version is designed for trusted LAN environments and should not be exposed directly to the public Internet without additional security hardening.
