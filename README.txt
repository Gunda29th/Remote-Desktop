============================================================
                         REMOTEDESK
============================================================
LAN Remote Desktop + Clipboard + File/Folder Sharing
Version: 1.3.2

A simple Windows LAN remote-desktop project.

The project is designed for two PCs:

    MAIN PC  -------------------->  TARGET PC
    Client / Controller             Server / Remote PC

The Main PC connects to the Target PC and can view/control it.
Clipboard and file/folder sharing work in BOTH directions.

------------------------------------------------------------
FEATURES
------------------------------------------------------------

Remote desktop
    [x] Live screen
    [x] Mouse control
    [x] Keyboard control
    [x] Ctrl+C / Ctrl+V and other keyboard shortcuts
    [x] Connect
    [x] Disconnect
    [x] Reconnect

Authentication
    [x] Username + password/PIN
    [x] One-time account creation on Target PC
    [x] Main PC "Remember me"
    [x] Saved Main PC password is protected with Windows DPAPI

Clipboard / transfer
    [x] Text clipboard - Main <-> Target
    [x] Image clipboard - Main <-> Target
    [x] File copy/paste - Main <-> Target
    [x] Folder copy/paste - Main <-> Target

Target PC
    [x] Simple local server GUI
    [x] Start Server
    [x] Stop Server
    [x] Restart Server
    [x] Connected / Disconnected status
    [x] Target does NOT need the Main PC IP

------------------------------------------------------------
IMPORTANT: HOW THE PROJECT WORKS
------------------------------------------------------------

MAIN PC
    The Main PC is the client/controller.

    You enter the TARGET PC's IP address on the Main PC.

TARGET PC
    The Target PC is the server.

    It waits for the Main PC connection.

Only the Main PC needs to know the Target PC IP. The README uses <TARGET_PC_IP> as a placeholder; replace it with your Target PC's current LAN IP when connecting.

The Target PC does NOT need to enter the Main PC IP.

After the Main PC connects, the same authenticated RemoteDesk
session is used for:

    Screen
    Mouse
    Keyboard
    Clipboard
    Files / folders

No separate clipboard IP is required.

------------------------------------------------------------
NETWORK PORTS
------------------------------------------------------------

Target PC listens on:

    TCP 5051  = Screen
    TCP 5052  = Input + clipboard/file transfer

This version is intended for a trusted LAN.

DO NOT expose ports 5051 or 5052 directly to the Internet.

For Internet access, a proper secure transport/authentication
design should be added first.

------------------------------------------------------------
REQUIREMENTS
------------------------------------------------------------

Operating system:
    Windows

Python:
    Python 3.x with the Python Launcher ("py") available.

Python packages:

    Main PC:
        Pillow
        pywin32

    Target PC:
        mss
        Pillow
        pyautogui
        pywin32

The included installers install these packages with pip.

------------------------------------------------------------
FOLDER STRUCTURE
------------------------------------------------------------

RemoteDesk...
|
+-- Main PC
|   |
|   +-- Install Main PC.bat
|   +-- Start RemoteDesk.vbs
|   +-- Start RemoteDesk.bat
|   +-- remote_client.py
|   +-- clipboard_bridge.py
|
+-- Target PC
|   |
|   +-- Install Target PC.bat
|   +-- Start RemoteDesk.bat
|   +-- Launch RemoteDesk.vbs
|   +-- target_launcher.py
|   +-- target_setup.py
|   +-- target_gui.py
|   +-- remote_server_core.py
|   +-- clipboard_bridge.py
|   +-- Reset Target Account.bat
|   +-- Add LAN Firewall Rules.bat
|
+-- README.txt

------------------------------------------------------------
FIRST-TIME TARGET PC SETUP
------------------------------------------------------------

Do this on the TARGET PC.

1. Copy the project to the Target PC.

2. Open:
       Target PC

3. Run:
       Install Target PC.bat

4. Wait for the dependency installation to finish.

5. Run:
       Start RemoteDesk.bat

