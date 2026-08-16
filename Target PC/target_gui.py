import subprocess
import sys
import tkinter as tk
from pathlib import Path

BASE = Path(__file__).resolve().parent
SERVER = BASE / "remote_server_core.py"
STATUS = BASE / "remote_status.txt"

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

class TargetGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RemoteDesk Server - Target PC")
        self.root.geometry("430x260")
        self.root.resizable(False, False)

        tk.Label(self.root, text="RemoteDesk Server").pack(pady=20)

        self.status = tk.Label(self.root, text="Stopped")
        self.status.pack(pady=5)

        self.detail = tk.Label(self.root, text="Server is not running")
        self.detail.pack(pady=5)

        row = tk.Frame(self.root)
        row.pack(pady=20)

        tk.Button(row, text="Start Server", width=12,
                  command=self.start_server).grid(row=0, column=0, padx=4)
        tk.Button(row, text="Stop Server", width=12,
                  command=self.stop_server).grid(row=0, column=1, padx=4)
        tk.Button(row, text="Restart Server", width=12,
                  command=self.restart_server).grid(row=0, column=2, padx=4)

        tk.Label(self.root, text="LAN server: TCP 5051 / 5052").pack()

        self.proc = None
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.root.after(300, self.start_server)
        self.root.after(200, self.poll)

    def start_server(self):
        if self.proc is not None and self.proc.poll() is None:
            return
        try:
            self.proc = subprocess.Popen(
                [sys.executable, str(SERVER)],
                cwd=str(BASE),
                creationflags=CREATE_NO_WINDOW
            )
            self.status.config(text="Starting...")
            self.detail.config(text="Starting local server")
        except Exception as e:
            self.status.config(text="Error")
            self.detail.config(text=str(e))

    def stop_server(self):
        if self.proc is not None:
            try:
                if self.proc.poll() is None:
                    self.proc.terminate()
                    self.proc.wait(timeout=3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc = None
        self.status.config(text="Stopped")
        self.detail.config(text="Server is not running")

    def restart_server(self):
        self.stop_server()
        self.root.after(500, self.start_server)

    def poll(self):
        try:
            if self.proc is not None and self.proc.poll() is None and STATUS.exists():
                parts = STATUS.read_text(encoding="utf-8").strip().split("|", 1)
                if len(parts) == 2:
                    self.status.config(text=parts[0])
                    self.detail.config(text=parts[1])
        except Exception:
            pass
        self.root.after(250, self.poll)

    def close(self):
        self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    TargetGUI().root.mainloop()
