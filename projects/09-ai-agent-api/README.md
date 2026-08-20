# Project 9 — AI Agent API

## Goal

Expose an agent loop — an LLM that reasons, calls tools, observes results, and repeats until it reaches a final answer — as a well-behaved HTTP API. This project makes agent architecture concrete: instead of a single request/response, you'll build a system that streams intermediate reasoning/tool-call steps to the client, enforces hard caps on iterations and cost so a stuck agent can't loop forever or blow a budget, and treats every tool call as an untrusted boundary needing guardrails. As a stretch, you'll expose one of the agent's tools as a minimal MCP server, connecting this project directly to Part 17's MCP chapters.

## Builds On

- [Part 17 — AI Agents & MCP](../../docs/17-ai-agents-and-mcp/README.md)
- Specifically: [agent architecture](../../docs/17-ai-agents-and-mcp/agent-architecture.md), [agent APIs](../../docs/17-ai-agents-and-mcp/agent-apis.md), [tool execution](../../docs/17-ai-agents-and-mcp/tool-execution.md), [memory systems](../../docs/17-ai-agents-and-mcp/memory-systems.md), [MCP architecture](../../docs/17-ai-agents-and-mcp/mcp-architecture.md), [MCP servers](../../docs/17-ai-agents-and-mcp/mcp-servers.md), [tools, resources, prompts](../../docs/17-ai-agents-and-mcp/tools-resources-prompts.md), [agent security and guardrails](../../docs/17-ai-agents-and-mcp/agent-security-and-guardrails.md)
- Also draws on: [function calling](../../docs/14-ai-api-engineering/function-calling.md), [tool calling](../../docs/14-ai-api-engineering/tool-calling.md), [streaming LLM responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md)
- Recommended pairing: [Project 8 — Multi-Provider LLM Gateway](../08-llm-gateway/README.md) as the underlying model provider

## Requirements

- `POST /agents/{agent_id}/runs` starts an agent run given a user goal/prompt; the agent plans, calls tools, and iterates until it produces a final answer or hits a cap.
- The agent loop is exposed as a stream: clients receive each step (thought, tool call, tool result, final answer) as it happens, not just the end result.
- At least three real tools are registered (e.g. a calculator, a web-search stub, and a database-lookup tool) behind a common `Tool` interface with a JSON-schema-defined input.
- Hard caps enforced: max iterations per run, max wall-clock time, and max total token/cost spend — the run is force-terminated with a clear reason if any cap is hit.
- Tool execution is sandboxed/validated: tool inputs are schema-validated before execution, and tool outputs are size-capped before being fed back into the next LLM call.
- Full run history (every step, tool call, and result) is persisted and retrievable after the fact for debugging/audit.
- A run can be cancelled mid-flight by the client.
- (Stretch) One tool is implemented as an actual MCP server, and the agent connects to it as an MCP client rather than a hardcoded function — demonstrating the same tool working both ways.

## Architecture

```mermaid
flowchart TB
    Client[Client] -->|POST /agents/id/runs| API[Agent API]
    API --> Orchestrator[Agent Orchestrator\n(loop controller)]
    Orchestrator --> LLM[LLM Client\n(via Project 8 Gateway)]
    Orchestrator --> Guardrails[Iteration/Time/Cost Cap Enforcer]
    Orchestrator --> ToolRegistry[Tool Registry]
    ToolRegistry --> Calc[Calculator Tool]
    ToolRegistry --> Search[Web Search Tool]
    ToolRegistry --> DBTool[DB Lookup Tool]
    ToolRegistry -.MCP.-> MCPServer[MCP Server\n(stretch: one tool as MCP)]
    Orchestrator --> RunStore[(runs, steps tables)]
    Orchestrator -->|SSE stream of steps| Client
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/agents` | Register a new agent definition (system prompt, allowed tools, caps). |
| GET | `/agents` | List available agent definitions. |
| POST | `/agents/{agent_id}/runs` | Start a run with a user goal. Returns `run_id` and streams steps via SSE. |
| GET | `/runs/{run_id}` | Get run status and final answer (if complete). |
| GET | `/runs/{run_id}/steps` | Full step-by-step history: thoughts, tool calls, tool results, final answer. |
| POST | `/runs/{run_id}/cancel` | Cancel an in-progress run. |
| GET | `/tools` | List registered tools with their JSON-schema input definitions. |
| POST | `/tools/{tool_name}/invoke` | (Debug/admin) Directly invoke a tool outside of an agent run, for testing tool behavior in isolation. |

## Database Schema

```sql
CREATE TABLE agents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,
    system_prompt  TEXT NOT NULL,
    allowed_tools  TEXT[] NOT NULL,
    max_iterations INTEGER NOT NULL DEFAULT 10,
    max_seconds    INTEGER NOT NULL DEFAULT 60,
    max_cost_usd   NUMERIC(10,4) NOT NULL DEFAULT 0.50,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE runs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id       UUID NOT NULL REFERENCES agents(id),
    user_id        UUID NOT NULL,
    goal           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'running'
                   CHECK (status IN ('running','completed','failed','cancelled','cap_exceeded')),
    final_answer   TEXT,
    termination_reason TEXT,
    iteration_count INTEGER NOT NULL DEFAULT 0,
    total_cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ
);

CREATE TABLE steps (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id         UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_number    INTEGER NOT NULL,
    step_type      TEXT NOT NULL CHECK (step_type IN ('thought','tool_call','tool_result','final_answer','error')),
    tool_name      TEXT,
    tool_input     JSONB,
    tool_output    JSONB,
    content        TEXT,
    tokens_used    INTEGER,
    cost_usd       NUMERIC(10,6),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, step_number)
);
```

## Suggested Folder Structure

