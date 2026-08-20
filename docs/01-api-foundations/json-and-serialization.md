# JSON and Serialization

## Why This Matters

Your Python program has objects, dictionaries, lists, and typed values living in memory. The client on the other end of an HTTP request has its own completely different in-memory representation, possibly in a different programming language entirely. **Serialization** is the process that bridges this gap — turning an in-memory data structure into bytes that can travel over the network, and **deserialization** turns those bytes back into a usable data structure on the other side. JSON is the format almost every modern API uses to do this, and understanding exactly what it can and can't represent precisely is what prevents an entire category of subtle bugs: numbers that silently lose precision, dates that get parsed inconsistently across languages, and fields that mean something different than you assumed.

## Core Concept

**JSON (JavaScript Object Notation)** is a lightweight, text-based data format for representing structured data. Despite the name, it's language-independent — virtually every programming language has a JSON library, which is exactly why it became the default choice for API bodies: it's simple enough to implement everywhere, human-readable enough to debug by eye, and expressive enough for most structured data.

JSON supports exactly six data types, and understanding that this list is *closed* — nothing else is valid JSON — is important:

- **String** — text, always in double quotes: `"hello"`.
- **Number** — no distinction between integer and float at the format level: `42`, `3.14`, `-7`.
- **Boolean** — `true` or `false` (lowercase, unquoted).
- **null** — represents "no value" (lowercase, unquoted) — distinct from an empty string, zero, or a missing field entirely.
- **Object** — an unordered set of key-value pairs, keys always strings: `{"name": "Ada", "age": 30}`.
- **Array** — an ordered list of values, which can be any JSON type, including mixed types: `[1, "two", true, null]`.

Notably absent: dates, binary data, and a distinction between integers and floating-point numbers. Every one of these gaps is a real, recurring source of bugs, covered below.

**Serialization** is turning a language-native object (a Python `dict`, a database row, a class instance) into a JSON string. **Deserialization** (sometimes called "parsing" or "decoding") is the reverse: turning a JSON string back into a language-native object.

## Mental Model

Think of JSON like a universal shipping crate standard used at every port in the world, regardless of what country ships from or receives at that port. It doesn't matter if the sender packs the crate using metric tools and the receiver unpacks it with imperial tools — as long as both sides agree on the crate's external shape (JSON's fixed six types), the contents transfer correctly. But the crate standard itself doesn't understand *what's inside* — if you ship a car engine (a Python `datetime` object, a binary image file) that doesn't fit the crate's standard shape, you as the shipper have to first take it apart into crate-compatible pieces (serialize it to a string, or base64-encode binary data) before it can travel, and the receiver has to know how to reassemble it (deserialize/parse) back into something meaningful on their end.

## How It Works

**JSON syntax** — a JSON document is either a single value or, in practice for APIs, almost always a top-level object or array:

```json
{
  "id": 42,
  "name": "Priya Sharma",
  "active": true,
  "balance": 105.5,
  "tags": ["premium", "verified"],
  "manager": null,
  "address": {
    "city": "Bengaluru",
    "zip": "560001"
  }
}
```

Strict rules that trip people up: keys and string values must use **double quotes** (not single quotes), there's **no trailing comma** allowed after the last item in an object or array, and comments are **not** part of the JSON spec at all (some parsers accept them as an extension, but standard JSON doesn't).

**The classic pitfalls**, all stemming from JSON's closed, minimal type system:

- **Dates/times have no native type.** JSON has no `Date` type — dates are almost always represented as strings, conventionally in **ISO 8601** format (`"2026-08-18T09:12:00Z"`), but this is a *convention*, not something JSON enforces. Different APIs sometimes use Unix timestamps (a number) instead — always check the API's documentation rather than assuming.
- **Numbers don't distinguish int from float, and have precision limits.** `42` and `42.0` are both just "Number" in JSON — many JSON parsers (including JavaScript's, since numbers there are IEEE 754 doubles) can't safely represent integers larger than 2^53 exactly. A large database ID or a 64-bit integer can silently lose precision when round-tripped through JSON in a language with this limitation — a real, recurring bug in systems that pass large numeric IDs between JavaScript and other languages. The common fix is to send very large integers as strings instead of numbers.
- **`null` vs. missing key vs. empty value are three different things.** `{"email": null}` (field present, explicitly no value), `{}` (field absent entirely), and `{"email": ""}` (field present, empty string) mean three different things and a well-designed API must be explicit about which one it uses and why — this distinction matters enormously for `PATCH` semantics (see [HTTP Methods](http-methods.md)): "field omitted" often means "don't change it," while "field explicitly null" often means "clear it."
- **No native binary type.** Binary data (images, files) must be encoded as text first, typically via **Base64**, which inflates size by roughly 33% — for large binary payloads, a non-JSON body format (like `multipart/form-data`, see [Request & Response Bodies](request-response.md)) is usually a better choice than embedding Base64 inside JSON.
- **Key order is not guaranteed to be meaningful.** JSON objects are formally unordered; while most real-world parsers preserve insertion order in practice, you shouldn't design an API that depends on key order carrying meaning.

