# Tool-Using Agent Loop + Minimal MCP Server

A runnable tool-calling agent loop (call LLM with tools -> execute a
requested tool -> feed the result back -> repeat until a final answer),
exposed via FastAPI, plus a hand-rolled, illustrative MCP server showing
the JSON-RPC shape a real MCP server implements.

Accompanies:
[`docs/14-ai-api-engineering/tool-calling.md`](../../docs/14-ai-api-engineering/tool-calling.md),
[`docs/17-ai-agents-and-mcp/agent-architecture.md`](../../docs/17-ai-agents-and-mcp/agent-architecture.md),
[`docs/17-ai-agents-and-mcp/tool-execution.md`](../../docs/17-ai-agents-and-mcp/tool-execution.md), and
[`docs/17-ai-agents-and-mcp/mcp-servers.md`](../../docs/17-ai-agents-and-mcp/mcp-servers.md)

## What This Demonstrates

- **`tools.py`** — three tools, each defined as a JSON schema (name,
  description, `input_schema`) paired with an async Python handler:
  - `calculator` — evaluates a basic arithmetic expression using a
    restricted AST walk (`_safe_eval`), **not** Python's `eval()` — no
    names, attribute access, or function calls are reachable from the
    input, only arithmetic.
  - `get_current_time` — returns the current UTC time.
  - `search` — looks up a topic in a tiny in-memory mock index (not a real
    web search).
- **`llm_client.py`** — a generic `call_llm_with_tools()` abstraction.
  Routes to a real provider if `LLM_API_KEY` is set (a clearly-commented
  pseudo-implementation only, since we can't assume which provider/SDK you
  have), otherwise falls back to a small rule-based local simulation so the
  whole loop runs and is demonstrably correct with **zero** provider
  credentials.
- **`main.py`** — the agent loop itself (`run_agent_loop`): calls the LLM,
  checks the response for `tool_use` blocks, executes the matching
  function from `tools.py`, feeds the `tool_result` back into the message
  history, and repeats — bounded by `MAX_ITERATIONS` so a stuck loop can't
  run forever. Exposed via `POST /agent`.
- **`mcp_server_example.py`** — a minimal, illustrative MCP server exposing
  `get_current_time` over stdio using hand-rolled JSON-RPC framing,
  following the shape described in
  [`docs/17-ai-agents-and-mcp/mcp-servers.md`](../../docs/17-ai-agents-and-mcp/mcp-servers.md).
  **This is for learning the protocol shape, not for production** — a real
  server should use the official MCP SDK (`pip install mcp`), which handles
  the handshake, framing, and error formatting correctly.

## Prerequisites

- Python 3.11+
- No LLM provider account required to run the demo (see above).

## How to Run the Agent API

```bash
cd examples/ai-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: only needed for a real provider
uvicorn main:app --reload
```

Try each tool:

```bash
curl -s -X POST http://localhost:8000/agent -H "Content-Type: application/json" \
  -d '{"message": "(4 + 5) * 2"}'

curl -s -X POST http://localhost:8000/agent -H "Content-Type: application/json" \
  -d '{"message": "what time is it?"}'

curl -s -X POST http://localhost:8000/agent -H "Content-Type: application/json" \
  -d '{"message": "search for fastapi"}'

curl -s -X POST http://localhost:8000/agent -H "Content-Type: application/json" \
  -d '{"message": "tell me a joke"}'
```

The response includes `answer`, the list of `steps` taken (each tool
called, its input, and its result), and how many loop `iterations` it took
— useful for seeing the loop mechanics, not just the final answer.

See available tool schemas:

```bash
curl -s http://localhost:8000/tools
```

## How to Run the MCP Server Example

```bash
cd examples/ai-agent
python mcp_server_example.py
```

Then paste JSON-RPC requests, one per line:

```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_current_time", "arguments": {}}}
```

Each line gets one JSON-RPC response back on stdout — this is the same
request/response framing a host process would use when talking to a
locally-spawned MCP server over a subprocess pipe (stdio transport).

## Using a Real LLM Provider

1. Set `LLM_API_KEY` (and optionally `LLM_MODEL`) in `.env`.
2. In `llm_client.py`, implement `_call_real_provider()` following the
   shape shown in its docstring — a generic tool-calling chat completion
   request — adjusting the URL, request body, and response parsing for
   your actual provider.
3. Restart the server. `call_llm_with_tools` automatically switches to the
   real-provider path once `LLM_API_KEY` is set.

## Things to Try / Modify

1. **Force the iteration cap** — temporarily set `MAX_ITERATIONS = 1` in
   `main.py` and send a message that requires a tool call; confirm the
   endpoint returns a `500` explaining the loop didn't converge, instead of
   silently truncating.
2. **Add a fourth tool** — e.g. a `unit_converter` tool — following the
   `register_tool` pattern in `tools.py`, and confirm the simulated
   `llm_client` (or a real provider once wired up) picks it correctly based
   on the user's message.
3. **Chain multiple tool calls** — extend `_simulate_response` in
   `llm_client.py` so a single question ("what time is it, and what's
   12 * 7?") triggers two sequential tool calls before the final answer,
   exercising more than two loop iterations.
4. **Add a second tool to the MCP server** — extend
   `mcp_server_example.py` to also expose `calculator` from `tools.py`,
   registering it the same way `get_current_time` is registered, then
   compare how much protocol-handling code you had to write by hand versus
   what the official MCP SDK would give you for free.