```
09-ai-agent-api/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── agents.py
│   │   ├── runs.py
│   │   └── tools.py
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── run.py
│   │   └── step.py
│   ├── orchestrator/
│   │   ├── agent_loop.py         # the core plan -> act -> observe loop
│   │   ├── caps.py               # iteration/time/cost enforcement
│   │   └── stream.py             # SSE step emitter
│   ├── tools/
│   │   ├── base.py               # Tool interface + JSON schema validation
│   │   ├── calculator.py
│   │   ├── web_search.py
│   │   └── db_lookup.py
│   ├── mcp/
│   │   ├── server.py             # stretch: one tool exposed as MCP server
│   │   └── client.py             # agent-side MCP client
│   ├── llm/
│   │   └── client.py             # calls Project 8's gateway or a provider directly
│   ├── models/
│   │   ├── agent.py
│   │   ├── run.py
│   │   └── step.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_agent_loop_caps.py
│   ├── test_tool_schema_validation.py
│   ├── test_run_cancellation.py
│   └── test_step_history.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI project with Postgres for `agents`/`runs`/`steps`, and wire up an LLM client (ideally pointed at [Project 8's gateway](../08-llm-gateway/README.md) for routing/cost tracking for free).
2. Define the `Tool` interface: `name`, `description`, `input_schema` (JSON Schema), `execute(input) -> output`, and implement three concrete tools, per [tool execution](../../docs/17-ai-agents-and-mcp/tool-execution.md).
3. Implement `POST /agents` to register an agent definition (system prompt, allowed tool names, caps) and `GET /agents`/`GET /tools`.
4. Implement the core agent loop in `orchestrator/agent_loop.py`: call the LLM with the conversation + tool schemas, parse its response for a tool call or final answer, execute the tool if requested, append the result to the conversation, and repeat, per [agent architecture](../../docs/17-ai-agents-and-mcp/agent-architecture.md).
5. Persist every step to the `steps` table as it happens (not batched at the end), so a crashed run still has a partial, inspectable history.
6. Implement the cap enforcer: check iteration count, elapsed wall-clock time, and accumulated cost before each LLM call; terminate the run with `cap_exceeded` and a specific `termination_reason` when any limit is hit.
7. Implement tool input validation against each tool's JSON schema before execution — reject malformed tool calls back to the LLM as an error observation rather than crashing the run, per [agent security and guardrails](../../docs/17-ai-agents-and-mcp/agent-security-and-guardrails.md).
8. Cap tool output size (e.g. truncate web-search results) before feeding them back into the next LLM call, to control token growth across iterations.
9. Implement `POST /agents/{id}/runs` to start a run as a background task and stream steps to the client over SSE as they're produced.
10. Implement `POST /runs/{id}/cancel`: set a cancellation flag the loop checks between iterations/tool calls, and stop cleanly with status `cancelled`.
11. Implement `GET /runs/{id}` and `GET /runs/{id}/steps` for post-hoc inspection of completed or failed runs.
12. (Stretch) Wrap one existing tool (e.g. `db_lookup`) as an actual MCP server exposing it via `tools/list` and `tools/call`, and have the agent orchestrator use an MCP client to call it instead of calling the Python function directly, per [MCP servers](../../docs/17-ai-agents-and-mcp/mcp-servers.md) and [MCP clients](../../docs/17-ai-agents-and-mcp/mcp-clients.md).
13. Write tests that force each termination path (normal completion, iteration cap, time cap, cost cap, cancellation) and assert `termination_reason` and step history are correct in each case.

## Advanced Improvements

- Add persistent cross-run memory per user (a `memories` table the agent can read/write to), per [memory systems](../../docs/17-ai-agents-and-mcp/memory-systems.md).
- Add multi-agent orchestration where one agent can delegate a sub-task to another, per [multi-agent communication](../../docs/17-ai-agents-and-mcp/multi-agent-communication.md).
- Add human-in-the-loop approval for high-risk tool calls (e.g. anything that writes data) before execution proceeds.
- Add streaming of partial LLM tokens within a "thought" step, not just step-level granularity.
- Add a replay endpoint that re-runs a past run's exact step sequence against a new model version for regression testing.
- Add per-tool rate limiting and per-tool cost accounting, not just run-level caps.

## Production Checklist

- [ ] Hard caps on iterations, wall-clock time, and cost are enforced server-side and cannot be bypassed by a malicious or malformed goal prompt.
- [ ] Every tool input is schema-validated before execution; no tool ever receives raw, unvalidated LLM output.
- [ ] Tools that touch external systems (web search, DB writes) are sandboxed/scoped with least privilege and cannot access resources outside their declared purpose.
- [ ] Full step-by-step audit trail persisted for every run, including failed and cancelled ones, for debugging and compliance.
- [ ] Prompt-injection guardrails: content returned from tools (e.g. web search results) is treated as untrusted data, not as new instructions, per [agent security and guardrails](../../docs/17-ai-agents-and-mcp/agent-security-and-guardrails.md).
- [ ] Run cancellation is checked frequently enough that a client-initiated cancel takes effect within a bounded time.
- [ ] Cost tracked per run and aggregable per user/tenant, integrated with the billing/budget system if paired with [Project 8](../08-llm-gateway/README.md).
- [ ] Timeouts on every tool call individually, not just on the run as a whole, so one hanging tool can't stall the entire loop.
- [ ] Observability: step type distribution, average iterations to completion, and cap-exceeded rate tracked as product health metrics.
- [ ] Load/stress tested with adversarial goals designed to induce infinite tool-call loops, confirming caps actually terminate them.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Pairs with: [Project 8 — Multi-Provider LLM Gateway](../08-llm-gateway/README.md)
