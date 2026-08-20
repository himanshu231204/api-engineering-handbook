# HTTP Basics — Raw Sockets, No Framework

Accompanies [Part 1 — API Foundations](../../docs/01-api-foundations/README.md), especially
[HTTP and HTTPS](../../docs/01-api-foundations/http.md), [Request/Response](../../docs/01-api-foundations/request-response.md),
[Headers](../../docs/01-api-foundations/headers.md), and [Status Codes](../../docs/01-api-foundations/status-codes.md).

## What this demonstrates

Before you ever touch FastAPI, it helps to see that HTTP is just **text sent over a TCP
socket** with a very specific format. This example strips away every framework:

- `server.py` uses only `http.server` from the standard library to handle raw requests
  and write raw responses.
- `client.py` uses a plain `socket` connection to build an HTTP/1.1 request **by hand**
  (request line + headers + blank line + body) and prints the exact bytes sent and
  received, unparsed.

There is no routing library, no serialization library, no connection pooling — just the
protocol. Once you've seen this, everything FastAPI does later is "the same thing, with
conveniences."

## Prerequisites

- Python 3.11+
- No third-party packages — everything here is the standard library.

## How to run it

Terminal 1 — start the server:

```bash
cd examples/http-basics
python server.py
# Serving on http://127.0.0.1:8000
```

Terminal 2 — run the raw client:

```bash
cd examples/http-basics
python client.py
```

You'll see two blocks of output per request: the exact bytes sent on the wire, and the
exact bytes received back — including the status line (`HTTP/1.1 200 OK`), every header,
a blank line, and then the body.

You can also poke the server with `curl -v` or a browser, which is a good way to compare
a "real" client's request against the one `client.py` builds by hand:

```bash
curl -v http://127.0.0.1:8000/hello
curl -v -X POST http://127.0.0.1:8000/echo -d '{"name": "Ada"}' -H 'Content-Type: application/json'
curl -v http://127.0.0.1:8000/status/404
```

## Things to try

1. **Break the request format.** In `client.py`, remove the trailing `\r\n\r\n` (the
   blank line that separates headers from the body) and see the server hang or fail to
   parse the request — this is what that blank line is actually for.
2. **Request an arbitrary status code.** Hit `GET /status/500` or `GET /status/201` and
   watch the status *line* change while everything else about the response shape stays
   the same — status codes are just a number and a reason phrase, nothing magic.
3. **Compare `Connection: close` vs `keep-alive`.** The client here closes the TCP
   connection after every request. Try removing that header and using
   `http.client.HTTPConnection` instead to make two requests over the same socket —
   notice you now need `Content-Length` (or chunked encoding) to know where one response
   ends and the next begins, since the socket itself doesn't tell you.
