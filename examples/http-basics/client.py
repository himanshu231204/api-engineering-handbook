"""
A raw HTTP client built on a plain TCP socket -- no `requests`, no
`http.client`, nothing that hides the protocol from you.

This builds the request line, headers, and body as literal bytes, sends
them over a socket, and prints back exactly what came over the wire so you
can see the status line and headers un-parsed.

Run the server first:
    python server.py

Then in another terminal:
    python client.py
"""

from __future__ import annotations

import socket

HOST = "127.0.0.1"
PORT = 8000


def raw_request(method: str, path: str, body: bytes = b"", extra_headers: dict | None = None) -> bytes:
    """Build an HTTP/1.1 request by hand and return the raw response bytes."""
    headers = {
        "Host": f"{HOST}:{PORT}",
        # Close the connection after one response so reading is simple --
        # a real client would use keep-alive and Content-Length/chunked
        # framing to know where the response ends.
        "Connection": "close",
        "User-Agent": "http-basics-raw-client/1.0",
    }
    if body:
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if extra_headers:
        headers.update(extra_headers)

    # This is the exact wire format of an HTTP/1.1 request:
    #   METHOD path HTTP/1.1\r\n
    #   Header: value\r\n
    #   ...
    #   \r\n
    #   <body bytes>
    request_line = f"{method} {path} HTTP/1.1\r\n"
    header_lines = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    request = (request_line + header_lines + "\r\n").encode("utf-8") + body

    print("----- bytes sent on the wire -----")
    print(request.decode("utf-8", errors="replace"))
    print("-----------------------------------")

    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        sock.sendall(request)
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


def main() -> None:
    response = raw_request("GET", "/hello")
    print("----- bytes received on the wire -----")
    print(response.decode("utf-8", errors="replace"))
    print("---------------------------------------")

    body = b'{"name": "Ada"}'
    response = raw_request("POST", "/echo", body=body)
    print("----- bytes received on the wire (POST /echo) -----")
    print(response.decode("utf-8", errors="replace"))
    print("-----------------------------------------------------")


if __name__ == "__main__":
    main()
