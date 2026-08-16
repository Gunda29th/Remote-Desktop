import base64, io, json, os, socket, struct, threading, uuid, ctypes, time, queue
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from clipboard_bridge import ClipboardBridge, CLIP_MAGIC, CLIP_MAX_MEMORY, CLIP_CHUNK

SCREEN_PORT=5051
INPUT_PORT=5052
MAGIC=b"LRD3"
AUTH_MAGIC=b"AUTH"
MAX_FRAME=12*1024*1024
SETTINGS=os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),"RemoteDesk","main_settings.json")

def dpapi_encrypt(text):
    class B(ctypes.Structure): _fields_=[("cbData",ctypes.c_ulong),("pbData",ctypes.POINTER(ctypes.c_ubyte))]
    raw=text.encode(); buf=ctypes.create_string_buffer(raw)
    inp=B(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte))); out=B()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(inp),None,None,None,None,0,ctypes.byref(out)): return ""
    data=ctypes.string_at(out.pbData,out.cbData); ctypes.windll.kernel32.LocalFree(out.pbData)
    return base64.b64encode(data).decode()

def dpapi_decrypt(enc):
    class B(ctypes.Structure): _fields_=[("cbData",ctypes.c_ulong),("pbData",ctypes.POINTER(ctypes.c_ubyte))]
    try: raw=base64.b64decode(enc)
    except: return ""
    buf=ctypes.create_string_buffer(raw); inp=B(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte))); out=B()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(inp),None,None,None,None,0,ctypes.byref(out)): return ""
    data=ctypes.string_at(out.pbData,out.cbData); ctypes.windll.kernel32.LocalFree(out.pbData)
    return data.decode()

def load_settings():
    try:
        d=json.load(open(SETTINGS,encoding="utf-8"))
        if d.get("password"): d["password"]=dpapi_decrypt(d["password"])
        return d
    except: return {}

def save_settings(d):
    os.makedirs(os.path.dirname(SETTINGS),exist_ok=True)
    out=dict(d)
    if out.get("password"): out["password"]=dpapi_encrypt(out["password"])
    json.dump(out,open(SETTINGS,"w",encoding="utf-8"))