## Architecture

```mermaid
flowchart LR
    subgraph Server
        P[Python object<br/>dict / Pydantic model]
    end
    P -->|serialize / encode| J["JSON text\n{\"id\": 42, ...}"]
    J -->|sent as HTTP body| Wire[( )]
    Wire -->|received| J2[JSON text]
    subgraph Client
        J2 -->|deserialize / parse| O[Native object<br/>in client's language]
    end
```

The JSON text in the middle is the only thing that actually crosses the network — both sides independently convert to/from their own native representations around that shared, language-neutral format.

## Request / Response Example

A request with a JSON body demonstrating several of the pitfalls above in one realistic payload:

```http
POST /api/v1/orders HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Length: 189

{
  "order_id": "9007199254741337",
  "item": "Widget",
  "quantity": 2,
  "price": 19.99,
  "placed_at": "2026-08-18T09:12:00Z",
  "gift_message": null,
  "discount_code": "",
  "tags": ["urgent", "gift"]
}
```

Notice `order_id` is sent as a **string**, not a number — deliberately, because it's a large integer that could lose precision if some downstream JSON parser (e.g., JavaScript) treats it as a native number. `gift_message: null` (explicitly no message) and `discount_code: ""` (a code field that's present but empty) are deliberately different from each other and from omitting either field entirely.

## Code Example

Python's built-in `json` module handles serialization/deserialization, and Pydantic (used throughout this handbook's FastAPI examples) adds validation and typed parsing on top:

```python
import json
from datetime import datetime, timezone

data = {
    "id": 42,
    "name": "Priya Sharma",
    "active": True,          # Python's True → JSON's true
    "balance": 105.5,
    "tags": ["premium", "verified"],
    "manager": None,         # Python's None → JSON's null
    "created_at": datetime.now(timezone.utc).isoformat(),  # datetime has no JSON type — serialize explicitly
}

# Serialize: Python dict -> JSON string
json_text = json.dumps(data, indent=2)
print(json_text)

# Deserialize: JSON string -> Python dict
parsed = json.loads(json_text)
print(type(parsed["created_at"]))  # still a str — json.loads never re-parses it back into a datetime automatically
```

