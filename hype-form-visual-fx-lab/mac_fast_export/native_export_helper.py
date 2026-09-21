#!/usr/bin/env python3
"""
HYPE FORM / Visual FX Lab — Native Fast Export Helper

Loopback-only HTTP bridge that accepts raw RGBA frames from the browser and pipes
those frames into native FFmpeg. On macOS it prefers h264_videotoolbox; elsewhere
it falls back to libx264 for development/testing.

Security model:
- binds to 127.0.0.1 only
- accepts browser origins only from this app's local server, file:// (Origin: null),
  or the shingoviva GitHub Pages origin
- mutating endpoints require the random token returned by /health
- output paths are chosen by the helper, never supplied by the browser
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = int(os.environ.get("HYPE_FORM_HELPER_PORT", "47832"))
HELPER_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / "index.html"
TOKEN = secrets.token_urlsafe(24)

MAX_WIDTH = 4096
MAX_HEIGHT = 4096
MAX_FPS = 120.0
MAX_FRAMES = 7200
MAX_FRAME_BYTES = MAX_WIDTH * MAX_HEIGHT * 4

ALLOWED_ORIGINS = {
    "null",  # file:// pages
    "https://shingoviva.github.io",
}
LOCAL_ORIGIN_RE = re.compile(r"^http://(?:127\.0\.0\.1|localhost)(?::\d+)?$")


def _which_ffmpeg() -> str | None:
    candidates = [
        os.environ.get("FFMPEG_PATH", ""),
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        shutil.which("ffmpeg") or "",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return item
    return None


def _encoder_info(ffmpeg: str | None) -> dict:
    if not ffmpeg:
        return {"available": False, "encoder": None, "videotoolbox": False, "ffmpeg": None}
    try:
        p = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=8,
            check=False,
        )
        text = p.stdout or ""
        vt = "h264_videotoolbox" in text
        x264 = "libx264" in text
        encoder = "h264_videotoolbox" if vt else ("libx264" if x264 else None)
        return {"available": bool(encoder), "encoder": encoder, "videotoolbox": vt, "ffmpeg": ffmpeg}
    except Exception:
        return {"available": False, "encoder": None, "videotoolbox": False, "ffmpeg": ffmpeg}


FFMPEG = _which_ffmpeg()
ENCODER = _encoder_info(FFMPEG)


def _safe_filename(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name or "").strip())
    stem = stem.strip(".-")[:120] or "hype-form-motion"
    if not stem.lower().endswith(".mp4"):
        stem += ".mp4"
    return stem


def _export_dir() -> Path:
    override = os.environ.get("HYPE_FORM_EXPORT_DIR")
    base = Path(override).expanduser() if override else (Path.home() / "Downloads" / "HYPE_FORM_EXPORTS")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _unique_output_path(filename: str) -> Path:
    base = _export_dir() / _safe_filename(filename)
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    for n in range(2, 1000):
        candidate = base.with_name(f"{stem}-{n}{suffix}")
        if not candidate.exists():
            return candidate
    return base.with_name(f"{stem}-{int(time.time())}{suffix}")


def _bitrate_for(width: int, height: int, fps: float, quality: str) -> int:
    q = {"medium": 0.12, "high": 0.20, "very-high": 0.32}.get(quality, 0.20)
    bits = int(width * height * fps * q)
    return max(4_000_000, min(bits, 60_000_000))


def _ffmpeg_cmd(width: int, height: int, fps: float, quality: str, output: Path) -> list[str]:
    if not FFMPEG or not ENCODER.get("encoder"):
        raise RuntimeError("FFmpeg with H.264 encoding support was not found.")
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-video_size", f"{width}x{height}",
        "-framerate", f"{fps:.6f}",
        "-i", "pipe:0",
        "-an",
    ]
    encoder = ENCODER["encoder"]
    if encoder == "h264_videotoolbox":
        bitrate = _bitrate_for(width, height, fps, quality)
        maxrate = int(bitrate * 1.45)
        bufsize = int(bitrate * 2.0)
        # FFmpeg's VideoToolbox encoder exposes realtime/prio_speed. Native Fast
        # intentionally favors throughput; Very High keeps more quality headroom.
        prio_speed = "0" if quality == "very-high" else "1"
        realtime = "0" if quality == "very-high" else "1"
        cmd += [
            "-c:v", "h264_videotoolbox",
            "-allow_sw", "1",
            "-realtime", realtime,
            "-prio_speed", prio_speed,
            "-profile:v", "high",
            "-b:v", str(bitrate),
            "-maxrate", str(maxrate),
            "-bufsize", str(bufsize),
            "-g", str(max(1, round(fps * 2))),
        ]
    else:
        crf = {"medium": "23", "high": "19", "very-high": "16"}.get(quality, "19")
        preset = "veryfast" if quality != "very-high" else "fast"
        cmd += ["-c:v", "libx264", "-preset", preset, "-crf", crf, "-profile:v", "high"]
    cmd += [
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-movflags", "+faststart",
        str(output),
    ]
    return cmd


@dataclass
class ExportSession:
    id: str
    width: int
    height: int
    fps: float
    expected_frames: int
    quality: str
    output_path: Path
    process: subprocess.Popen
    started_at: float = field(default_factory=time.perf_counter)
    frame_count: int = 0
    bytes_received: int = 0
    last_frame_ms: float = 0.0
    stderr_tail: str = ""
    closed: bool = False

    @property
    def frame_bytes(self) -> int:
        return self.width * self.height * 4


SESSIONS: dict[str, ExportSession] = {}
SESSIONS_LOCK = threading.Lock()


def _allowed_origin(origin: str | None) -> bool:
    if not origin:
        return True  # curl / local diagnostics
    return origin in ALLOWED_ORIGINS or bool(LOCAL_ORIGIN_RE.match(origin))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "HypeFormFastExport/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write("[helper] " + (fmt % args) + "\n")
        sys.stdout.flush()

    def _cors(self) -> bool:
        origin = self.headers.get("Origin")
        if not _allowed_origin(origin):
            return False
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Hype-Token, X-Hype-Session, X-Hype-Frame")
        self.send_header("Access-Control-Max-Age", "600")
        return True

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        if not self._cors():
            self.end_headers()
            return
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self) -> bool:
        if self.headers.get("X-Hype-Token") != TOKEN:
            self._json(403, {"ok": False, "error": "Invalid helper token."})
            return False
        return True

    def _read_json(self, max_bytes: int = 64 * 1024) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > max_bytes:
            raise ValueError("Invalid JSON body size.")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin")
        if not _allowed_origin(origin):
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {
                "ok": bool(ENCODER.get("available")),
                "helperVersion": HELPER_VERSION,
                "ffmpeg": FFMPEG,
                "encoder": ENCODER.get("encoder"),
                "videoToolbox": bool(ENCODER.get("videotoolbox")),
                "token": TOKEN,
                "exportDir": str(_export_dir()),
                "appRoot": str(ROOT),
            })
            return
        if parsed.path in ("/", "/index.html"):
            if not INDEX_FILE.exists():
                self._json(404, {"ok": False, "error": "index.html not found next to helper."})
                return
            body = INDEX_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._json(404, {"ok": False, "error": "Not found."})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/start", "/frame", "/finish", "/cancel", "/reveal"}:
            self._json(404, {"ok": False, "error": "Not found."})
            return
        if not self._auth():
            return
        try:
            if parsed.path == "/start":
                self._start()
            elif parsed.path == "/frame":
                self._frame()
            elif parsed.path == "/finish":
                self._finish()
            elif parsed.path == "/cancel":
                self._cancel()
            elif parsed.path == "/reveal":
                self._reveal()
        except BrokenPipeError:
            pass
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _start(self) -> None:
        if not ENCODER.get("available"):
            self._json(503, {"ok": False, "error": "FFmpeg H.264 encoder is unavailable."})
            return
        data = self._read_json()
        width = int(data.get("width", 0))
        height = int(data.get("height", 0))
        fps = float(data.get("fps", 0))
        expected = int(data.get("frames", 0))
        quality = str(data.get("quality", "high"))
        if width <= 0 or height <= 0 or width > MAX_WIDTH or height > MAX_HEIGHT or width % 2 or height % 2:
            raise ValueError("Invalid export dimensions; dimensions must be even and <= 4096.")
        if fps <= 0 or fps > MAX_FPS:
            raise ValueError("Invalid FPS.")
        if expected <= 0 or expected > MAX_FRAMES:
            raise ValueError("Invalid frame count.")
        if quality not in {"medium", "high", "very-high"}:
            quality = "high"
        filename = _safe_filename(data.get("filename") or f"hype-form-motion-{int(time.time())}.mp4")
        output = _unique_output_path(filename)
        sid = uuid.uuid4().hex
        cmd = _ffmpeg_cmd(width, height, fps, quality, output)
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        sess = ExportSession(sid, width, height, fps, expected, quality, output, proc)
        with SESSIONS_LOCK:
            SESSIONS[sid] = sess
        self._json(200, {
            "ok": True,
            "session": sid,
            "encoder": ENCODER.get("encoder"),
            "videoToolbox": bool(ENCODER.get("videotoolbox")),
            "frameBytes": sess.frame_bytes,
            "outputPath": str(output),
        })

    def _get_session(self) -> ExportSession:
        sid = self.headers.get("X-Hype-Session", "")
        if not sid:
            try:
                data = self._read_json()
                sid = str(data.get("session", ""))
            except Exception:
                sid = ""
        with SESSIONS_LOCK:
            sess = SESSIONS.get(sid)
        if not sess:
            raise ValueError("Unknown native export session.")
        return sess

    def _frame(self) -> None:
        sid = self.headers.get("X-Hype-Session", "")
        frame_index = int(self.headers.get("X-Hype-Frame", "-1"))
        with SESSIONS_LOCK:
            sess = SESSIONS.get(sid)
        if not sess:
            raise ValueError("Unknown native export session.")
        if sess.closed:
            raise ValueError("Export session is already closed.")
        if frame_index != sess.frame_count:
            raise ValueError(f"Frame order mismatch: expected {sess.frame_count}, got {frame_index}.")
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length != sess.frame_bytes or length > MAX_FRAME_BYTES:
            raise ValueError(f"Invalid frame byte count: expected {sess.frame_bytes}, got {length}.")
        if not sess.process.stdin:
            raise RuntimeError("FFmpeg stdin is unavailable.")
        started = time.perf_counter()
        remaining = length
        while remaining:
            chunk = self.rfile.read(min(1024 * 1024, remaining))
            if not chunk:
                raise RuntimeError("Frame upload ended early.")
            sess.process.stdin.write(chunk)
            remaining -= len(chunk)
        sess.process.stdin.flush()
        sess.last_frame_ms = (time.perf_counter() - started) * 1000.0
        sess.frame_count += 1
        sess.bytes_received += length
        if sess.process.poll() is not None:
            err = (sess.process.stderr.read() if sess.process.stderr else b"").decode("utf-8", "replace")[-4000:]
            sess.stderr_tail = err
            raise RuntimeError(f"FFmpeg stopped during frame ingest: {err.strip() or 'unknown encoder error'}")
        self._json(200, {
            "ok": True,
            "frame": frame_index,
            "received": sess.frame_count,
            "expected": sess.expected_frames,
            "pipeMs": round(sess.last_frame_ms, 3),
        })

    def _finish(self) -> None:
        data = self._read_json()
        sid = str(data.get("session", ""))
        with SESSIONS_LOCK:
            sess = SESSIONS.get(sid)
        if not sess:
            raise ValueError("Unknown native export session.")
        if sess.closed:
            raise ValueError("Export session is already closed.")
        if sess.frame_count != sess.expected_frames:
            raise ValueError(f"Frame count mismatch: received {sess.frame_count}, expected {sess.expected_frames}.")
        if sess.process.stdin:
            sess.process.stdin.close()
        try:
            code = sess.process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            sess.process.kill()
            code = sess.process.wait(timeout=5)
        stderr = (sess.process.stderr.read() if sess.process.stderr else b"").decode("utf-8", "replace")
        sess.stderr_tail = stderr[-4000:]
        sess.closed = True
        elapsed = time.perf_counter() - sess.started_at
        if code != 0:
            raise RuntimeError(f"FFmpeg failed ({code}): {sess.stderr_tail.strip() or 'unknown error'}")
        size = sess.output_path.stat().st_size if sess.output_path.exists() else 0
        self._json(200, {
            "ok": True,
            "session": sid,
            "frames": sess.frame_count,
            "bytesReceived": sess.bytes_received,
            "elapsedSeconds": round(elapsed, 3),
            "encoder": ENCODER.get("encoder"),
            "videoToolbox": bool(ENCODER.get("videotoolbox")),
            "outputPath": str(sess.output_path),
            "filename": sess.output_path.name,
            "fileSize": size,
        })

    def _cancel(self) -> None:
        data = self._read_json()
        sid = str(data.get("session", ""))
        with SESSIONS_LOCK:
            sess = SESSIONS.get(sid)
        if sess and not sess.closed:
            try:
                if sess.process.stdin:
                    sess.process.stdin.close()
            except Exception:
                pass
            try:
                sess.process.terminate()
                sess.process.wait(timeout=3)
            except Exception:
                try:
                    sess.process.kill()
                except Exception:
                    pass
            sess.closed = True
            try:
                if sess.output_path.exists():
                    sess.output_path.unlink()
            except Exception:
                pass
        self._json(200, {"ok": True, "session": sid})

    def _reveal(self) -> None:
        data = self._read_json()
        sid = str(data.get("session", ""))
        with SESSIONS_LOCK:
            sess = SESSIONS.get(sid)
        if not sess or not sess.output_path.exists():
            raise ValueError("Export file is unavailable.")
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(sess.output_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._json(200, {"ok": True})
        else:
            self._json(200, {"ok": False, "error": "Reveal is available on macOS only.", "outputPath": str(sess.output_path)})


def main() -> int:
    print("HYPE FORM / Visual FX Lab — Mac Fast Export Helper")
    print(f"Helper: v{HELPER_VERSION}")
    print(f"App:    {INDEX_FILE}")
    if FFMPEG:
        print(f"FFmpeg: {FFMPEG}")
    else:
        print("FFmpeg: NOT FOUND")
    print(f"Encoder: {ENCODER.get('encoder') or 'NOT FOUND'}")
    if sys.platform == "darwin":
        print(f"VideoToolbox: {'YES' if ENCODER.get('videotoolbox') else 'NO'}")
    if not ENCODER.get("available"):
        print("\nFFmpeg with H.264 support is required.")
        print("Homebrew: brew install ffmpeg")
        return 2
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"\nREADY: http://{HOST}:{PORT}/")
    print(f"Exports: {_export_dir()}")
    print("Keep this Terminal window open while using Mac Fast Export.\n")
    if os.environ.get("HYPE_FORM_NO_BROWSER") != "1":
        threading.Timer(0.65, lambda: webbrowser.open(f"http://{HOST}:{PORT}/")).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nStopping helper…")
    finally:
        server.server_close()
        with SESSIONS_LOCK:
            sessions = list(SESSIONS.values())
        for sess in sessions:
            if sess.process.poll() is None:
                try:
                    sess.process.terminate()
                except Exception:
                    pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())