6. On the first launch, RemoteDesk opens:
       RemoteDesk First-Time Setup

7. Create:
       Username
       Password / PIN
       Confirm Password / PIN

8. Click:
       Create Account

9. After the account is created, the Target Server GUI opens.

The account is stored locally in the Windows user AppData area.

You normally create the account only once.

------------------------------------------------------------
TARGET PC NORMAL USE
------------------------------------------------------------

After the first-time setup:

1. Run:
       Start RemoteDesk.bat

2. The Target Server GUI opens.

The buttons control ONLY the Target PC's local server:

    Start Server
        Starts the RemoteDesk server on the Target PC.

    Stop Server
        Stops the RemoteDesk server on the Target PC.

    Restart Server
        Restarts the Target PC server.

    Connected / Disconnected
        Shows the current Main PC connection status.

The Target GUI does NOT connect to the Main PC.

------------------------------------------------------------
OPTIONAL TARGET FIREWALL SETUP
------------------------------------------------------------

If the Main PC cannot connect to the Target PC, Windows
Firewall may be blocking the server.

On the TARGET PC, run:

    Add LAN Firewall Rules.bat

This adds inbound TCP rules for:

    5051
    5052

Only do this on a trusted LAN.

------------------------------------------------------------
FIRST-TIME MAIN PC SETUP
------------------------------------------------------------

Do this on the MAIN PC.

1. Copy the project to the Main PC.

2. Open:
       Main PC

3. Run:
       Install Main PC.bat

4. Wait for installation to finish.

5. Start RemoteDesk with:
       Start RemoteDesk.vbs

The VBS launcher is the clean launcher and does not open a
normal CMD/Windows Terminal window.

------------------------------------------------------------
CONNECTING FROM MAIN PC
------------------------------------------------------------

On the Main PC RemoteDesk window:

    Target IP:
        Enter the Target PC's LAN IPv4 address.

    Username:
        Enter the username created on the Target PC.

    Password/PIN:
        Enter the password/PIN created on the Target PC.

    Remember me:
        Enable this if you want the Main PC to remember the
        connection details.

Then click:

    Connect

Example:

    Target IP:     <TARGET_PC_IP>
    Username:      <YOUR_USERNAME>
    Password/PIN:  <YOUR_PASSWORD_OR_PIN>

Do NOT use the Main PC's IP in the Target GUI.

------------------------------------------------------------
DISCONNECT / RECONNECT
------------------------------------------------------------

MAIN PC:

    Disconnect
        Closes the current remote session.

    Reconnect
        Disconnects and starts a new connection attempt.

TARGET PC:

    Stop Server
        Completely stops the Target server.

    Restart Server
        Restarts the Target server.

------------------------------------------------------------
REMOTE KEYBOARD
------------------------------------------------------------

After connecting:

1. Click once inside the remote screen.
2. The remote screen receives keyboard focus.
3. Use normal shortcuts.

Examples:

    Ctrl+C
    Ctrl+V
    Ctrl+X
    Ctrl+A
    Ctrl+Z
    Ctrl+S

If a shortcut appears not to work, click the remote screen
again and retry.

------------------------------------------------------------
CLIPBOARD SHARING
------------------------------------------------------------

Clipboard sharing is BIDIRECTIONAL.

    MAIN PC  <----------------->  TARGET PC

Text:
    Copy text on either PC.
    Paste it on the other PC.

Images:
    Copy an image on either PC.
    Paste it on the other PC.

No additional IP address is required.

The clipboard uses the existing authenticated RemoteDesk
connection after the Main PC has connected to the Target PC.

------------------------------------------------------------
FILE AND FOLDER SHARING
------------------------------------------------------------

File/folder sharing is also BIDIRECTIONAL.

MAIN -> TARGET:

1. On the Main PC, open Windows Explorer.
2. Copy a file or folder with Ctrl+C.
3. On the Target PC, choose the destination.
4. Press Ctrl+V.

TARGET -> MAIN:

