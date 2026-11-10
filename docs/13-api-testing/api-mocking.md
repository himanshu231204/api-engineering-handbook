# API Mocking

> [!TIP]
> **In one line:** Mocking replaces slow, costly, or unreliable external HTTP dependencies with controllable stand-ins in tests, but stand-ins drift from reality unless a contract or recorded response keeps them honest.
>
> **In plain English:** When rehearsing a play, you do not wait for the famous guest star to be free; an understudy reads their lines so everyone else can practise. A mock is the understudy for another service. It lets you rehearse your own code at any hour, including the day the star is "ill", as long as you occasionally check the understudy still says the real lines.
>
> **You'll be able to:** choose between stubs, mocks, and fakes · mock outbound HTTP with respx or pytest-httpx and simulate errors and timeouts · keep mocks truthful with recorded responses and contract tests

## Why This Matters

Almost every API you build calls other APIs: a payment processor, an email service, a geocoder, an identity provider, another team's microservice, and increasingly an LLM provider. Calling the real thing from tests has predictable problems. It is slow (hundreds of milliseconds per call, multiplied across a suite), flaky (the provider has an outage and your build goes red), rate limited, sometimes billed (an LLM test suite can cost real money on every push), and unable to produce the awkward cases you most need to test: a timeout, a `503`, a malformed body, a duplicate webhook, a response that arrives after the client gave up. You cannot ask a payment provider to fail on demand.

So tests substitute something for the real dependency. The craft is in what you substitute, where you cut, and how you stop the substitute from becoming a comfortable lie. A mock that returns a response shape the provider changed six months ago produces a test suite that is green and a feature that is broken. Good mocking makes tests fast and deterministic; disciplined mocking keeps them truthful.

## Core Concept

Test doubles come in several kinds, and the words are often used loosely. Using them precisely helps you pick the right one.

| Double | What it does | Example |
|---|---|---|
| **Stub** | Returns canned answers; no logic, no verification | `GET /rates` always returns `{"usd": 1.0}` |
| **Mock** | A stub that also records calls so the test can assert how it was used | Assert the charge call was made once with amount `1999` |
| **Fake** | A simplified but working implementation | An in-memory payment provider that tracks charges and enforces idempotency keys |
| **Spy** | Wraps the real thing and records calls | Real client, plus a record of requests it sent |
| **Recorded / replayed** | Real responses captured once, replayed later | A saved JSON file of a real provider response |

**Where you cut** matters as much as what you use. You can substitute at three layers:

1. **At your own abstraction.** Define an interface (a Python `Protocol`) such as `PaymentGateway` and inject a fake implementation. Tests do not touch HTTP at all. This is simple and fast, but the real HTTP adapter, which contains the URL, headers, serialization and error mapping, is untested.
2. **At the HTTP boundary.** Keep the real client code and intercept requests at the transport level, returning scripted responses. This tests your adapter's real request-building and response-parsing code. For `httpx` the common tools are `respx` and `pytest-httpx`; for the `requests` library the equivalent is `responses`; for `aiohttp` there is `aioresponses`.
3. **A stand-in server.** Run a real HTTP server (a small fake service or a tool like WireMock) that your code connects to over the network. This is the most realistic and also used by other languages' clients, at the cost of running another process.

A good test suite uses both of the first two: the interface-level fake in most business-logic tests, and HTTP-boundary mocks in a few focused tests of the adapter itself.

## Mental Model

A flight simulator is a mock of an aeroplane. It is excellent for rehearsing engine failure because it can produce one on demand, and no real plane is needed. But a simulator built from last decade's aircraft manual trains pilots for a plane that no longer exists. The simulator is only as good as its fidelity, so serious operators compare it against real flight data regularly. Your mocks need the same recalibration against the real provider.

## How It Works

**Mocking at the HTTP boundary with respx.** `respx` patches `httpx`'s transport layer. You declare routes with a method and URL and attach a response or side effect:

