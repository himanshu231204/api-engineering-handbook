# AI Engineer Interview Questions

Questions covering Parts 14–17 of the handbook: LLM APIs, production AI systems, RAG, and AI agents/MCP.

## LLM API Fundamentals

**1. What is a token, and why doesn't "1 token = 1 word" hold?**
A token is a sub-word unit produced by the model's tokenizer (e.g. Byte-Pair Encoding) — common words might be one token, rarer words split into multiple tokens, and non-English text/code often tokenizes less efficiently. This matters directly for cost and context-window budgeting, since both are measured in tokens, not words or characters.

**2. What happens when a request exceeds the model's context window, and how do you design around it?**
The API returns an error — the model doesn't automatically truncate or summarize for you. Design around it by tracking token counts before sending (using the provider's tokenizer), truncating or summarizing conversation history, chunking large documents, and — for RAG — controlling how many retrieved chunks you inject based on the token budget actually available after the system prompt and conversation history.

**3. Explain temperature vs top-p, and why you generally shouldn't max out both at once.**
Temperature reshapes the probability distribution over the next token (higher = flatter/more random); top-p restricts sampling to the smallest set of tokens whose cumulative probability reaches p (lower = more restrictive). They both control randomness through different mechanisms, and tuning both aggressively at once makes behavior unpredictable and hard to reason about — most guidance is to primarily tune one.

**4. What's the difference between function calling and tool calling? Are they actually different?**
In most current usage they refer to the same underlying mechanism — the model outputs a structured call (name + arguments matching a JSON schema) instead of free text, which your code then executes. "Function calling" was OpenAI's original term for a single function-style call; "tool calling" is the more general/current term as providers extended it to arbitrary tools, often supporting multiple/parallel calls in one turn.

**5. How would you get an LLM to reliably return valid JSON matching a specific schema?**
Use the provider's structured output / JSON schema mode if available — it constrains generation (via constrained decoding or grammar-based sampling) so the output is guaranteed to match the schema, rather than just asking nicely in the prompt. If structured output mode isn't available, fall back to a strict system prompt + schema example + a validation/retry loop that re-prompts on parse failure.

**6. Design the request/response flow for streaming an LLM chat response to a browser client.**
Server opens a streaming connection to the LLM provider (`stream: true`) and receives incremental chunks (deltas). The API server forwards each chunk to the client as it arrives — typically via Server-Sent Events or a chunked HTTP response — so the browser can render tokens as they're generated instead of waiting for the full response. Handle the stream's terminal event/error cleanly so the client knows when generation is done or failed.

## Production AI Systems

**7. Why would you build a multi-provider LLM gateway instead of calling one provider's API directly?**
It decouples your application from any single provider's API shape, giving you failover when a provider has an outage, the ability to route requests to different models by cost/capability/latency needs, centralized rate limiting and cost tracking across providers, and leverage to negotiate/switch providers without rewriting application code.

**8. How do you design fallback behavior when your primary LLM provider is down?**
Wrap the primary call in retry logic with backoff for transient errors, and a circuit breaker so sustained outages fail fast. On circuit-open (or after retries exhausted), fail over to a secondary provider/model — ideally one with a comparable capability profile — and log/alert on the failover so it's visible, since silent degraded quality is worse than a visible outage in many cases.

**9. What's the difference between token-based rate limiting and request-based rate limiting, and why do LLM APIs need both?**
Request-based limits cap requests/minute regardless of size; token-based limits cap tokens/minute (input+output), since an LLM request's actual cost/compute scales with tokens, not request count — a single request with a 100K-token document costs far more than 100 tiny requests. Providers typically enforce both simultaneously (RPM and TPM limits) because either one alone can be gamed (many tiny requests vs. few huge ones).

**10. What is prompt caching, and what makes a prompt cacheable?**
Prompt caching lets a provider reuse the processed representation of a prompt prefix across requests, cutting cost/latency when the same large prefix (system prompt, tool definitions, a long document) repeats across calls. It's most effective for a stable prefix at the *start* of the prompt with only the trailing part (the actual user turn) changing between requests — providers generally require the cached portion to be identical, byte-for-byte, to hit the cache.

**11. What's the difference between prompt caching and semantic caching?**
Prompt caching reuses the *computation* for an identical prompt prefix (exact match) to save compute. Semantic caching caches full *responses* keyed by the meaning of a query (via embedding similarity), so a differently-worded but semantically similar question can return a previously-cached answer without calling the LLM at all — higher potential savings, but risks returning a stale or subtly wrong answer for a query that's similar but not actually identical in intent.

