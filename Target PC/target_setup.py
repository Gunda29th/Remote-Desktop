import hashlib
import json
import secrets
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

APPDIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "RemoteDesk"
CRED = APPDIR / "credentials.json"

def save_account(username, password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 180000
    )
    APPDIR.mkdir(parents=True, exist_ok=True)
    CRED.write_text(json.dumps({
        "username": username,
        "salt": salt.hex(),
        "hash": digest.hex(),
        "iterations": 180000
    }), encoding="utf-8")

root = tk.Tk()
root.title("RemoteDesk - First Time Setup")
root.geometry("400x280")
root.resizable(False, False)

tk.Label(root, text="RemoteDesk First-Time Setup").pack(pady=(20, 8))
tk.Label(root, text="Create the account used by the Main PC").pack(pady=4)

tk.Label(root, text="Username").pack()
username = tk.Entry(root, width=30)
username.pack(pady=3)

tk.Label(root, text="Password / PIN").pack()
password = tk.Entry(root, width=30, show="*")
password.pack(pady=3)

tk.Label(root, text="Confirm Password / PIN").pack()
confirm = tk.Entry(root, width=30, show="*")
confirm.pack(pady=3)

def create():
    u = username.get().strip()
    p = password.get()
    c = confirm.get()

    if not u or not p:
        messagebox.showerror("RemoteDesk", "Username and password/PIN are required.")
        return
    if p != c:
        messagebox.showerror("RemoteDesk", "Passwords do not match.")
        return

    save_account(u, p)
    messagebox.showinfo(
        "RemoteDesk",
        "Account created successfully.\n\nRemoteDesk is ready."
    )
    root.destroy()

tk.Button(root, text="Create Account", width=18, command=create).pack(pady=14)

root.update_idletasks()
root.mainloop()