- `respx.mock` is a context manager or decorator that activates the routing. By default any request that does not match a declared route raises an error, which is what you want: an unexpected outbound call is a bug, not something to pass silently. `assert_all_called=True` additionally fails the test if a declared route was never called, catching stale mocks.
- `router.post("https://api.pay.test/v1/charges").mock(return_value=httpx.Response(201, json={...}))` returns a fixed response.
- `side_effect` can be an exception class (`httpx.ConnectTimeout`), an exception instance, a function that builds a response from the request, or a list for a sequence, for example `[httpx.Response(503), httpx.Response(200)]` to test that retry works.
- The returned route has `.called`, `.call_count`, and `.calls.last.request`, so you can assert what your code actually sent.

`pytest-httpx` offers the same idea as a pytest fixture: the `httpx_mock` fixture, with `add_response(...)` and `add_exception(...)` and `get_requests()`. In recent versions it fails the test if a registered response was never requested or if an unregistered request is made, which is strict by default. Check the version you install for its exact defaults.

**Simulate the awkward cases deliberately.** The reason to mock at all is control, so write tests for failures: timeouts (`httpx.ReadTimeout`), connection errors, `429` with `Retry-After`, `500`/`503`, a `200` with a malformed or incomplete JSON body, a slow success, an unexpected extra field, and a duplicated webhook. Whether your code maps each to the right behaviour (retry, fallback, a clear `502` to your own caller) is what these tests verify.

**Recording and replaying.** Writing every response by hand is tedious and error-prone. The alternative is to capture real interactions once and replay them in tests. Tools in this family (for example `vcrpy` and the `pytest-recording` plugin for Python) record HTTP exchanges to a "cassette" file the first time and serve them from the file afterwards. Benefits: realistic shapes with no hand-writing, and diffs when you re-record. Costs: recorded files contain whatever the provider sent, so scrub secrets and personal data (filter authorization headers and tokens before committing), and cassettes go stale, so re-record on a schedule or when upgrading a client library. A lightweight manual version of the same idea is to save a few real responses as JSON fixtures and load them into your mocks.

**Fakes for stateful dependencies.** Some flows need behaviour: create a charge, then fetch it, then refund it. Scripting each response is brittle; an in-memory fake that implements the handful of operations you use is clearer. A fake can enforce rules that matter, such as idempotency keys, and can be shared across test suites. The trade-off is that you now maintain a second, simplified implementation, so keep it small and test it against the real thing where possible.

**Mocking LLM providers deterministically.** Model APIs are the extreme case: non-deterministic, slow, billed per token, and rate limited. For tests of your own logic, replace the model with a deterministic fake. Either substitute at your own abstraction (an `LLMClient` protocol with a `FakeLLM` returning scripted completions or tool calls in order) or intercept at the HTTP boundary with a response shaped like the provider's, including streaming chunks. Turning temperature down does not make a real model deterministic enough for exact assertions, so do not rely on it for unit tests. Scripted fakes let you assert your prompt construction (what you sent), your parsing (what you do with the reply), your retries, and your handling of refusals, truncation, malformed JSON, and tool-call loops, none of which need a real model. Quality of the real model's answers is a separate evaluation problem, handled offline with evaluation datasets.

**Drift: the central risk.** A mock encodes your belief about the provider. If the provider changes (a renamed field, a new required header, a different error body) your mock does not notice, and the tests stay green. Mitigations:

- **Contract tests** verify your mock against reality. A consumer-driven contract, as in [contract-testing.md](contract-testing.md), is exactly a checked description of the mock's responses, verified against the real provider (or its published OpenAPI spec). If the provider is an internal service, the owning team verifies your contract.
- **Generate mocks from the provider's OpenAPI spec** where one exists, and validate every mocked response body against the spec's schema inside the test helper, so a hand-written mock that violates the spec fails immediately.
- **A small number of live tests** run on a schedule (not on every push) against the provider's sandbox, which detect drift. See [end-to-end-testing.md](end-to-end-testing.md) for keeping them isolated.
- **Re-record cassettes** periodically and review the diff.

