import io
import os
import struct
import tempfile
import time
import uuid
import zipfile

import win32clipboard
import win32con

CLIP_KIND_TEXT = b"T"
CLIP_KIND_IMAGE = b"I"
CLIP_KIND_FILES = b"F"

CLIP_MAX_MEMORY = 32 * 1024 * 1024
CLIP_CHUNK = 1024 * 1024
CLIP_MAGIC = b"CBR1"
CLIP_HEADER_SIZE = 4 + 1 + 8 + 16 + 8


class ClipboardBridge:
    def __init__(self):
        self.clip_sender_id = uuid.uuid4().bytes
        self.clip_counter = 0
        self.clip_last_signature = None
        self.clip_applying_remote = False
        self.clip_last_remote_apply = 0.0
        self.clip_temp_root = os.path.join(
            tempfile.gettempdir(), "RemoteDeskClipboard"
        )
        os.makedirs(self.clip_temp_root, exist_ok=True)

    def open_clipboard(self):
        for _ in range(20):
            try:
                win32clipboard.OpenClipboard()
                return True
            except Exception:
                time.sleep(0.02)
        return False

    def close_clipboard(self):
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass

    def get_clipboard(self):
        if not self.open_clipboard():
            return None, None
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                return "files", list(
                    win32clipboard.GetClipboardData(win32con.CF_HDROP)
                )

            if win32clipboard.IsClipboardFormatAvailable(
                win32con.CF_UNICODETEXT
            ):
                return "text", win32clipboard.GetClipboardData(
                    win32con.CF_UNICODETEXT
                )

            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                return "image", bytes(
                    win32clipboard.GetClipboardData(win32con.CF_DIB)
                )

            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIBV5):
                return "image", bytes(
                    win32clipboard.GetClipboardData(win32con.CF_DIBV5)
                )

            return None, None
        except Exception:
            return None, None
        finally:
            self.close_clipboard()

    def signature(self, kind, data):
        if kind == "text":
            return ("text", data)

        if kind == "image":
            return ("image", len(data), hash(data))

        if kind == "files":
            result = []
            for path in data:
                try:
                    st = os.stat(path)
                    result.append(
                        (os.path.abspath(path), st.st_size, st.st_mtime_ns)
                    )
                except OSError:
                    result.append((os.path.abspath(path), None, None))
            return ("files", tuple(result))

        return None

    def set_text(self, text):
        if not self.open_clipboard():
            return False
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(
                win32con.CF_UNICODETEXT, text
            )
            return True
        except Exception:
            return False
        finally:
            self.close_clipboard()

    def set_image(self, data):
        if not self.open_clipboard():
            return False
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            return True
        except Exception:
            return False
        finally:
            self.close_clipboard()

    def set_files(self, paths):
        if not paths:
            return False

        header = struct.pack("IiiII", 20, 0, 0, 0, 1)
        names = "".join(
            os.path.abspath(p) + "\0" for p in paths
        ) + "\0"
        payload = header + names.encode("utf-16le")

        if not self.open_clipboard():
            return False

        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(
                win32con.CF_HDROP, payload
            )
            return True
        except Exception:
            return False
        finally:
            self.close_clipboard()

    def next_clip_counter(self):
        self.clip_counter += 1
        return self.clip_counter

    def build_clip_header(self, kind, size):
        kind_byte = {
            "text": CLIP_KIND_TEXT,
            "image": CLIP_KIND_IMAGE,
            "files": CLIP_KIND_FILES,
        }[kind]

        return (
            b"C"
            + CLIP_MAGIC
            + kind_byte
            + struct.pack("!Q", size)
            + self.clip_sender_id
            + struct.pack("!Q", self.next_clip_counter())
        )

    def send_clip_bytes(self, conn, kind, data):
        header = self.build_clip_header(kind, len(data))
        conn.sendall(header)

        view = memoryview(data)
        while view:
            sent = conn.send(view[:CLIP_CHUNK])
            if sent <= 0:
                raise ConnectionError("Clipboard connection closed")
            view = view[sent:]

    def make_archive(self, paths):
        valid = [
            os.path.abspath(p)
            for p in paths
            if os.path.exists(p)
        ]
        if not valid:
            return None

        archive = os.path.join(
            self.clip_temp_root,
            "send_" + uuid.uuid4().hex + ".zip"
        )

        with zipfile.ZipFile(
            archive, "w", compression=zipfile.ZIP_STORED
        ) as zf:
            for path in valid:
                if os.path.isdir(path):
                    parent = os.path.dirname(
                        os.path.normpath(path)
                    )

                    for current, dirs, files in os.walk(path):
                        rel_root = os.path.relpath(
                            current, parent
                        )

                        if not files and not dirs:
                            zf.writestr(
                                rel_root.rstrip("/") + "/",
                                b""
                            )

                        for name in files:
                            full = os.path.join(current, name)
                            arc = os.path.relpath(full, parent)
                            zf.write(full, arc)
                else:
                    zf.write(
                        path,
                        os.path.basename(os.path.normpath(path))
                    )

        return archive

    def apply_received_files(self, archive):
        destination = os.path.join(
            self.clip_temp_root,
            "recv_" + uuid.uuid4().hex
        )
        os.makedirs(destination, exist_ok=True)

        try:
            with zipfile.ZipFile(archive, "r") as zf:
                base = os.path.abspath(destination)

                for member in zf.infolist():
                    target = os.path.abspath(
                        os.path.join(destination, member.filename)
                    )

                    if os.path.commonpath([base, target]) != base:
                        raise ValueError("Unsafe archive path")

                zf.extractall(destination)

            paths = [
                os.path.join(destination, name)
                for name in os.listdir(destination)
            ]

            if self.set_files(paths):
                self.clip_last_signature = self.signature(
                    "files", paths
                )
                self.clip_last_remote_apply = time.monotonic()

            return True

        except Exception as e:
            print("Clipboard file receive error:", e)
            shutil_path = destination
            try:
                import shutil
                shutil.rmtree(shutil_path, ignore_errors=True)
            except Exception:
                pass
            return False

    def clipboard_monitor_prepare(self):
        kind, data = self.get_clipboard()

        if kind is not None:
            self.clip_last_signature = self.signature(kind, data)

    def clipboard_changed(self):
        kind, data = self.get_clipboard()

        if kind is None:
            return None, None

        current = self.signature(kind, data)

        if current == self.clip_last_signature:
            return None, None

        self.clip_last_signature = current
        return kind, data

    def apply_remote_clipboard(self, kind, data):
        self.clip_applying_remote = True

        try:
            if kind == "text":
                ok = self.set_text(data)
            elif kind == "image":
                ok = self.set_image(data)
            else:
                ok = False

            if ok:
                k, d = self.get_clipboard()
                if k is not None:
                    self.clip_last_signature = self.signature(k, d)
                self.clip_last_remote_apply = time.monotonic()

        finally:
            self.clip_applying_remote = False
