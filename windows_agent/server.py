"""Minimal authenticated Windows LAN agent. Python 3.10+."""
import ctypes
import hmac
import json
import os
import re
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get("DESKTOP_CONTROL_TOKEN", "")
HOST = os.environ.get("DESKTOP_CONTROL_HOST", "127.0.0.1")
PORT = int(os.environ.get("DESKTOP_CONTROL_PORT", "8765"))
ALLOW_SHUTDOWN = os.environ.get("DESKTOP_CONTROL_ALLOW_SHUTDOWN") == "1"

def valid_mac(mac):
    return isinstance(mac, str) and re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac) is not None

def magic_packet(mac):
    if not valid_mac(mac):
        raise ValueError("Invalid MAC address")
    raw = bytes.fromhex(mac.replace(":", ""))
    return b"\xff" * 6 + raw * 16

def wake(mac):
    packet = magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, ("255.255.255.255", 9))

def media(action):
    if os.name != "nt":
        raise RuntimeError("Windows only")
    keys = {"playpause": 0xB3, "next": 0xB0, "previous": 0xB1}
    if action not in keys:
        raise ValueError("Unknown media action")
    key = keys[action]
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key, 0, 2, 0)

def audio(process, mute):
    if os.name != "nt":
        raise RuntimeError("Windows only")
    if not isinstance(process, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}\.exe", process, re.I):
        raise ValueError("Invalid executable name")
    if type(mute) is not bool:
        raise ValueError("mute must be a boolean")
    from pycaw.pycaw import AudioUtilities
    changed = 0
    for session in AudioUtilities.GetAllSessions():
        if session.Process and session.Process.name().lower() == process.lower() and session.SimpleAudioVolume:
            session.SimpleAudioVolume.SetMute(int(mute), None)
            changed += 1
    return changed

def status():
    try:
        import psutil
        return {"cpu_percent": psutil.cpu_percent(interval=0.1), "ram_percent": psutil.virtual_memory().percent}
    except ImportError:
        return {"cpu_percent": None, "ram_percent": None, "note": "Install psutil for metrics"}

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        return bool(TOKEN) and hmac.compare_digest(supplied, "Bearer " + TOKEN)

    def handle_request(self):
        if not self.authorized():
            return self.reply(401, {"error": "Unauthorized"})
        path = self.path.split("?", 1)[0]
        if self.command == "GET" and path == "/status":
            return self.reply(200, status())
        if self.command != "POST" or path not in ("/media", "/audio", "/wol", "/shutdown"):
            return self.reply(404, {"error": "Unknown endpoint"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2048:
                return self.reply(400, {"error": "Invalid body length"})
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("JSON object required")
            if path == "/media":
                media(body.get("action"))
                result = {"ok": True}
            elif path == "/audio":
                count = audio(body.get("process"), body.get("mute"))
                result = {"ok": True, "sessions_changed": count}
            elif path == "/wol":
                wake(body.get("mac"))
                result = {"ok": True}
            else:
                if not ALLOW_SHUTDOWN:
                    return self.reply(403, {"error": "Shutdown disabled"})
                if os.name != "nt":
                    raise RuntimeError("Windows only")
                result = {"ok": True, "message": "Shutdown scheduled"}
                self.reply(200, result)
                subprocess.Popen(["shutdown", "/s", "/t", "5"])
                return
            self.reply(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.reply(400, {"error": str(exc)})
        except Exception:
            self.reply(500, {"error": "Operation failed; check server logs"})

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

if __name__ == "__main__":
    if len(TOKEN) < 24:
        raise SystemExit("Set DESKTOP_CONTROL_TOKEN to a random string of at least 24 characters")
    print(f"Desktop Control listening on {HOST}:{PORT} (trusted LAN only)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