**Do not mock what you own.** Mocking your own database or your own code removes the thing you want to test; use a real test database for that ([test-databases.md](test-databases.md)) and reserve mocks for external systems at the edge of your service.

## Architecture

```mermaid
flowchart TB
    subgraph T["Test process"]
        BL["Business logic\n(depends on PaymentGateway protocol)"]
        AD["HTTP adapter\n(real httpx code)"]
        BL --> AD
    end
    AD -->|"production"| EXT["Real provider API"]
    AD -->|"adapter test"| RX["respx / pytest-httpx\nscripted responses"]
    BL -->|"logic test"| FK["In-memory fake\nimplementing the protocol"]
    RX -.->|"verified by"| CT["Contract test /\nOpenAPI schema check"]
    CT -.-> EXT
```

```mermaid
sequenceDiagram
    participant D as "Dev"
    participant R as "Recorder"
    participant P as "Real provider"
    participant C as "CI test run"
    D->>R: run tests with record mode on
    R->>P: real request (sandbox)
    P-->>R: real response
    R->>R: scrub secrets, save cassette file
    C->>R: replay mode
    R-->>C: saved response, no network
```

## Request / Response Example

A scripted exchange for testing retry behaviour against a flaky payments provider. First the provider answers with a transient failure.

```http
POST /v1/charges HTTP/1.1
Host: api.pay.test
Authorization: Bearer test_key_placeholder
Idempotency-Key: order-1001
Content-Type: application/json

{"amount": 1999, "currency": "usd", "source": "tok_visa"}
```

```http
HTTP/1.1 503 Service Unavailable
Retry-After: 1
Content-Type: application/json

{"error": {"type": "api_error", "message": "temporarily unavailable"}}
```

The mock then returns success for the retry, and the test asserts that both requests carried the same `Idempotency-Key`.

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": "ch_3Qx91", "status": "succeeded", "amount": 1999, "currency": "usd"}
```

The second response is the shape you should copy from the provider's real documentation or a recorded sandbox call, not from memory.

## Code Example

A payment adapter that retries once on `503`, tested at the HTTP boundary with `respx`, and a business-logic test using an interface-level fake. The same pattern applies to an LLM client. Tests are plain functions using `asyncio.run` so they need no async pytest plugin. The base URL and API key come from the environment in production code.

```python
# payments.py
import os
from typing import Protocol

import httpx


class PaymentGateway(Protocol):
    """Your own abstraction; business logic depends on this, not on httpx."""
    async def charge(self, amount: int, currency: str, order_id: str) -> str: ...


class HttpPaymentGateway:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def charge(self, amount: int, currency: str, order_id: str) -> str:
        last: httpx.Response | None = None
        for _ in range(2):                                   # one retry on 503
            last = await self._client.post(
                "/v1/charges",
                json={"amount": amount, "currency": currency},
                headers={"Idempotency-Key": order_id},       # same key on retry: safe
            )
            if last.status_code != 503:
                break
        assert last is not None
        last.raise_for_status()
        return last.json()["id"]


def make_gateway() -> HttpPaymentGateway:
    client = httpx.AsyncClient(
        base_url=os.environ.get("PAYMENTS_BASE_URL", "https://api.pay.test"),
        headers={"Authorization": f"Bearer {os.environ['PAYMENTS_API_KEY']}"},
        timeout=httpx.Timeout(5.0),
    )
    return HttpPaymentGateway(client)


class FakeGateway:
    """In-memory fake: stateful, enforces idempotency, no HTTP."""
    def __init__(self) -> None:
        self.charges: dict[str, str] = {}

    async def charge(self, amount: int, currency: str, order_id: str) -> str:
        return self.charges.setdefault(order_id, f"ch_fake_{len(self.charges) + 1}")