**12. How do you track cost per user/feature in an application with variable LLM usage?**
Log token usage (input/output separately, since they're priced differently) per request, tagged with user ID, feature/endpoint, and model used. Aggregate by whatever dimension you need to attribute cost to (per user, per feature, per team) and multiply by the provider's per-token pricing for that model. This is essential for usage-based billing, budget alerts, and identifying which features are cost outliers.

## RAG (Retrieval-Augmented Generation)

**13. Walk through the full RAG pipeline from document upload to answer.**
Document is uploaded and parsed into clean text. Text is chunked into retrievable pieces. Each chunk is embedded and stored in a vector database with metadata. At query time, the user's query is embedded with the same model, the vector DB returns the top-K most similar chunks, an optional reranker refines the ordering, the chunks are assembled into a prompt (context construction) respecting the token budget, and the LLM generates an answer grounded in that context, ideally with citations.

**14. Why would you add a reranking step when the vector database already returns results sorted by similarity?**
Vector similarity search (especially approximate nearest-neighbor at scale) is optimized for speed/recall over a large corpus, not precision — it can retrieve chunks that are topically related but not the *most* relevant. A reranker (often a cross-encoder that scores the query and each candidate chunk jointly, unlike bi-encoder embeddings which score them independently) is slower but far more accurate, so you retrieve broadly (top-50) then rerank down to a precise top-5.

**15. Your RAG system gives confidently wrong answers. How would you debug whether it's a retrieval problem or a generation problem?**
Inspect the actual chunks retrieved for the failing query — if the correct information isn't among them, it's a retrieval problem (chunking, embedding model, or query formulation). If the correct information *is* present in the retrieved context but the model still answers wrong, it's a generation/prompting problem (context construction, "lost in the middle," or the model ignoring context). This separation is essential — most "the LLM is dumb" complaints in RAG systems are actually retrieval failures.

**16. What's the tradeoff in choosing chunk size for a RAG pipeline?**
Smaller chunks give more precise retrieval (each chunk is topically focused, so similarity matching is sharper) but less context per chunk, sometimes cutting off information needed to answer fully. Larger chunks preserve more context per chunk but dilute the embedding (a chunk covering multiple topics embeds as a blurry average) and can push irrelevant content into the LLM's context. Most teams start around 200–500 tokens with overlap and tune based on measured retrieval quality.

**17. How would you design async document processing for large file uploads in a RAG system?**
The upload endpoint accepts the file, stores it in object storage, writes a job record, and returns immediately (`202 Accepted`) with a job ID — it does not parse/chunk/embed synchronously. A background worker picks up the job from a queue, does parsing/chunking/embedding, and updates job status as it progresses. The client polls the job status endpoint (or receives a webhook/websocket update) to know when the document is searchable.

## AI Agents & MCP

**18. What's the basic loop an AI agent runs, and where can it go wrong?**
The agent loop: receive a goal/input → the LLM decides on an action (respond, or call a tool) → if a tool call, execute it and feed the result back into context → repeat until the LLM produces a final answer or a stop condition is hit. Failure modes: infinite loops (no convergence, needs a max-iteration cap), tool results that don't fit the context window, and the agent taking an unsafe or irreversible action without confirmation.

**19. What are the three MCP primitives, and how do you decide which one to use when designing a new MCP server capability?**
Tools (model-invoked actions with side effects), Resources (host/user-attached reference data), Prompts (user-invoked reusable templates). Ask "who decides to use this, and does it do something or just provide data?" — an action the model should decide to take is a tool; a document/data source to reference is a resource; a pre-built interaction pattern a human picks explicitly is a prompt.

**20. Why does MCP exist instead of every application just implementing custom tool integrations?**
Without a standard, every host application needs bespoke integration code for every external tool/data source it wants to expose to an LLM (N applications × M tools = N×M integrations). MCP standardizes the protocol between hosts and capability providers, so a tool/data source implemented once as an MCP server works with any MCP-compatible host, and a host implemented once as an MCP client can use any MCP server — turning N×M into N+M.

**21. How would you design guardrails for an agent that can execute arbitrary tool calls, including destructive ones (e.g. deleting resources)?**
Classify tools by risk level and require explicit human confirmation for destructive/irreversible actions before execution. Scope the agent's credentials to the minimum permissions needed (principle of least privilege) rather than a broad service account. Log every tool call with its arguments for auditability. Consider a dry-run/preview mode for destructive tools, and rate-limit/cap how many actions an agent can take autonomously before requiring a checkpoint.

**22. What's the difference between an agent's short-term (context) memory and long-term memory, and why does an agent need both?**
Short-term memory is the current conversation/context window — everything the model can directly attend to right now, but it's bounded and disappears when the session ends. Long-term memory persists across sessions (a vector store, a structured DB of facts/preferences) and is retrieved into context only when relevant, similar to RAG. Agents need both because a bounded context window can't hold an entire operating history, but useful facts learned in one session (user preferences, past decisions) shouldn't be relearned from scratch every time.

**23. How do multiple agents communicate with each other in a multi-agent system, and what problems does that introduce?**
Common patterns: a shared message/event bus, direct agent-to-agent calls (one agent's output is another's input), or an orchestrator agent that delegates subtasks to specialist agents and aggregates results. Problems introduced: coordinating who acts when (avoiding duplicate or conflicting work), context/state getting fragmented across agents, cost/latency multiplying with each additional agent hop, and debugging becoming harder since failures can originate in any agent in the chain.

**24. When would you choose an LLM gateway with model routing over just always calling your best/most capable model?**
When cost and latency matter at scale, and not every request needs your most capable (and most expensive/slowest) model — route simple, high-volume tasks (classification, short extraction) to a cheaper/faster model, and reserve the most capable model for complex reasoning tasks. Routing logic can be rule-based (task type) or itself a lightweight classifier, and should have graceful fallback to a more capable model when the cheaper one's output looks low-confidence.

**25. What's a practical difference between building a chatbot and building an agent?**
A chatbot generates a response to a message — the model does not take actions in the world, it just talks. An agent, by contrast, has tools available and can decide to *act* — querying a database, calling an API, writing a file — often across multiple steps before producing a final response, meaning its behavior includes side effects and requires the guardrails, permissioning, and observability that a pure-conversation chatbot doesn't need.
