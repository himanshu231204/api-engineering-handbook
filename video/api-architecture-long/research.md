# Source map — "API Architecture at a Glance" (Long, 16:9)

Primary source: the handbook chapter [`docs/00-introduction/api-architecture.md`](../../docs/00-introduction/api-architecture.md). No web research was needed: every fact on screen comes from the chapter, the concept diagrams and example it points to, or a real run. No third-party statistics are used.

## Harvest (`harvest/harvest.json`)
- 2 Mermaid blocks (flowchart TD "whole map", flowchart LR "grouped by layer"), 0 embedded concept SVGs, 1 text block (the 7-step `/chat` trace), 3 quiz questions.
- Related diagram the chapter's topic is built on: `diagrams/api-request-flow.md` (Mermaid sequence).

## Asset map (everything the repo has is on screen)
| Beat | Asset | Source |
|---|---|---|
| map | Mermaid flowchart TD | chapter, "Core Concept" (`hf/assets/repo/mermaid/api-architecture-layers-td.svg`) |
| lay | Mermaid flowchart LR with subgraphs | chapter, "Architecture" (`…-layers-lr.svg`) |
| gw | concept SVG | `docs/assets/diagrams/11-api-gateway.svg` |
| cache | concept SVG | `docs/assets/diagrams/07-cache-aside.svg` |
| queue | concept SVG | `docs/assets/diagrams/08-message-queue.svg` |
| ai | concept SVG | `docs/assets/diagrams/15-llm-gateway.svg` |
| read | Mermaid sequence | `diagrams/api-request-flow.md` (`api-request-flow.svg`) |
| write | concept SVG | `docs/assets/diagrams/18-request-flow.svg` |
| chat | the chapter's 7-step "send a chat message" trace, verbatim | chapter, "Request / Response Example" (`harvest/code/block1.txt`) |
| route, run1, run2 | excerpt of `examples/llm-gateway/main.py` + real terminal output | `demo/real_output.txt` (run with `demo/run_demo.sh`) |
| rec, quiz | key takeaways; "Check Yourself" question 3 and its answer | chapter |

## Fact check (claim on screen -> where it comes from)
- Five layers: "client → edge → gateway → application → data/AI" (chapter, Core Concept).
- Org-chart roles (receptionist, security and routing, department, filing cabinet, ticket system, AI specialist): chapter, "Mental Model".
- GET /products/9 may stop at the CDN; POST /orders goes gateway → app → database and may enqueue a job; POST /chat goes gateway → app → AI gateway → provider with streaming: chapter, "How It Works" and "Request / Response Example".
- "about 1 ms" cache hit, TTL, delete-on-write: `07-cache-aside.svg`. "202 Accepted / decoupling, durability, load leveling": `08-message-queue.svg`. "401 / 429 rejected at the edge; keep it dumb": `11-api-gateway.svg`. "201 Created in about 20 to 150 ms, worker after the response": `18-request-flow.svg`.
- Mistakes (day-one layers, microservices as inherently better, AI as afterthought), AI perspective (slow, non-deterministic, metered; LLM gateways, token rate limits, prompt caching, semantic caching in Parts 14-17), "Part 11" and "Part 18" pointers: chapter.
- Real run: the example's priority list, token bucket (capacity 5, refill 1/s) and fallback are in `examples/llm-gateway/main.py`; the output (4 calls served by the flaky first provider, 1 fallback to provider_a costing $0.000228, a burst of 8 = 5 x 200 then 3 x 429) is the recorded run in `demo/real_output.txt`.

## Mistakes chapter / quiz
Three common mistakes from the chapter; the end quiz is Check Yourself question 3 (queue the confirmation email).