async def place_order(gateway: PaymentGateway, order_id: str, amount: int) -> dict:
    charge_id = await gateway.charge(amount, "usd", order_id)
    return {"order_id": order_id, "charge_id": charge_id, "status": "paid"}
```

```python
# test_payments.py
import asyncio
import json

import httpx
import pytest
import respx

from payments import FakeGateway, HttpPaymentGateway, place_order

BASE = "https://api.pay.test"


def test_adapter_retries_503_and_reuses_idempotency_key():
    async def run():
        # assert_all_called fails the test if a declared route is never hit;
        # unmatched requests raise, so unexpected calls cannot pass silently.
        with respx.mock(base_url=BASE, assert_all_called=True) as router:
            route = router.post("/v1/charges").mock(side_effect=[
                httpx.Response(503, json={"error": {"type": "api_error"}}),
                httpx.Response(201, json={"id": "ch_3Qx91", "status": "succeeded"}),
            ])
            async with httpx.AsyncClient(base_url=BASE) as client:
                charge_id = await HttpPaymentGateway(client).charge(1999, "usd", "order-1001")
            assert charge_id == "ch_3Qx91"
            assert route.call_count == 2
            keys = {c.request.headers["Idempotency-Key"] for c in route.calls}
            assert keys == {"order-1001"}                      # what we actually sent
            assert json.loads(route.calls.last.request.content)["amount"] == 1999
    asyncio.run(run())


def test_adapter_surfaces_timeout():
    async def run():
        with respx.mock(base_url=BASE) as router:
            router.post("/v1/charges").mock(side_effect=httpx.ConnectTimeout)
            async with httpx.AsyncClient(base_url=BASE) as client:
                with pytest.raises(httpx.ConnectTimeout):
                    await HttpPaymentGateway(client).charge(1999, "usd", "order-1002")
    asyncio.run(run())


def test_business_logic_with_fake_is_idempotent():
    gw = FakeGateway()
    a = asyncio.run(place_order(gw, "order-7", 500))
    b = asyncio.run(place_order(gw, "order-7", 500))          # retried request
    assert a["charge_id"] == b["charge_id"] and len(gw.charges) == 1
