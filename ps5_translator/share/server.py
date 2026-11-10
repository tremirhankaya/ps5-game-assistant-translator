"""Show translations on a phone: a tiny web server for the home network.

The phone opens http://<this PC>:<port>/<code>/ in its browser; no app needed.
The page keeps one request open and the server answers it the moment a new
line exists (long polling), so the phone shows a translation right away. Only translated subtitles
are served: no settings, no API key. The random code in the address keeps
other devices on the network from opening the page by guessing.
"""
from __future__ import annotations

import json
import secrets
import socket
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_PORT = 8765
MAX_WAIT = 25.0  # seconds a phone's request may stay open waiting for a new line
_PAGE = Path(__file__).with_name("page.html")


def new_code() -> str:
    return secrets.token_urlsafe(6)


def local_ip() -> str:
    """This PC's address on the home network."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))  # no data is sent; this only picks the right network card
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


class ShareServer:
    def __init__(self, code: str, port: int = DEFAULT_PORT, host: str = "0.0.0.0") -> None:
        self.code = code
        self._lines: list[dict] = []
        self._lock = threading.Condition()
        self._stopped = False
        self._httpd = self._bind(host, port)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def _bind(self, host: str, port: int) -> ThreadingHTTPServer:
        handler = self._make_handler()
        last_error: OSError | None = None
        for candidate in ([port + i for i in range(10)] if port else [0]):
            try:
                return ThreadingHTTPServer((host, candidate), handler)
            except OSError as exc:  # port already in use: try the next one
                last_error = exc
        raise RuntimeError(f"Boş bir port bulunamadı: {last_error}")

    @property
    def url(self) -> str:
        return f"http://{local_ip()}:{self.port}/{self.code}/"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stopped = True
            self._lock.notify_all()  # release phones that are waiting for a line
        self._httpd.shutdown()
        self._httpd.server_close()

    def add_line(self, translated: str, source: str, time: str | None = None) -> None:
        with self._lock:
            self._lines.append(
                {"time": time or datetime.now().strftime("%H:%M:%S"), "translated": translated, "source": source}
            )
            self._lock.notify_all()

    def lines_after(self, index: int, wait: float = 0.0) -> dict:
        """Lines after `index`. With `wait`, blocks up to that many seconds until there is one."""
        with self._lock:
            if wait > 0 and index >= len(self._lines):
                self._lock.wait_for(lambda: self._stopped or len(self._lines) > index, timeout=wait)
            index = max(0, min(index, len(self._lines)))
            return {"total": len(self._lines), "lines": self._lines[index:]}

    def _make_handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                url = urlparse(self.path)
                prefix = f"/{server.code}/"
                if not url.path.startswith(prefix):
                    self.send_error(404)
                    return
                rest = url.path[len(prefix):]
                if rest == "":
                    self._send(_PAGE.read_bytes(), "text/html; charset=utf-8")
                elif rest == "lines":
                    query = parse_qs(url.query)
                    try:
                        after = int(query.get("after", ["0"])[0])
                    except ValueError:
                        after = 0
                    try:
                        wait = min(max(float(query.get("wait", ["0"])[0]), 0.0), MAX_WAIT)
                    except ValueError:
                        wait = 0.0
                    body = json.dumps(server.lines_after(after, wait), ensure_ascii=False).encode("utf-8")
                    self._send(body, "application/json; charset=utf-8")
                else:
                    self.send_error(404)

            def _send(self, body: bytes, content_type: str) -> None:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args) -> None:  # keep the terminal quiet
                pass

        return Handler
