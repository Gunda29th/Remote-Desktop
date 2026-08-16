import hashlib, hmac, io, json, os, socket, struct, threading, time, uuid
from pathlib import Path

import mss, pyautogui
from PIL import Image
from clipboard_bridge import ClipboardBridge, CLIP_MAGIC, CLIP_MAX_MEMORY, CLIP_CHUNK

SCREEN_PORT=5051
INPUT_PORT=5052
MAGIC=b"LRD3"
AUTH_MAGIC=b"AUTH"
FPS=18
JPEG_QUALITY=45
MAX_INPUT=64*1024
APPDIR=Path(os.environ.get("APPDATA",str(Path.home())))/"RemoteDesk"
CRED=APPDIR/"credentials.json"
STATUS=Path(__file__).resolve().parent/"remote_status.txt"

running=True
connected=False
screen_conn=None
input_conn=None
session_lock=threading.Lock()
stop_event=threading.Event()
pending={}
pending_lock=threading.Lock()
clip=ClipboardBridge()

def status(a,b):
    try: STATUS.write_text(a+"|"+b,encoding="utf-8")
    except: pass
    print(a+" - "+b)

def exact(c,n):
    d=bytearray()
    while len(d)<n:
        x=c.recv(min(1024*1024,n-len(d)))
        if not x: raise ConnectionError("Connection closed")
        d.extend(x)
    return bytes(d)

def verify(u,p):
    try:
        o=json.loads(CRED.read_text(encoding="utf-8"))
        if u!=o["username"]: return False
        actual=hashlib.pbkdf2_hmac("sha256",p.encode(),bytes.fromhex(o["salt"]),int(o["iterations"])).hex()
        return hmac.compare_digest(actual,o["hash"])
    except Exception as e:
        print("Credential error:",e); return False

def disconnect():
    global connected,screen_conn,input_conn
    with session_lock:
        was=connected; connected=False
        a,b=screen_conn,input_conn
        screen_conn=input_conn=None
        stop_event.set()
    for c in (a,b):
        try:
            if c:c.shutdown(socket.SHUT_RDWR)
        except:pass
        try:
            if c:c.close()
        except:pass
    if was:print("Remote session ended.")
    if running:status("Disconnected","Waiting for Main PC")

def capture(screen):
    try:
        with mss.MSS() as sct:
            mon=sct.monitors[1]; delay=1/FPS
            while running and not stop_event.is_set():
                t=time.monotonic(); raw=sct.grab(mon)
                img=Image.frombytes("RGB",raw.size,raw.rgb)
                buf=io.BytesIO(); img.save(buf,"JPEG",quality=JPEG_QUALITY)
                data=buf.getvalue()
                screen.sendall(b"S"+struct.pack("!I",len(data))+data)
                time.sleep(max(0,delay-(time.monotonic()-t)))
    except Exception as e:print("Screen connection ended:",e)

def handle_input(o):
    t=o.get("type")
    if t=="mouse_move":pyautogui.moveTo(int(o["x"]),int(o["y"]))
    elif t=="mouse_button":
        b={1:"left",2:"middle",3:"right"}.get(int(o["button"]))
        if b:
            pyautogui.moveTo(int(o["x"]),int(o["y"]))
            if o.get("action")=="down":pyautogui.mouseDown(button=b)
            elif o.get("action")=="up":pyautogui.mouseUp(button=b)
    elif t=="scroll":pyautogui.scroll(int(o.get("delta",0)))
    elif t=="key":
        k=str(o.get("key","")).lower()
        allowed={"enter","backspace","tab","escape","esc","space","shift","ctrl","alt","win","up","down","left","right","home","end","pageup","pagedown","delete","insert","capslock","printscreen"}|{f"f{i}" for i in range(1,13)}
        if len(k)==1 or k in allowed:
            if o.get("action")=="key_down":pyautogui.keyDown(k)
            elif o.get("action")=="key_up":pyautogui.keyUp(k)

def receive_clip(conn,kind,size):
    if kind in (b"T",b"I"):
        if size>CLIP_MAX_MEMORY:raise ValueError("Clipboard payload too large")
        data=exact(conn,size)
        clip.apply_remote_clipboard("text" if kind==b"T" else "image",
                                    data.decode("utf-8") if kind==b"T" else data)
    elif kind==b"F":
        archive=os.path.join(clip.clip_temp_root,"recv_"+uuid.uuid4().hex+".zip")
        remaining=size
        try:
            with open(archive,"wb") as f:
                while remaining:
                    chunk=conn.recv(min(CLIP_CHUNK,remaining))
                    if not chunk:raise ConnectionError("File transfer interrupted")
                    f.write(chunk);remaining-=len(chunk)
            clip.clip_applying_remote=True
            try:
                destination=os.path.join(clip.clip_temp_root,"files_"+uuid.uuid4().hex)
                os.makedirs(destination,exist_ok=True)
                import zipfile
                with zipfile.ZipFile(archive,"r") as zf:
                    base=os.path.abspath(destination)
                    for m in zf.infolist():
                        dst=os.path.abspath(os.path.join(destination,m.filename))
                        if os.path.commonpath([base,dst])!=base:raise ValueError("Unsafe archive path")
                    zf.extractall(destination)
                paths=[os.path.join(destination,n) for n in os.listdir(destination)]
                if clip.set_files(paths):
                    clip.clip_last_signature=clip.signature("files",paths)
                    clip.clip_last_remote_apply=time.monotonic()
                print("Files/folders received from Main PC.")
            finally:clip.clip_applying_remote=False
        finally:
            try:os.remove(archive)
            except OSError:pass
    else:raise ValueError("Unknown clipboard packet type")