```

For an LLM client the shape is identical: define `class LLM(Protocol): async def complete(self, messages) -> str`, implement `FakeLLM` that pops scripted replies from a list (including a malformed-JSON reply and a tool-call reply), and keep one small `respx` test of the real adapter against a response copied from the vendor's documentation.

## Production Considerations

- **Strict by default.** Configure mocks to fail on unmatched requests and on unused routes. Silent pass-through to the real network is how tests start calling production providers.
- **Block the network in unit tests.** Plugins such as `pytest-socket` can disable real sockets so an unmocked call fails loudly instead of slowly. Allow localhost only for tests that need a test database.
- **Validate mocks against the spec.** Run mocked response bodies through the provider's OpenAPI schema or your Pydantic response models in a helper so an impossible mock cannot be written.
- **Cassette hygiene.** Redact authorization headers, tokens, emails, and any personal data before committing recorded files; treat them as code that needs review.
- **Keep the sandbox smoke tests.** A few scheduled tests against the real sandbox detect drift that mocks cannot, and they should alert rather than block merges.
- **Ownership.** A shared fake for a widely used internal service should be owned and versioned by that service's team, so consumers do not each invent a divergent fiction.
- **Cost control.** For LLM suites, a mocked default with a clearly marked opt-in live suite avoids surprise bills and flaky builds.

## Common Mistakes

- **Mocking so much that the test proves nothing.** A test that mocks the service layer, the repository, and the client, then asserts the mocks were called, only tests the test. Mock at the edge and assert on outcomes.
- **Hand-written responses from memory.** The mock matches your assumption, not the provider; copy from docs or recordings.
- **No failure cases.** Mocks that only ever return happy responses waste their main advantage.
- **Letting mocks drift** with no contract test, schema validation, or live check.
- **Asserting implementation details,** such as exact call order or internal helper calls, so refactors break tests without breaking behaviour.
- **Committing recordings with secrets** or real customer data.
- **Mocking your own database** instead of using a disposable real one.

## Best Practices

- Define your own interface for each external dependency and inject it; use fakes there for business-logic tests.
- Test the real HTTP adapter at the transport level with respx or pytest-httpx, covering success, each error class, timeouts, and malformed bodies.
- Make unmatched requests and unused mocks failures.
- Copy response shapes from provider documentation or recordings and validate them against a schema.
- Pair every important mock with a contract test or scheduled sandbox check; see [contract-testing.md](contract-testing.md).
- Keep fakes small and test them against the behaviour they claim to imitate.
- Use deterministic scripted fakes for LLM calls and reserve real-model checks for a small opt-in suite.

## AI Engineering Perspective

LLM calls are where mocking earns its keep: tokens cost money, latency is seconds, and output varies run to run. A scripted `FakeLLM` lets you test the deterministic machinery around the model, such as prompt assembly, retrieval context injection, JSON parsing and repair, tool-call dispatch, loop limits, and fallback to a second provider, with exact assertions. Include scripted pathologies: a refusal, a reply truncated at the token limit, invalid JSON, a tool call with the wrong argument types, a stream that ends early, and a `429`. Provider response formats do change, and the model's behaviour changes more often than its schema, so keep a few recorded real responses to check your parser against, and run a small, budget-capped live evaluation separately. See [Part 14](../14-ai-api-engineering/README.md) for provider APIs and streaming formats, [Part 15](../15-production-ai-systems/README.md) for gateways and fallback chains, and [Part 17](../17-ai-agents-and-mcp/README.md) for tool-call loops.

## Exercises

**Beginner**
1. Write a respx test for a client function that calls `GET /rates/usd`. Add a second test where the route returns `500` and assert your function raises the exception you chose.

**Intermediate**
2. Add a test that the adapter does not retry on `400`. Then switch the test to `pytest-httpx` and note the differences in setup and strictness.
3. Build a `FakeLLM` that returns a list of scripted replies, one with malformed JSON, and test that your parsing layer retries once and then raises a clear error.

**Advanced**
4. Design a drift-detection strategy for a mocked third-party API: what runs on every push, what runs nightly against the sandbox, how mocks are validated against the OpenAPI spec, and who is alerted.

## Key Takeaways

- Choose the right double: stubs return canned data, mocks also verify calls, fakes implement simplified behaviour.
- Mock at your own interface for business logic and at the HTTP transport for adapter tests, and fail on unexpected or unused routes.
- Spend your mocks on failure cases (timeouts, `5xx`, malformed bodies), which real providers cannot produce on demand.
- Mocks drift from reality; contract tests, schema validation, and scheduled sandbox checks are the antidote.

### Check Yourself
<details markdown="1">
<summary>1. What is the difference between a stub, a mock, and a fake?</summary>

A stub returns canned answers, a mock is a stub that also records calls so you can assert how it was used, and a fake is a simplified working implementation (for example an in-memory service). Fakes carry behaviour and state; stubs and mocks mostly do not.

</details>

<details markdown="1">
<summary>2. Why should an HTTP mock fail on requests that match no declared route?</summary>

An unmatched request means the code made a call the test did not anticipate. Letting it pass through could hit the real provider (slow, costly, flaky) or hide a bug, so failing loudly keeps tests hermetic and surfaces the surprise.

</details>

<details markdown="1">
<summary>3. Your payment provider renames a response field, all your tests stay green, and checkout breaks in production. What went wrong and how do you prevent it?</summary>

The mock encoded an outdated shape, so tests never saw the change. Verify mocks against the provider's contract or OpenAPI schema, add contract tests, and run a scheduled live sandbox check that alerts when the real response no longer matches.

</details>

---
Back to the [Part 13 README](README.md).
