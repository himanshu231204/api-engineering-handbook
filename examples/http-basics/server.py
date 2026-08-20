"""
A minimal HTTP/1.1 server built directly on Python's standard library.

No framework, no magic. This exists so you can *see* exactly what an HTTP
server does: read a request line, read headers, decide on a status line,
write headers back, write a body.

Run it:
    python server.py

Then hit it with the companion client.py, curl, or a browser:
    curl -v http://127.0.0.1:8000/hello
    curl -v -X POST http://127.0.0.1:8000/echo -d '{"name": "Ada"}'
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8000


class Handler(BaseHTTPRequestHandler):
    # BaseHTTPRequestHandler forces us to implement one method per HTTP
    # method we want to support. There is no routing framework underneath
    # this -- "routing" below is just an if/elif chain on self.path.

    server_version = "HTTPBasicsExample/1.0"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming convention)
        if self.path == "/":
            self._send_json(200, {"message": "GET / -> try /hello or /status/404"})
        elif self.path == "/hello":
            self._send_json(200, {"message": "hello, world"})
        elif self.path.startswith("/status/"):
            # Lets the client ask for an arbitrary status code, e.g.
            # /status/404, to see how status lines look on the wire.
            try:
                code = int(self.path.removeprefix("/status/"))
            except ValueError:
                code = 400
            self._send_json(code, {"requested_status": code})
        else:
            self._send_json(404, {"error": "not found", "path": self.path})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/echo":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            try:
                parsed = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError:
                parsed = None
            self._send_json(
                200,
                {
                    "you_sent_bytes": length,
                    "content_type": self.headers.get("Content-Type"),
                    "parsed_body": parsed,
                    "raw_body": raw_body.decode("utf-8", errors="replace"),
                },
            )
        else:
            self._send_json(404, {"error": "not found", "path": self.path})

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # keep console output tidy
        print(f"[server] {self.address_string()} - {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