class Client:
    def __init__(self):
        self.root=tk.Tk(); self.root.title("RemoteDesk - Main PC"); self.root.geometry("1100x760")
        self.ip=tk.StringVar(); self.user=tk.StringVar(); self.pw=tk.StringVar(); self.rem=tk.BooleanVar(value=True)
        s=load_settings(); self.ip.set(s.get("ip","")); self.user.set(s.get("username","")); self.pw.set(s.get("password","")); self.rem.set(bool(s.get("remember",True)))
        top=tk.Frame(self.root); top.pack(fill="x",padx=8,pady=8)
        tk.Label(top,text="Target IP").pack(side="left"); tk.Entry(top,textvariable=self.ip,width=18).pack(side="left",padx=5)
        tk.Label(top,text="Username").pack(side="left"); tk.Entry(top,textvariable=self.user,width=14).pack(side="left",padx=5)
        tk.Label(top,text="Password/PIN").pack(side="left"); tk.Entry(top,textvariable=self.pw,show="*",width=14).pack(side="left",padx=5)
        tk.Checkbutton(top,text="Remember me",variable=self.rem).pack(side="left",padx=5)
        self.cb=tk.Button(top,text="Connect",command=self.connect); self.cb.pack(side="left",padx=4)
        self.db=tk.Button(top,text="Disconnect",command=lambda:self.disconnect("Disconnected"),state="disabled"); self.db.pack(side="left",padx=4)
        tk.Button(top,text="Reconnect",command=self.reconnect).pack(side="left",padx=4)
        self.status=tk.StringVar(value="Disconnected"); tk.Label(top,textvariable=self.status).pack(side="left",padx=6)

        self.canvas=tk.Canvas(self.root,bg="black",highlightthickness=0); self.canvas.pack(fill="both",expand=True)
        self.running=False; self.screen=None; self.input=None; self.photo=None; self.sw=self.sh=1; self.dx=self.dy=0; self.dw=self.dh=1
        self.clip=ClipboardBridge()
        self.input_send_lock=threading.Lock()

        self.canvas.bind("<Motion>",self.move)
        for b in (1,2,3):
            self.canvas.bind(f"<ButtonPress-{b}>",lambda e,b=b:self.mouse(e,"down",b))
            self.canvas.bind(f"<ButtonRelease-{b}>",lambda e,b=b:self.mouse(e,"up",b))
        self.canvas.bind("<MouseWheel>",self.wheel)
        self.root.bind_all("<KeyPress>",self.key); self.root.bind_all("<KeyRelease>",self.key)
        self.canvas.bind("<Button-1>",self.focus_remote, add="+")
        self.root.protocol("WM_DELETE_WINDOW",self.close)

    def exact(self,c,n):
        d=bytearray()
        while len(d)<n:
            x=c.recv(min(1024*1024,n-len(d)))
            if not x: raise ConnectionError("Connection closed")
            d.extend(x)
        return bytes(d)

    def connect(self):
        if self.running:return
        ip=self.ip.get().strip(); u=self.user.get(); p=self.pw.get()
        if not ip or not u or not p:
            messagebox.showerror("RemoteDesk","Enter Target IP, username and password/PIN."); return
        self.status.set("Connecting...")
        if self.rem.get(): save_settings({"ip":ip,"username":u,"password":p,"remember":True})
        else: save_settings({"ip":"","username":"","password":"","remember":False})
        a=b=None
        try:
            sid=uuid.uuid4().bytes
            a=socket.socket(); a.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1); a.settimeout(8); a.connect((ip,SCREEN_PORT)); a.sendall(MAGIC+b"S"+sid); a.settimeout(None)
            b=socket.socket(); b.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1); b.settimeout(8); b.connect((ip,INPUT_PORT)); b.sendall(MAGIC+b"I"+sid)
            auth=json.dumps({"username":u,"password":p},separators=(",",":")).encode()
            b.sendall(AUTH_MAGIC+struct.pack("!I",len(auth))+auth)
            if self.exact(b,4)!=b"OKAY": raise PermissionError("Login failed")
            b.settimeout(None)
            self.screen=a; self.input=b; self.running=True
            self.clip.clipboard_monitor_prepare()
            self.cb.config(state="disabled"); self.db.config(state="normal"); self.status.set("Connected")
            threading.Thread(target=self.receive_screen,daemon=True).start()
            threading.Thread(target=self.receive_input_stream,daemon=True).start()
            threading.Thread(target=self.clipboard_monitor,daemon=True).start()
        except Exception as e:
            for s in (a,b):
                try:
                    if s:s.close()
                except:pass
            self.status.set("Connection failed: "+str(e))

    def receive_screen(self):
        try:
            while self.running:
                if self.exact(self.screen,1)!=b"S": raise ValueError("Bad frame")
                n=struct.unpack("!I",self.exact(self.screen,4))[0]
                if n<=0 or n>MAX_FRAME: raise ValueError("Invalid frame")
                img=Image.open(io.BytesIO(self.exact(self.screen,n))).convert("RGB")
                self.root.after(0,self.show,img)
        except Exception as e:
            if self.running:self.root.after(0,self.disconnect,"Connection lost: "+str(e))

    def receive_input_stream(self):
        # This is the ONLY reader for the authenticated input socket.
        # It handles both normal input acknowledgements/traffic and
        # Target -> Main clipboard/file packets.
        try:
            while self.running:
                first=self.input.recv(1)
                if not first: raise ConnectionError("Input connection closed")

                if first==b"C":
                    if self.exact(self.input,4)!=CLIP_MAGIC:
                        raise ValueError("Bad clipboard magic")
                    kind=self.exact(self.input,1)
                    size=struct.unpack("!Q",self.exact(self.input,8))[0]
                    self.exact(self.input,16)
                    self.exact(self.input,8)

                    if kind==b"T":
                        if size>CLIP_MAX_MEMORY: raise ValueError("Clipboard text too large")
                        data=self.exact(self.input,size).decode("utf-8")
                        self.root.after(0,self.clip.apply_remote_clipboard,"text",data)

                    elif kind==b"I":
                        if size>CLIP_MAX_MEMORY: raise ValueError("Clipboard image too large")
                        data=self.exact(self.input,size)
                        self.root.after(0,self.clip.apply_remote_clipboard,"image",data)

                    elif kind==b"F":
                        archive=os.path.join(self.clip.clip_temp_root,"recv_"+uuid.uuid4().hex+".zip")
                        remaining=size
                        try:
                            with open(archive,"wb") as f:
                                while remaining:
                                    chunk=self.input.recv(min(CLIP_CHUNK,remaining))
                                    if not chunk: raise ConnectionError("File transfer interrupted")
                                    f.write(chunk); remaining-=len(chunk)
                            self.root.after(0,self.clip.apply_received_files,archive)
                        except:
                            try: os.remove(archive)
                            except OSError: pass
                            raise
                    else:
                        raise ValueError("Unknown clipboard packet type")
                elif first==b"A":
                    # Reserved for future protocol acknowledgements.
                    self.exact(self.input,4)
                elif first==b"I":
                    # Server input acknowledgements are not currently used.
                    n=struct.unpack("!I",self.exact(self.input,4))[0]
                    if n>0 and n<=65536: self.exact(self.input,n)
                else:
                    raise ValueError("Unexpected input-channel packet")

        except Exception as e:
            if self.running:
                print("Target clipboard/input receive:",e)
                self.root.after(0,self.disconnect,"Connection lost: "+str(e))

    def show(self,img):
        if not self.running:return
        self.sw,self.sh=img.size; cw=max(1,self.canvas.winfo_width()); ch=max(1,self.canvas.winfo_height())
        scale=min(cw/img.width,ch/img.height); size=(max(1,int(img.width*scale)),max(1,int(img.height*scale)))
        if size!=img.size: img=img.resize(size,Image.Resampling.BILINEAR)
        self.photo=ImageTk.PhotoImage(img); self.canvas.delete("all"); self.dx=(cw-size[0])//2; self.dy=(ch-size[1])//2; self.dw,self.dh=size
        self.canvas.create_image(self.dx,self.dy,anchor="nw",image=self.photo)

    def focus_remote(self, e=None):
        # Keyboard shortcuts should go to the remote PC only when the
        # remote screen has focus. This prevents Ctrl+C/V in the login
        # fields from being sent to the Target PC.
        self.canvas.focus_set()
        return None

    def coords(self,e):
        if not self.dw or not self.dh:return None
        x=(e.x-self.dx)*self.sw/self.dw; y=(e.y-self.dy)*self.sh/self.dh
        if x<0 or y<0 or x>=self.sw or y>=self.sh:return None
        return int(x),int(y)

    def send(self,t,**kw):
        if not self.running:return
        try:
            d=json.dumps({"type":t,**kw},separators=(",",":")).encode()
            with self.input_send_lock:
                self.input.sendall(b"I"+struct.pack("!I",len(d))+d)
        except Exception as e:self.disconnect("Input lost: "+str(e))

    def move(self,e):
        p=self.coords(e)
        if p:self.send("mouse_move",x=p[0],y=p[1])

    def mouse(self,e,a,b):
        p=self.coords(e)
        if p:self.send("mouse_button",x=p[0],y=p[1],button=b,action=a)

    def wheel(self,e):self.send("scroll",delta=1 if e.delta>0 else -1)
    def key(self,e):
        # Only forward keyboard input when the remote screen has focus.
        # Otherwise typing in IP/username/password fields remains local.
        if self.root.focus_get() is not self.canvas:
            return

        keymap = {
            "Control_L": "ctrl",
            "Control_R": "ctrl",
            "Shift_L": "shift",
            "Shift_R": "shift",
            "Alt_L": "alt",
            "Alt_R": "alt",
            "Win_L": "win",
            "Win_R": "win",
            "Return": "enter",
            "Escape": "esc",
            "BackSpace": "backspace",
            "Delete": "delete",
            "Insert": "insert",
            "Prior": "pageup",
            "Next": "pagedown",
            "Left": "left",
            "Right": "right",
            "Up": "up",
            "Down": "down",
            "Home": "home",
            "End": "end",
            "Tab": "tab",
            "space": "space",
        }

        key = keymap.get(e.keysym, e.keysym.lower())

        allowed = {
            "ctrl", "shift", "alt", "win", "enter", "esc", "escape",
            "backspace", "delete", "insert", "pageup", "pagedown",
            "left", "right", "up", "down", "home", "end", "tab", "space"
        } | {f"f{i}" for i in range(1, 13)}

        if len(key) == 1 or key in allowed:
            self.send(
                "key",
                action="key_down" if e.type == tk.EventType.KeyPress else "key_up",
                key=key
            )


    def clipboard_monitor(self):
        while self.running:
            try:
                kind,data=self.clip.clipboard_changed()
                if kind and not self.clip.clip_applying_remote:
                    if kind=="text":
                        payload=data.encode("utf-8")
                        if len(payload)<=CLIP_MAX_MEMORY:self.send_clipboard_bytes("text",payload)
                    elif kind=="image":
                        if len(data)<=CLIP_MAX_MEMORY:self.send_clipboard_bytes("image",data)
                    elif kind=="files":
                        archive=self.clip.make_archive(data)
                        if archive:
                            try:self.send_clipboard_file(archive)
                            finally:
                                try:os.remove(archive)
                                except OSError:pass
            except Exception as e: print("Clipboard monitor error:",e)
            time.sleep(0.075)

    def send_clipboard_bytes(self,kind,data):
        with self.input_send_lock:
            self.input.sendall(self.clip.build_clip_header(kind,len(data)))
            view=memoryview(data)
            while view:
                sent=self.input.send(view[:CLIP_CHUNK])
                if sent<=0: raise ConnectionError("Clipboard connection closed")
                view=view[sent:]

    def send_clipboard_file(self,archive):
        size=os.path.getsize(archive)
        with self.input_send_lock:
            self.input.sendall(self.clip.build_clip_header("files",size))
            with open(archive,"rb") as f:
                while True:
                    chunk=f.read(CLIP_CHUNK)
                    if not chunk:break
                    self.input.sendall(chunk)

    def disconnect(self,msg="Disconnected"):
        self.running=False
        a,b=self.screen,self.input; self.screen=self.input=None
        for s in (a,b):
            try:
                if s:s.shutdown(socket.SHUT_RDWR)
            except:pass
            try:
                if s:s.close()
            except:pass
        self.photo=None; self.canvas.delete("all"); self.cb.config(state="normal"); self.db.config(state="disabled"); self.status.set(msg)

    def reconnect(self):
        self.disconnect("Reconnecting..."); self.root.after(300,self.connect)

    def close(self):
        self.disconnect(); self.root.destroy()

    def run(self): self.root.mainloop()

if __name__=="__main__": Client().run()
