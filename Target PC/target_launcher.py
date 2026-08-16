import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
APPDATA = Path(os.environ.get("APPDATA", str(Path.home())))
CRED = APPDATA / "RemoteDesk" / "credentials.json"
SETUP = BASE / "target_setup.py"
GUI = BASE / "target_gui.py"

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

def run():
    if not CRED.exists():
        # First launch: show the setup GUI. It is intentionally visible.
        p = subprocess.Popen(
            [sys.executable, str(SETUP)],
            cwd=str(BASE),
            creationflags=CREATE_NO_WINDOW
        )
        p.wait()

        if not CRED.exists():
            return

    # Normal operation: only the Target server GUI is shown.
    subprocess.Popen(
        [sys.executable, str(GUI)],
        cwd=str(BASE),
        creationflags=CREATE_NO_WINDOW
    )

if __name__ == "__main__":
    run()
