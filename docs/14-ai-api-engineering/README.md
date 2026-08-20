# Part 14 — AI API Engineering

## What You'll Learn

How LLM APIs actually work, in depth: chat completion architecture, tokens and tokenization, context windows, sampling parameters (temperature, top-p, max tokens, stop sequences), streaming, structured outputs and JSON schemas, and function/tool calling. This part treats LLM APIs with the same rigor as any other production API — because that's what they are, with a few very different characteristics.

## Prerequisites

Parts 1–3 (HTTP, REST, building APIs). This part assumes you already understand request/response APIs and JSON — it focuses on what's *different* about AI APIs.

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [LLM APIs](llm-apis.md) | ✅ Written |
| 2 | [Chat Completion Architecture](chat-completion-architecture.md) | ✅ Written |
| 3 | [Tokens and Tokenization](tokens-and-tokenization.md) | ✅ Written |
| 4 | [Context Windows](context-windows.md) | ✅ Written |
| 5 | [Temperature and Sampling](temperature-and-sampling.md) | ✅ Written |
| 6 | [Structured Outputs](structured-outputs.md) | ✅ Written |
| 7 | [JSON Schemas](json-schemas.md) | ✅ Written |
| 8 | [Function Calling](function-calling.md) | ✅ Written |
| 9 | [Tool Calling](tool-calling.md) | ✅ Written |
| 10 | [Streaming LLM Responses](streaming-llm-responses.md) | ✅ Written |

## Related Example

[`examples/llm-streaming/`](../../examples/llm-streaming/) — a FastAPI endpoint that streams an LLM response token-by-token via SSE.

## Next

[Part 15 — Production AI Systems](../15-production-ai-systems/README.md)
