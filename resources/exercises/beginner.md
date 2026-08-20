# Beginner Exercises

Hands-on, cross-chapter tasks for readers who've completed Parts 1–5 (API Foundations through Authentication). These are larger than the exercises embedded at the end of each chapter — expect each one to take an hour or more, not five minutes.

## 1. Build a minimal REST API for a "notes" resource
**Relates to:** Part 1 (HTTP Foundations), Part 2 (REST API Design), Part 3 (Building APIs)

Using FastAPI, build `GET /notes`, `POST /notes`, `GET /notes/{id}`, `PATCH /notes/{id}`, `DELETE /notes/{id}` for a simple in-memory notes resource (`id`, `title`, `body`, `created_at`). Return the correct status code for each operation (`201` on create, `204` on delete, `404` for a missing note). Test every endpoint with `curl` and record the exact request/response for each.

## 2. Compare offset and cursor-based pagination
**Relates to:** Part 2 (Pagination)

Build a FastAPI endpoint over a list of 1,000 generated items that supports both `?offset=&limit=` and `?cursor=&limit=` pagination styles on the same underlying dataset. Write a short comparison (a few sentences) of what happens to each style's results if you insert 5 new items at the front of the dataset mid-pagination.

## 3. Add query parameter filtering and sorting
**Relates to:** Part 2 (Filtering and Sorting)

Extend the notes API from Exercise 1 to support `?search=`, `?sort=created_at` / `?sort=-created_at` (descending), and combine it with pagination. Validate that an invalid `sort` value returns a `400` with a clear error message rather than crashing.

## 4. Validate request bodies with Pydantic and produce good error messages
**Relates to:** Part 3 (Request Validation with Pydantic)

Add a Pydantic model to the notes API that requires `title` (1–200 characters) and `body` (max 10,000 characters). Send several intentionally invalid requests (missing field, wrong type, too-long title) and inspect FastAPI's default `422` error response. Then customize the exception handler so the error response returns a flatter, simpler JSON shape of your own design.

## 5. Build a health check endpoint
**Relates to:** Part 6 (Health Checks, Readiness and Liveness Probes)

Add `/healthz` (liveness — just confirms the process is running) and `/readyz` (readiness — confirms the app can actually serve traffic, e.g. it can reach its dependencies) endpoints to your API. Simulate a dependency being unavailable (e.g. a flag you can flip) and confirm `/readyz` correctly reports `503` while `/healthz` still reports `200`.

## 6. Implement API key authentication
**Relates to:** Part 5 (API Keys)

Add a simple API key auth scheme to your notes API: require an `X-API-Key` header, validate it against a small hardcoded set of valid keys, and return `401` if it's missing or invalid. Then move the valid keys out of source code into an environment variable.

## 7. Build a login flow with sessions
**Relates to:** Part 5 (Sessions and Cookies)

Build a minimal login endpoint that accepts a username/password (hardcoded user list is fine), creates a server-side session (an in-memory dict keyed by a random session ID is fine for this exercise), and sets the session ID in an `HttpOnly` cookie. Add a `/me` endpoint that reads the session cookie and returns the logged-in user, returning `401` if there's no valid session.

## 8. Add environment-based configuration
**Relates to:** Part 3 (Environment Variables, Configuration Management)

Refactor your notes API so all configuration (port, log level, API keys, database URL if you have one) is loaded from environment variables via a typed settings object (e.g. Pydantic `BaseSettings`), not hardcoded. Add a `.env.example` file documenting every required variable without real secret values.

## 9. Generate and inspect OpenAPI documentation
**Relates to:** Part 3 (API Documentation with OpenAPI)

Add proper docstrings, response models, and status code annotations to every endpoint in your notes API so the auto-generated OpenAPI docs (`/docs`) are actually useful — a new developer should be able to understand every endpoint's inputs and outputs from the docs alone, without reading the code.

## 10. Write your first status-code decision table
**Relates to:** Part 1 (Status Codes)

For 8 different scenarios of your choosing (e.g. "user submits a form with a missing required field", "user requests a resource they don't have permission to view", "user's request times out waiting on a slow dependency"), write down which HTTP status code you'd return and a one-sentence justification. Cross-check your answers against `resources/cheatsheets/status-codes.md`.

## 11. Implement basic rate limiting
**Relates to:** Part 6 (Rate Limiting)

Add a simple fixed-window rate limiter (e.g. 10 requests per minute per API key) to your notes API using an in-memory counter. Write a small script that sends 15 requests in quick succession and confirms the 11th onward gets a `429` with a `Retry-After` header.

## 12. Explore JWT structure hands-on
**Relates to:** Part 5 (JWT Deeply Explained)

Generate a JWT for a test user (using a library, not by hand) with `sub`, `exp`, and a custom claim of your choosing. Decode it (without verifying) at jwt.io or with a CLI tool and identify the header, payload, and signature sections. Then write code that verifies the signature and rejects a token whose `exp` has passed, and rejects a token whose payload was tampered with (change one character in the payload segment and confirm signature verification now fails).