Pydantic (FastAPI's validation layer) automates this correctly, including datetime parsing:

```python
from pydantic import BaseModel
from datetime import datetime


class OrderIn(BaseModel):
    order_id: str          # deliberately a string — see the precision pitfall above
    item: str
    quantity: int
    price: float
    placed_at: datetime    # Pydantic parses ISO 8601 strings into real datetime objects
    gift_message: str | None = None  # None (JSON null) is a valid, distinct value here


raw_json = '''
{
  "order_id": "9007199254741337",
  "item": "Widget",
  "quantity": 2,
  "price": 19.99,
  "placed_at": "2026-08-18T09:12:00Z",
  "gift_message": null
}
'''

order = OrderIn.model_validate_json(raw_json)
print(order.placed_at, type(order.placed_at))  # a real datetime object, not a string
print(order.gift_message)                       # None
```

## Production Considerations

- **Pick and document a consistent date/time convention** (ISO 8601 in UTC is the strong default) across your entire API — mixing conventions across endpoints is a common source of client-side bugs.
- **Guard against large-integer precision loss** if any client might be JavaScript-based (browsers, Node.js services) — send large IDs as strings, or use a numeric type your consumers can safely handle.
- **Be deliberate about `null` vs. omitted fields**, especially in `PATCH` endpoints — document explicitly whether omitting a field means "no change" and whether `null` means "clear this field," and keep that contract consistent across your API.
- **Validate, don't just parse.** `json.loads` only checks that input is syntactically valid JSON — it says nothing about whether the *data* is valid for your application (right types, required fields present, values in range). That's what Pydantic validation (Part 3) is for, and skipping it is a common source of subtle bugs and security issues.
- **Watch payload size for large arrays.** JSON is verbose relative to binary formats — for very large datasets, consider pagination (Part 2) rather than one enormous JSON array.

## Common Mistakes

- **Assuming JSON numbers behave like your language's native integer type.** In JavaScript specifically, this causes real precision bugs with large IDs; always verify how your actual client-side language handles large numbers before choosing a numeric type.
- **Treating `null` and "field not present" as interchangeable.** They're semantically different and matter enormously for `PATCH` request design — conflating them leads to APIs where clients can't reliably express "leave this field alone" versus "clear this field."
- **Forgetting that JSON has no native date type.** Sending a Python `datetime` object directly to `json.dumps` raises a `TypeError` — it must be explicitly converted to a string (`.isoformat()`) first, which is exactly what Pydantic automates for you.
- **Writing JSON with trailing commas or single-quoted strings**, especially when hand-writing example payloads or test fixtures — these are invalid JSON and will fail to parse, even though they're valid in Python or JavaScript object literals.

## Best Practices

- Standardize on ISO 8601 (UTC) for all date/time fields across your API.
- Send large integers (IDs, especially 64-bit values) as JSON strings if any consumer might be JavaScript-based.
- Use a schema/validation layer (Pydantic) rather than trusting that syntactically valid JSON is also semantically valid for your application.
- Be explicit in your API documentation about the meaning of `null` versus an omitted field for every optional field, especially on `PATCH` endpoints.

## AI Engineering Perspective

JSON is the backbone of LLM API interaction in two distinct ways: it's the format of the request/response for chat completions themselves, and — increasingly important — it's the target format for **structured outputs**, where you ask a model to return data conforming to a specific **JSON Schema** rather than free-form text (covered in depth in [Part 14 — AI API Engineering](../14-ai-api-engineering/README.md)). This is exactly where the pitfalls in this chapter become sharp in practice: an LLM asked to return a large ID might return it as a JSON number and silently lose precision the same way a JavaScript client would; a model generating a `null` versus omitting a field entirely can change how your application code should react; and function/tool calling (Part 14, Part 17) relies on the model correctly serializing its intended arguments as JSON that your code then deserializes and validates before executing anything — making strict, careful deserialization *and* validation (not just parsing) a genuine security boundary, not just a data-hygiene concern, when the JSON in question came from a model rather than a trusted client.

## Exercises

**Beginner**
1. Identify which of the following are valid JSON, and fix the ones that aren't: `{'name': 'Ada'}`, `{"active": True}`, `{"tags": ["a", "b",]}`, `{"score": 9.5}`.
2. Explain the difference between `{"email": null}`, `{"email": ""}`, and `{}` (field omitted).

**Intermediate**
3. Using the Pydantic `OrderIn` example, add a field `updated_at: datetime | None = None` and write two example JSON payloads: one where the field is omitted, one where it's explicitly `null`. Confirm both parse successfully and explain when each would be appropriate for a `PATCH` endpoint.

**Advanced**
4. You're designing an API returning a 70-digit account balance for a financial system, where exact precision matters and the primary client is a JavaScript frontend. Explain, concretely, why sending this value as a JSON number is risky, and propose two different design solutions, with trade-offs.

## Key Takeaways

- JSON supports exactly six data types (string, number, boolean, null, object, array) — no native date, no int/float distinction, no binary type — and every API design pitfall in this chapter stems from working around that closed type system.
- Serialization converts native objects to JSON text for transport; deserialization converts JSON text back to native objects on the receiving side — and syntactic parsing is not the same as semantic validation.
- `null`, an empty value, and an omitted field are three distinct concepts that a well-designed API must treat deliberately, especially for `PATCH` semantics.
- Large integers and dates need deliberate, documented conventions (strings for large IDs, ISO 8601 for dates) because JSON itself doesn't enforce either.
- LLM structured outputs and tool/function calling are built directly on JSON serialization — validate model-generated JSON with the same rigor as any untrusted client input.
