# LLM APIs Cheatsheet

For the full explanation, see [AI API Engineering](../../docs/14-ai-api-engineering/README.md).

## Token & context window quick facts

- A **token** is roughly ¾ of a word in English text (~4 characters/token on average); code, non-English text, and rare words tokenize less efficiently (more tokens per character).
- **Context window** = max tokens (input + output combined, for most APIs) the model can attend to in one request. Common sizes range from ~8K up to 1M+ tokens depending on model/provider.
- Both **input tokens** and **output tokens** are billed, usually at different rates (output is typically more expensive than input).
- Exceeding the context window causes a hard error — you must truncate, summarize, or chunk input yourself; the API will not silently drop content for you.
- `max_tokens` (or equivalent) caps *output* length only — it does not reserve/guarantee input space.
- System prompt + conversation history + tool definitions + retrieved context (RAG) all count against the same context window budget.

## Sampling parameters quick reference

| Parameter | Range | Effect | Guidance |
|---|---|---|---|
| **Temperature** | 0.0–2.0 (varies by provider) | Controls randomness: low = deterministic/focused, high = creative/varied | `0`–`0.3` for extraction/classification/code; `0.7`–`1.0` for creative writing/brainstorming |
| **Top-p (nucleus sampling)** | 0.0–1.0 | Samples from the smallest set of tokens whose cumulative probability ≥ p | `0.9`–`1.0` typical; lower it to tighten output without fully zeroing temperature |
| **Top-k** | integer ≥ 1 | Samples only from the k most likely next tokens | Rarely tuned directly on most modern APIs; useful for tightly constrained output |
| **Frequency penalty** | provider-specific | Penalizes tokens proportional to how often they've already appeared | Reduces repetition/looping in long outputs |
| **Presence penalty** | provider-specific | Flat penalty for any token that has appeared at all | Encourages introducing new topics/vocabulary |

Rule of thumb: tune **either** temperature **or** top-p, not both aggressively at once — they interact and make behavior harder to reason about.

## Common LLM provider HTTP status codes

| Code | Meaning | What to do |
|---|---|---|
| `200 OK` | Success | — |
| `400 Bad Request` | Invalid request shape, bad parameters, malformed tool schema | Fix the request — don't retry as-is |
| `401 Unauthorized` | Invalid/missing API key | Check credentials, don't retry |
| `403 Forbidden` | Key valid but lacks access to this model/feature | Check plan/permissions |
| `404 Not Found` | Unknown model name or endpoint | Check model ID/spelling |
| `413 Payload Too Large` | Request exceeds size/token limits | Truncate/chunk input |
| `422 Unprocessable Entity` | Request well-formed but semantically invalid (e.g. schema violates constraints) | Fix request content |
| `429 Too Many Requests` | Rate limit (requests/min or tokens/min) exceeded | Back off exponentially, respect `Retry-After` |
| `500 Internal Server Error` | Provider-side failure | Retry with backoff |
| `503 Service Unavailable` | Provider overloaded/down | Retry with backoff, consider failover to another provider |
| `529 Overloaded` (Anthropic-specific) | Provider temporarily overloaded | Retry with backoff, same as 503 handling |

## Quick tips

- Always set a `max_tokens` explicitly — an unbounded generation can run long and cost more than expected.
- Stream responses (`stream: true`) for anything user-facing to reduce perceived latency (see [Streaming LLM Responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md)).
- Prefer structured outputs / JSON schema mode over asking the model to "please respond in JSON" in the prompt — it's enforced, not just requested.
- Cache the system prompt / tool definitions when a provider supports prompt caching — it's often the largest fixed cost per request.