def send_clipboard_bytes(conn,kind,data):
    conn.sendall(clip.build_clip_header(kind,len(data)))
    view=memoryview(data)
    while view:
        sent=conn.send(view[:CLIP_CHUNK])
        if sent<=0:raise ConnectionError("Clipboard connection closed")
        view=view[sent:]

def send_clipboard_file(conn,archive):
    size=os.path.getsize(archive)
    conn.sendall(clip.build_clip_header("files",size))
    with open(archive,"rb") as f:
        while True:
            chunk=f.read(CLIP_CHUNK)
            if not chunk:break
            conn.sendall(chunk)

def target_clipboard_monitor(conn):
    # Target -> Main direction. This runs independently from the input
    # event loop and uses the same authenticated TCP connection.
    while running and not stop_event.is_set():
        try:
            kind,data=clip.clipboard_changed()
            if kind and not clip.clip_applying_remote:
                if kind=="text":
                    payload=data.encode("utf-8")
                    if len(payload)<=CLIP_MAX_MEMORY:send_clipboard_bytes(conn,"text",payload)
                elif kind=="image":
                    if len(data)<=CLIP_MAX_MEMORY:send_clipboard_bytes(conn,"image",data)
                elif kind=="files":
                    archive=clip.make_archive(data)
                    if archive:
                        try:send_clipboard_file(conn,archive)
                        finally:
                            try:os.remove(archive)
                            except OSError:pass
        except Exception as e:
            if running and not stop_event.is_set():print("Target clipboard monitor:",e)
            break
        time.sleep(0.075)

def session(screen,inp,client):
    stop_event.clear()
    threading.Thread(target=capture,args=(screen,),daemon=True).start()
    clip.clipboard_monitor_prepare()
    threading.Thread(target=target_clipboard_monitor,args=(inp,),daemon=True).start()
    status("Connected","Main PC: "+client)
    try:
        while running and not stop_event.is_set():
            inp.settimeout(0.2)
            try:first=inp.recv(1)
            except socket.timeout:continue
            if not first:break
            if first==b"I":
                n=struct.unpack("!I",exact(inp,4))[0]
                if n<=0 or n>MAX_INPUT:raise ValueError("Invalid input size")
                handle_input(json.loads(exact(inp,n).decode("utf-8")))
            elif first==b"C":
                if exact(inp,4)!=CLIP_MAGIC:raise ValueError("Bad clipboard magic")
                kind=exact(inp,1);size=struct.unpack("!Q",exact(inp,8))[0]
                exact(inp,16);exact(inp,8)
                receive_clip(inp,kind,size)
            else:
                raise ValueError("Bad input/clipboard packet")
    except Exception as e:print("Input/session ended:",e)
    disconnect()

def accept(listener,channel):
    global connected,screen_conn,input_conn
    while running:
        try:
            c,addr=listener.accept()
            try:
                if exact(c,4)!=MAGIC:raise ValueError("Bad magic")
                if exact(c,1)!=channel:raise ValueError("Bad channel")
                sid=exact(c,16)
                if channel==b"I":
                    if exact(c,4)!=AUTH_MAGIC:raise ValueError("Missing authentication")
                    n=struct.unpack("!I",exact(c,4))[0]
                    if n<=0 or n>8192:raise ValueError("Bad auth size")
                    auth=json.loads(exact(c,n).decode())
                    if not verify(str(auth.get("username","")),str(auth.get("password",""))):
                        c.sendall(b"FAIL");print("Authentication failed from",addr[0]);c.close();continue
                    c.sendall(b"OKAY")
                with pending_lock:
                    p=pending.setdefault(sid,{})
                    p[channel]=(c,addr)
                    if b"S" in p and b"I" in p:
                        screen,saddr=p[b"S"];inp,_=p[b"I"];del pending[sid]
                    else:screen=inp=None
                if screen is not None:
                    with session_lock:
                        if connected:screen.close();inp.close();continue
                        screen_conn=screen;input_conn=inp;connected=True
                    print("Authenticated remote session from",saddr)
                    threading.Thread(target=session,args=(screen,inp,f"{saddr[0]}:{saddr[1]}"),daemon=True).start()
            except Exception as e:
                print("Handshake error:",e)
                try:c.close()
                except:pass
        except OSError:break
        except Exception as e:print("Listener error:",e)

def main():
    global running
    if not CRED.exists():status("Setup required","Run RemoteDesk first");return
    pyautogui.PAUSE=0;pyautogui.FAILSAFE=False
    sl=socket.socket();sl.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sl.bind(("0.0.0.0",SCREEN_PORT));sl.listen(8)
    il=socket.socket();il.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);il.bind(("0.0.0.0",INPUT_PORT));il.listen(8)
    threading.Thread(target=accept,args=(sl,b"S"),daemon=True).start()
    threading.Thread(target=accept,args=(il,b"I"),daemon=True).start()
    status("Disconnected","Waiting for Main PC")
    print("RemoteDesk Target Server")
    print("Screen server listening on port 5051")
    print("Input + clipboard server listening on port 5052")
    print("Clipboard is bidirectional: Main <-> Target")
    print("Waiting for Main PC...")
    try:
        while running:time.sleep(1)
    finally:
        disconnect()
        try:sl.close();il.close()
        except:pass

if __name__=="__main__":main()
