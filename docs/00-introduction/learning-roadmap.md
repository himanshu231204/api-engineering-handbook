# Learning Roadmap

> [!TIP]
> **In one line:** Pick one of three paths through the handbook based on what you already know, and prove each part stuck before moving on — depth beats speed.
>
> **In plain English:** This chapter is a trip plan. Just as you learn to drive before you enter a race, the AI parts (14–17) rely on the backend basics in Parts 1–13. Choose your route, keep a steady pace, and check yourself after each part.
>
> **You'll be able to:** Choose Path A, B or C for your starting point · Set a realistic weekly pace · Test whether you really learned a part before moving on

## Why This Matters

190 chapters across 20 parts is a lot. Without a plan, it's easy to either burn out trying to read everything linearly in one sitting, or jump straight to the "exciting" AI chapters and hit a wall because you're missing prerequisites (rate limiting, caching, auth) that AI systems still depend on. This chapter gives you a concrete plan.

## The Journey

```text
Beginner
   ↓
Understand HTTP                         → Part 1
   ↓
Learn REST APIs                         → Part 2
   ↓
Build APIs                              → Part 3
   ↓
Work with Databases                     → Part 4
   ↓
Authentication & Authorization          → Part 5
   ↓
Production Reliability                  → Part 6
   ↓
Caching & Async Systems                 → Parts 7–8
   ↓
Webhooks & Real-Time APIs               → Part 9
   ↓
API Security                            → Part 10
   ↓
Microservices                           → Part 11
   ↓
Observability                           → Part 12
   ↓
API Testing                             → Part 13
   ↓
LLM APIs                                → Part 14
   ↓
Production AI Systems                   → Part 15
   ↓
RAG APIs                                → Part 16
   ↓
AI Agents & MCP                         → Part 17
   ↓
Production Architecture                 → Part 18
   ↓
System Design Case Studies              → Part 19
   ↓
Capstone Projects                       → Part 20
```

## Three Suggested Paths

**Path A — Full sequential (recommended for most people).** Read Parts 1 → 20 in order, doing exercises as you go and building each capstone project as soon as its prerequisite parts are done. This is the path the handbook is written for.

**Path B — "I already know backend basics."** If you're already comfortable with HTTP, REST, and building APIs (Parts 1–3 feel like review), skim Parts 1–3, read Parts 4–13 for anything unfamiliar (many experienced backend engineers still have gaps in reliability patterns, observability, or distributed transactions), then slow down for Parts 14–20.

**Path C — "I need AI API skills fast, and I'll backfill fundamentals later."** Read Part 0, skim Part 1 (you need HTTP basics), then jump to Parts 14–17. This path works if you're already an experienced backend engineer moving into AI work — but come back for Parts 5, 6, 7, and 10. Production AI systems fail in the same ways traditional APIs do (bad auth, no rate limiting, no caching, no observability) plus a few new ways, and skipping those parts means re-learning them the hard way in production.

## Time Investment (Rough Guide)

| Path | Chapters read closely | Rough pace |
|---|---|---|
| A — Full sequential | All 190 | 1–2 parts/week alongside building |
| B — Backend-experienced | ~140 | 2–3 parts/week |
| C — AI-fast-track (with backfill) | ~90 upfront, backfill later | Parts 14–17 in 1–2 weeks, backfill ongoing |

These are guides, not deadlines — depth matters more than speed. A chapter you skimmed and immediately forgot didn't save you any time.

## How to Know You've Actually Learned a Part

Don't just read — after each part, you should be able to:

1. Explain the core concept out loud, from memory, without notes.
2. Do the part's exercises without looking back at the chapter.
3. Spot the concept "in the wild" — e.g., after Part 6, notice retry/backoff logic (or its absence) in a real API client you use.

If you can't do at least the first two, re-read before moving on — later parts assume earlier ones stuck.

## Key Takeaways

- Pick a path (A, B, or C) based on your starting point, not by comparing yourself to someone else's plan.
- AI API engineering (Parts 14–17) is built on top of general backend engineering (Parts 1–13), not a separate discipline — don't skip the foundation entirely.
- Depth beats speed: the exercises exist to prove you actually learned the chapter, not just read it.

### Check Yourself

<details markdown="1">
<summary>1. What are the three suggested paths?</summary>

A: read Parts 1 to 20 in order. B: you know backend basics — skim 1–3, read 4–13 for gaps, slow down for 14–20. C: AI fast track — Part 0, skim Part 1, jump to 14–17, then come back for the fundamentals.

</details>

<details markdown="1">
<summary>2. Why does Path C tell you to come back for Parts 5, 6, 7 and 10?</summary>

Production AI systems fail in the same ways ordinary APIs do — bad auth, no rate limiting, no caching, no observability — plus a few new ways. Skip those parts and you learn them the hard way in production.

</details>

<details markdown="1">
<summary>3. You finished Part 6, but you can't explain retries from memory or do its exercises without looking back. What now?</summary>

Re-read before moving on. The chapter's test is to explain the core idea out loud without notes and do the exercises without peeking — later parts assume earlier ones stuck.

</details>
