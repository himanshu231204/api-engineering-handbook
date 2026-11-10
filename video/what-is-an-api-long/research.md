# Research brief — "What Is an API?" (Long, 16:9, 7–10 min)

Primary source: handbook chapter `docs/00-introduction/what-is-an-api.md`, fact-checked against MDN and Postman's 2025 State of the API report.

## Definition (plain words)
An API is a contract that lets one program ask another to do something, without knowing how the second program works inside. This video covers **web APIs**: a client sends an HTTP request, a server sends back a response.

## How it works (3–5 steps → SVG flow)
1. The client opens a connection and sends a request: method + path (+ headers, optional body).
2. Something in front of the server routes and validates it against the contract.
3. Business logic runs, usually reading/writing a database.
4. The server returns a response: status code + headers + (usually JSON) body.
5. The client reads the status first, then the body. HTTP is stateless: each request stands alone (MDN).

## Chapter ideas (each with an example)
1. **The contract** — wall socket / restaurant menu. Demo: menu → waiter → kitchen → food.
2. **A request, line by line** — `GET /users/42 HTTP/1.1` + `Host`, `Accept`, `Authorization`; the 200 + JSON response. (Verified against MDN's request/response parts.)
3. **The server side** — the 8-line FastAPI `get_user` endpoint from the handbook (run it before showing it); swap fake dict → PostgreSQL, client sees no change.
4. **Who calls APIs** — browser, mobile app, another service, script, AI agent. LLM APIs are plain POST + JSON.
5. **Mistakes chapter** — see below.

## Common mistakes (hook fuel and mistakes chapter)
- "API" = "REST API" or "web API". APIs also include function signatures, OS calls; REST is an architectural style, not a synonym for HTTP.
- Mirroring the DB schema in the response → rename a column, break every client.
- Confusing the API with the whole system or with the UI (many UIs, one API).
- Verbs in URLs (`/getUser`), `200 OK` for errors, leaking raw exception text (secondary sources; widely repeated, treat as best practice, not law).
- Undocumented contracts (Postman 2025: 93% of teams report collaboration blockers; 55% cite inconsistent documentation).

## Surprising facts / numbers (with sources)
- 65% of organisations generate revenue from their APIs; 25% operate as fully API-first (Postman 2025, 5,700+ respondents — vendor survey, say "Postman's survey").
- Only 24% of developers design APIs with AI agents in mind, while 89% use generative AI (Postman 2025).
- REST is still used by 93% of respondents (Postman 2025).
- HTTP: the client always initiates the request, never the server (MDN). HTTP is stateless but not sessionless (cookies).

## Analogy
Restaurant: menu = contract/docs, waiter = API layer, kitchen = server, dish = response. Kitchen can swap chefs and stoves as long as the dish matches the menu.

## Real things the video can show
- MDN "Overview of HTTP" page (dark-mode capture) with the request/response diagram.
- Postman 2025 State of the API page (for the stat beats), cited as a vendor survey.
- Real terminal: run the handbook's FastAPI example locally and `curl` it, showing a real 200 and a real 404.
- FastAPI logo/docs page (official), the handbook's own SVG `docs/assets/diagrams/00-what-is-an-api.svg` (original).

## Search phrases people use
"what is an api", "what is an api explained", "how do apis work", "api for beginners", "rest api vs api", "what is an api in programming".

## Sources
- [Overview of HTTP — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)
- [2025 State of the API Report — Postman](https://www.postman.com/state-of-api/2025/)
- [Handbook chapter: What Is an API?](../../docs/00-introduction/what-is-an-api.md)
- Search-result summaries (beginner API guides, REST design-mistake roundups from Zuplo, DZone, Racklify) — used for the mistakes list only; not quoted.
