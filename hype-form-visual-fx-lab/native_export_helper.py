#!/usr/bin/env python3
"""HYPE FORM / Visual FX Lab v28.2.35 Mac Native Export Helper.

Runs only on 127.0.0.1. Serves the app and accepts raw RGBA frames from the
locked browser renderer, piping them to native FFmpeg. On macOS it prefers
h264_videotoolbox; otherwise it falls back to libx264 for diagnostics.
"""
from __future__ import annotations
import argparse, json, os, secrets, shutil, subprocess, sys, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

HOST="127.0.0.1"
PORT=48735
ROOT=Path(__file__).resolve().parent
OUT_DIR=Path.home()/"Downloads"/"HYPE_FORM_Exports"
SESSIONS={}
LOCK=threading.RLock()

def ffmpeg_path():
    return shutil.which("ffmpeg")

def encoder_info(ffmpeg):
    if not ffmpeg:
        return None
    try:
        p=subprocess.run([ffmpeg,"-hide_banner","-encoders"],capture_output=True,text=True,timeout=5)
        txt=(p.stdout or "")+(p.stderr or "")
    except Exception:
        return None
    if sys.platform=="darwin" and "h264_videotoolbox" in txt:
        return "h264_videotoolbox"
    if "libx264" in txt:
        return "libx264"
    if "h264_videotoolbox" in txt:
        return "h264_videotoolbox"
    return None

def safe_filename(name):
    base=Path(str(name or "hype-form-motion.mp4")).name
    if not base.lower().endswith(".mp4"):
        base += ".mp4"
    return "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in base)[:160]

def ffmpeg_cmd(ffmpeg,encoder,w,h,fps,bitrate,out_path):
    cmd=[ffmpeg,"-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgba","-s:v",f"{w}x{h}",
         "-r",str(fps),"-i","pipe:0","-an","-c:v",encoder]
    if encoder=="h264_videotoolbox":
        cmd += ["-b:v",f"{bitrate:.2f}M","-allow_sw","1","-realtime","0"]
    else:
        cmd += ["-preset","veryfast","-crf","18","-b:v",f"{bitrate:.2f}M"]
    cmd += ["-pix_fmt","yuv420p","-movflags","+faststart",str(out_path)]
    return cmd