1. On the Target PC, open Windows Explorer.
2. Copy a file or folder with Ctrl+C.
3. On the Main PC, choose the destination.
4. Press Ctrl+V.

The transfer uses the existing authenticated RemoteDesk
connection.

No separate IP needs to be entered for file sharing.

------------------------------------------------------------
IMPORTANT ABOUT FILE/FOLDER TRANSFERS
------------------------------------------------------------

Files and folders are transferred through a temporary
RemoteDesk directory and then exposed to Windows as clipboard
file data.

Test with a small file first.

For large files/folders, transfer time depends on the LAN
connection and disk speed.

------------------------------------------------------------
TROUBLESHOOTING
------------------------------------------------------------

Problem:
    Main PC cannot connect.

Check:

    1. Target PC RemoteDesk is running.
    2. Target GUI says it is waiting for Main PC.
    3. Target PC IP address is correct.
    4. Both PCs are on the same LAN.
    5. Windows Firewall allows TCP 5051 and 5052.
    6. Username/password/PIN are correct.

Problem:
    Target GUI opens but server is stopped.

Solution:

    Click:
        Start Server

Problem:
    Connection is lost.

Try:

    Main PC -> Reconnect

If that does not work:

    Target PC -> Restart Server
    Main PC -> Connect

Problem:
    Ctrl+V or another shortcut does not work.

Solution:

    Click once inside the remote screen, then retry.

Problem:
    Clipboard works one direction only.

Check that BOTH PCs are using the same project version.

Do not mix files from older RemoteDesk versions.

Problem:
    Authentication fails.

Make sure the username and password/PIN exactly match the
account created on the Target PC.

If you intentionally need to create a new Target account:

    Target PC -> Reset Target Account.bat

Then start RemoteDesk again and create the new account.

------------------------------------------------------------
UPDATING THE PROJECT
------------------------------------------------------------

When a new version is released:

1. Stop RemoteDesk on both PCs.
2. Back up the current project folder.
3. Replace the project files with the new version.
4. Run the updated installer on the Main PC if dependencies
   changed.
5. Run the updated installer on the Target PC if dependencies
   changed.
6. Start the Target PC.
7. Start the Main PC.
8. Connect and test:
       Screen
       Mouse
       Keyboard
       Ctrl+C / Ctrl+V
       Text clipboard
       Image clipboard
       File
       Folder

Do not mix Python files from different RemoteDesk versions
unless you know they are compatible.

------------------------------------------------------------
GITHUB
------------------------------------------------------------

For GitHub, upload the project source code and this README.

Recommended repository name:

    RemoteDesk

Recommended description:

    Windows LAN remote desktop with bidirectional clipboard
    and file/folder sharing.

Do NOT upload:

    - Personal usernames
    - Passwords/PINs
    - credentials.json
    - Personal IP addresses
    - Personal screenshots containing private information
    - Personal configuration files

The Target account is stored outside the project folder under
the Windows user's AppData area.

The Main PC saved connection settings are also stored under
the Windows user's AppData area.

------------------------------------------------------------
SECURITY NOTES
------------------------------------------------------------

This project is intended as a LAN prototype.

The Target server listens on TCP 5051 and 5052.

Only use it on a network you trust.

Do not expose these ports directly to the public Internet.

RemoteDesk provides remote keyboard and mouse control of the
Target PC, so anyone who successfully authenticates should be
treated as having significant control of that Target machine.

Keep your username and password/PIN private.

------------------------------------------------------------
PROJECT STATUS
------------------------------------------------------------

Version 1.0 includes:

    Screen                     YES
    Mouse                      YES
    Keyboard                   YES
    Keyboard shortcuts         YES
    Authentication             YES
    Remember Me                YES
    Connect                    YES
    Disconnect                 YES
    Reconnect                  YES
    Target local GUI           YES
    Text clipboard             YES - both directions
    Image clipboard            YES - both directions
    File sharing               YES - both directions
    Folder sharing             YES - both directions

Main PC is the client/controller.

Target PC is the server.

============================================================
