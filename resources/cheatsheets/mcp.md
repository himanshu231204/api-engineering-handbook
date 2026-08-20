# MCP (Model Context Protocol) Cheatsheet

For the full explanation, see [AI Agents & MCP](../../docs/17-ai-agents-and-mcp/README.md).

## MCP primitives, one line each

| Primitive | Who invokes it | What it's for |
|---|---|---|
| **Tools** | The model (LLM decides when to call it, based on the conversation) | Actions with side effects — run a query, send a message, execute code. Has a name, description, JSON Schema for args. |
| **Resources** | The host application (or user), not the model autonomously | Data to reference/attach to context — a file, a DB row, a log. Addressed by URI, has a MIME type. |
| **Prompts** | The user (via host UI, like a slash-command) | Reusable, server-defined prompt templates that produce a ready-to-send message sequence. |

The distinguishing question: **who decides to use it, and what happens when they do?** Model decides → tool (side effect). Host/user decides → resource (data). User decides → prompt (interaction template).

## Transports quick reference

| Transport | How it works | Best for |
|---|---|---|
| **stdio** | Client spawns the server as a local subprocess; communicates over stdin/stdout | Local tools, CLI integrations, servers running on the same machine as the client |
| **Streamable HTTP** | Client sends requests over HTTP POST; server can respond with a single JSON response or open an SSE stream for multiple messages | Remote servers, cloud-hosted MCP servers, anything not co-located with the client |
| **(Legacy) HTTP+SSE** | Separate SSE endpoint for server→client messages, HTTP POST for client→server | Older MCP servers predating Streamable HTTP — being phased out in favor of it |

## Client–Host–Server roles

- **Host** — the user-facing application (e.g. an IDE, a chat app, Claude Code itself). Owns the UI, manages permissions, decides which resources/prompts get surfaced to the user, and holds the overall conversation.
- **Client** — lives inside the host, maintains a 1:1 connection to a single MCP server, handles the protocol-level message exchange (JSON-RPC 2.0 over the chosen transport).
- **Server** — a separate process/service exposing tools, resources, and/or prompts for a specific capability (e.g. a GitHub MCP server, a Postgres MCP server). Doesn't know about the LLM directly — it just exposes capabilities via the protocol.

One host can run many clients simultaneously, each talking to a different server — that's how a single chat session can have GitHub, Slack, and a database all available as capabilities at once.

## Quick facts

- MCP messages are **JSON-RPC 2.0** — requests, responses, and notifications.
- Discovery is explicit: `tools/list`, `resources/list`, `prompts/list` — the client asks the server what's available.
- Servers can push **notifications** (e.g. `notifications/resources/updated`) when something changes, without the client polling.
- MCP does not replace function/tool calling — it standardizes *how* those tools (and resources/prompts) are discovered and invoked across many servers, instead of every integration being bespoke.