class Handler(SimpleHTTPRequestHandler):
    server_version="HYPEFORMNative/28.2.35"

    def end_headers(self):
        self.send_header("Cache-Control","no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stdout.write("[HYPE FORM] "+fmt%args+"\n")

    def _json(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def _read_json(self):
        n=int(self.headers.get("Content-Length","0") or "0")
        if n>64*1024: raise ValueError("JSON body too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if urlparse(self.path).path=="/v1/health":
            ff=ffmpeg_path(); enc=encoder_info(ff)
            return self._json(200,{"ok":True,"version":"v28.2.35","ffmpeg":bool(ff),"ffmpeg_path":ff or "","encoder":enc or "","platform":sys.platform})
        return super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        try:
            if path=="/v1/export/start": return self.start_export()
            if path=="/v1/export/frame": return self.push_frame()
            if path=="/v1/export/finish": return self.finish_export()
            if path=="/v1/export/cancel": return self.cancel_export()
            return self._json(404,{"error":"not found"})
        except Exception as e:
            return self._json(500,{"error":str(e)})

    def start_export(self):
        meta=self._read_json()
        ff=ffmpeg_path(); enc=encoder_info(ff)
        if not ff: return self._json(503,{"error":"FFmpeg not found. Install with: brew install ffmpeg"})
        if not enc: return self._json(503,{"error":"No H.264 encoder found in FFmpeg."})
        w=int(meta.get("width",0)); h=int(meta.get("height",0)); fps=float(meta.get("fps",30)); total=int(meta.get("total_frames",0)); bitrate=float(meta.get("bitrate_mbps",18))
        if w<2 or h<2 or w>8192 or h>8192 or (w&1) or (h&1): return self._json(400,{"error":"invalid even dimensions"})
        if not (1<=fps<=120) or not (1<=total<=7200): return self._json(400,{"error":"invalid fps/frame count"})
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        sid=secrets.token_urlsafe(18); name=safe_filename(meta.get("filename"))
        tmp=OUT_DIR/(f".{sid}.partial.mp4"); final=OUT_DIR/name
        if final.exists():
            final=OUT_DIR/f"{final.stem}-{int(time.time())}{final.suffix}"
        cmd=ffmpeg_cmd(ff,enc,w,h,fps,bitrate,tmp)
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        sess={"id":sid,"proc":proc,"tmp":tmp,"final":final,"w":w,"h":h,"fps":fps,"total":total,"next":0,"bytes":0,"started":time.perf_counter(),"encoder":enc}
        with LOCK: SESSIONS[sid]=sess
        return self._json(200,{"ok":True,"session_id":sid,"encoder":enc,"output":str(final),"width":w,"height":h,"fps":fps,"total_frames":total})

    def push_frame(self):
        sid=self.headers.get("X-Hype-Session",""); idx=int(self.headers.get("X-Hype-Frame","-1"))
        with LOCK: sess=SESSIONS.get(sid)
        if not sess: return self._json(404,{"error":"unknown export session"})
        if idx!=sess["next"]: return self._json(409,{"error":f"frame order mismatch: expected {sess['next']} got {idx}"})
        expected=sess["w"]*sess["h"]*4
        n=int(self.headers.get("Content-Length","0") or "0")
        if n!=expected: return self._json(400,{"error":f"raw frame size mismatch: expected {expected}, got {n}"})
        data=self.rfile.read(n)
        if len(data)!=expected: return self._json(400,{"error":"incomplete frame body"})
        proc=sess["proc"]
        if proc.poll() is not None:
            err=(proc.stderr.read() or b"").decode("utf-8","replace")
            return self._json(500,{"error":"FFmpeg exited early: "+err[-1200:]})
        proc.stdin.write(data); proc.stdin.flush()
        sess["next"]+=1; sess["bytes"]+=len(data)
        return self._json(200,{"ok":True,"frame":idx})

    def finish_export(self):
        meta=self._read_json(); sid=str(meta.get("session_id",""))
        with LOCK: sess=SESSIONS.pop(sid,None)
        if not sess: return self._json(404,{"error":"unknown export session"})
        proc=sess["proc"]
        try:
            proc.stdin.close(); rc=proc.wait(timeout=180)
        except Exception:
            proc.kill(); rc=proc.wait()
        err=(proc.stderr.read() or b"").decode("utf-8","replace")
        if rc!=0:
            try: sess["tmp"].unlink(missing_ok=True)
            except Exception: pass
            return self._json(500,{"error":"FFmpeg failed: "+err[-1600:]})
        os.replace(sess["tmp"],sess["final"])
        elapsed=time.perf_counter()-sess["started"]
        return self._json(200,{"ok":True,"path":str(sess["final"]),"encoder":sess["encoder"],"frames":sess["next"],"bytes":sess["bytes"],"elapsed_sec":round(elapsed,3)})

    def cancel_export(self):
        meta=self._read_json(); sid=str(meta.get("session_id",""))
        with LOCK: sess=SESSIONS.pop(sid,None)
        if sess:
            proc=sess["proc"]
            try:
                if proc.stdin: proc.stdin.close()
            except Exception: pass
            if proc.poll() is None: proc.kill()
            try: sess["tmp"].unlink(missing_ok=True)
            except Exception: pass
        return self._json(200,{"ok":True,"cancelled":bool(sess)})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=PORT)
    args=ap.parse_args()
    os.chdir(ROOT)
    ff=ffmpeg_path(); enc=encoder_info(ff)
    print(f"HYPE FORM Native Export Helper v28.2.35")
    print(f"App: http://{HOST}:{args.port}/")
    print(f"FFmpeg: {ff or 'NOT FOUND'}")
    print(f"H.264 encoder: {enc or 'NOT FOUND'}")
    if sys.platform=="darwin" and enc!="h264_videotoolbox":
        print("WARNING: h264_videotoolbox not detected; native export will use software fallback if available.")
    httpd=ThreadingHTTPServer((HOST,args.port),Handler)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        with LOCK:
            for sess in list(SESSIONS.values()):
                try: sess["proc"].kill()
                except Exception: pass
        httpd.server_close()

if __name__=="__main__":
    main()
