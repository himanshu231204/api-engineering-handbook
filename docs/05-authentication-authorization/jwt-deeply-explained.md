# JWT Deeply Explained

## Why This Matters

JSON Web Tokens (JWTs) are everywhere in modern API authentication — they're the default access token format for OAuth 2.0, the standard output of Firebase Auth, Auth0, AWS Cognito, and most homegrown auth systems. They're also one of the most commonly *misimplemented* security mechanisms in the industry: a huge share of real-world JWT vulnerabilities come not from the format itself but from verification code that trusts fields it shouldn't. Understanding the format precisely — not just "it's a token with some JSON in it" — is what separates code that's actually secure from code that merely looks secure.

## Core Concept

A **JWT** is a compact, URL-safe string representing a set of **claims** (statements about a subject — typically a user), **cryptographically signed** so that any tampering is detectable. It is not encrypted by default — a plain JWT (a JWS, JSON Web *Signature*) is signed, not confidential; anyone who has the token can read its contents by decoding the payload, they just can't *modify* it undetected without invalidating the signature. (JWTs can optionally be encrypted using JWE, but this is far less common than the signed JWS form covered here.)

A JWT consists of exactly three parts, base64url-encoded and joined by dots:

```
header.payload.signature
```

- **Header**: metadata — the signing algorithm (`alg`) and token type (`typ`).
- **Payload**: the claims — arbitrary JSON, including standard registered claims like `sub` (subject), `exp` (expiry), `iat` (issued at), `iss` (issuer), `aud` (audience), plus any custom claims your application needs (roles, scopes, tenant ID).
- **Signature**: computed over `base64url(header) + "." + base64url(payload)` using the algorithm named in the header and a secret or private key. This is what the verifier checks to confirm the token wasn't tampered with and was issued by someone holding the signing key.

## Mental Model

Think of a JWT like a **wax-sealed letter with the contents visible through a clear envelope**. Anyone who picks up the letter can read every word inside — there's no secrecy. But the wax seal (the signature) proves it came from whoever holds the original seal stamp (the signing key), and any attempt to alter the letter's text breaks the seal in a way that's obviously detectable when the recipient checks it. This is why you must never put secrets you don't want exposed (passwords, unmasked card numbers) directly into a JWT payload — "signed, not secret" is the core property to internalize.

## How It Works

### Encoding

1. Build the header: `{"alg": "HS256", "typ": "JWT"}`.
2. Build the payload: `{"sub": "user_123", "exp": 1720003600, "role": "admin"}`.
3. Base64url-encode both, join with a dot: `header_b64.payload_b64`.
4. Compute the signature over that string using the chosen algorithm and key, base64url-encode it, and append: `header_b64.payload_b64.signature_b64`.

### Signing algorithms: HS256 vs RS256

- **HS256 (HMAC-SHA256)**: a **symmetric** algorithm — the same secret key both signs and verifies the token. Simple, fast, but means *every service that needs to verify tokens also needs the signing secret* — which means every one of those services could also mint valid tokens. Fine for a single monolithic auth service verifying its own tokens; risky to share widely.
- **RS256 (RSA-SHA256)**: an **asymmetric** algorithm — a private key signs, and the corresponding public key verifies. The private key stays only on the auth server; any number of downstream services can verify tokens using the public key without ever being able to mint new ones. This is the standard choice for distributed/microservice systems and is what OAuth providers and OpenID Connect use, publishing their public keys via a JWKS (JSON Web Key Set) endpoint.

Choosing HS256 when you actually have multiple independent services verifying tokens is a common architectural mistake — it forces you to distribute a secret that, if any one service is compromised, lets an attacker forge tokens for your entire system.

### Verification

A correct verifier must, in order:

1. Parse the token's three parts.
2. **Determine the algorithm from server-side configuration, not from the token's own `alg` header.** This is the single most important rule in JWT verification (see Common Mistakes below).
3. Recompute the signature using the pinned algorithm and the correct key, and compare it to the signature in the token.
4. Reject if the signature doesn't match.
5. Check standard claims: `exp` (has it expired?), `nbf` (not valid before, if present), `iss` (was it issued by the expected issuer?), `aud` (was it issued for this service?).
6. Only after all of the above passes, trust the payload's claims.

### Why JWTs can't be trivially revoked

Because a JWT's validity is determined entirely by its signature and embedded expiry — with no server-side lookup — there is no built-in way to invalidate a specific token before it naturally expires. If a user's account is compromised, or a token leaks, or a user logs out, the JWT itself remains cryptographically "valid" until `exp` passes. Common mitigations:

- **Keep access token lifetimes short** (minutes, not days) so the exposure window is small — see [Access vs Refresh Tokens](access-vs-refresh-tokens.md).
- **Maintain a server-side denylist/blocklist** of revoked token IDs (`jti` claim) checked on each request — this reintroduces a lookup, partially trading away the "stateless" benefit for revocability.
- **Rotate the signing key**, which invalidates *every* token signed with the old key at once — a blunt instrument, but effective for a suspected mass compromise.

## Architecture

```mermaid
sequenceDiagram
    participant Auth as Auth Server
    participant Client
    participant API as Resource Server

    Note over Auth: Holds private signing key (RS256)\nor shared secret (HS256)
    Client->>Auth: POST /login (credentials)
    Auth->>Auth: Verify credentials
    Auth->>Auth: Build header + payload
    Auth->>Auth: Sign: header_b64.payload_b64 -> signature
    Auth-->>Client: JWT: header.payload.signature

    Client->>API: GET /resource\nAuthorization: Bearer <JWT>
    Note over API: Holds public key (RS256)\nor shared secret (HS256) - never the private key
    API->>API: 1. Pin expected alg (server config, NOT token header)
    API->>API: 2. Recompute signature, compare
    API->>API: 3. Check exp, iss, aud claims
    alt Signature invalid or expired
        API-->>Client: 401 Unauthorized
    else Valid
        API->>API: Trust payload claims (sub, role, ...)
        API-->>Client: 200 OK + resource
    end
```

## Request / Response Example

A JWT split into its three parts (this is a real, decodable — but not usable — example structure):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.
eyJzdWIiOiJ1c2VyXzEyMyIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTcxOTk5OTIwMCwiZXhwIjoxNzIwMDAwMTAwfQ
.
TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ
```

Decoded header:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

Decoded payload:

```json
{
  "sub": "user_123",
  "role": "admin",
  "iat": 1719999200,
  "exp": 1720000100
}
```

Using it as a bearer token:

```http
GET /v1/admin/reports HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTcxOTk5OTIwMCwiZXhwIjoxNzIwMDAwMTAwfQ.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ
```

A rejection because the token expired:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{"error": "token_expired", "message": "JWT exp claim is in the past"}
```

## Code Example

```python
import os
import time
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

app = FastAPI()
bearer_scheme = HTTPBearer()

# Load the signing key from the environment - never hardcode it in source.
# For HS256 this is a shared secret; for RS256 this would be a private key
# (signing) and a separate public key (verification).
JWT_SECRET = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
ISSUER = "https://auth.example.com"
AUDIENCE = "example-api"


def create_access_token(user_id: str, role: str, ttl_seconds: int = 900) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + ttl_seconds,  # short-lived - 15 minutes here
        "iss": ISSUER,
        "aud": AUDIENCE,
    }
    # jose.jwt.encode sets the "alg" header for us based on the algorithm we pass -
    # this is fine on the ENCODING side; the danger is only on the decoding side.
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        # CRITICAL: `algorithms=[ALGORITHM]` pins the algorithm the server will
        # accept. jose will REJECT a token whose header claims a different
        # algorithm (e.g. "alg": "none" or "alg": "RS256" when we expect HS256).
        # Never derive the algorithm to use from the token itself - that is
        # exactly the "alg: none" / algorithm-confusion vulnerability class.
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.post("/login")
async def login(username: str, password: str):
    user = authenticate(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user_id=user["id"], role=user["role"])
    return {"access_token": token, "token_type": "bearer", "expires_in": 900}


@app.get("/v1/admin/reports")
async def admin_reports(claims: dict = Depends(verify_access_token)):
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return {"reports": ["q1-revenue", "q2-revenue"]}


def authenticate(username: str, password: str) -> dict | None:
    return {"id": "user_123", "role": "admin"} if username and password else None
```

## Production Considerations

- **Always pin the algorithm on the verifying side.** Libraries that let you omit the `algorithms` parameter and "trust" the token's own header are dangerous — configure it explicitly, every time.
- **Keep access-token lifetimes short** (minutes) precisely because revocation is hard; pair with a [refresh token](access-vs-refresh-tokens.md) for longer sessions.
- **Use RS256 (or ES256) for multi-service systems**, distributing only the public key to verifiers, keeping the private signing key confined to the auth server.
- **Set and verify `iss` and `aud`.** Without them, a token issued for one service/audience could potentially be replayed against a different service that shares the same signing key.
- **Never store sensitive data in the payload** — it's base64-encoded, not encrypted, and trivially readable by anyone who intercepts the token or inspects it client-side (e.g., via browser dev tools).
- **Keep tokens small.** Every claim you add is sent on every single request; large JWTs add real bandwidth and header-size overhead at scale.

## Common Mistakes

- **Accepting `alg: none`.** Some JWT libraries historically allowed an "unsecured" JWT with no signature at all if the header specified `alg: none` — a verifier that doesn't explicitly reject this will treat a completely unsigned, attacker-crafted token as valid. Modern libraries default-reject this, but always confirm your verification call pins the algorithm explicitly rather than trusting the library's defaults blindly.
- **Algorithm confusion (RS256 → HS256 downgrade).** If a verifier is configured to "accept whatever `alg` the token says" and also has access to the RS256 public key, an attacker can craft a token with `alg: HS256` and sign it using the public key as an HMAC secret (public keys are, after all, public) — the verifier, using the public key as an HMAC key, sees a valid signature. Pinning the expected algorithm server-side prevents this entirely.
- **Trusting an expired-but-unchecked token** because the application code decodes the JWT without actually validating `exp` (some low-level "decode" functions, as opposed to "verify" functions, skip validation by design).
- **Storing JWTs in `localStorage` in browser apps**, exposing them to any XSS payload — prefer an `HttpOnly` cookie for browser-based clients when feasible.
- **Treating a valid signature as authorization.** A syntactically and cryptographically valid JWT only proves *who issued and signed it and that it wasn't tampered with* — your application still must apply [authorization](authentication-vs-authorization.md) logic on top of the claims.

## Best Practices

- Pin the verification algorithm explicitly; never trust the token's own `alg` header to select it.
- Use asymmetric signing (RS256/ES256) whenever more than one service verifies tokens.
- Set short expiries on access tokens and rely on a revocable refresh token for longer-lived sessions.
- Always validate `exp`, `iss`, and `aud`, not just the signature.
- Keep payloads minimal and non-sensitive — treat them as public, readable data.

## AI Engineering Perspective

JWTs show up constantly in AI system backends: they're a natural way to pass a verified user identity and entitlements (which model tiers a user can access, their remaining quota) from your API gateway down into internal services, including an [LLM gateway](../15-production-ai-systems/README.md) that needs to know "which customer is this, and what's their rate limit?" without a database round-trip on every token-streamed request. The stateless-verification property is especially valuable in high-throughput, latency-sensitive AI inference paths, where an extra database lookup per request adds up. The revocation trade-off matters too: if a JWT embeds a user's AI usage tier or permissions and that changes mid-session (a downgrade, a ban), a long-lived token will keep granting the old permissions until it expires — reinforcing why short access-token lifetimes matter even more in systems processing costly LLM calls, where continued unauthorized access has a real dollar cost per request.

## Exercises

**Beginner**
1. Decode the example JWT payload shown in this chapter by hand (base64url-decoding just the middle segment) and confirm it matches the shown decoded JSON.
2. Explain why a JWT is described as "signed, not encrypted," and what that means for what you should and shouldn't put in the payload.

**Intermediate**
3. Modify the `verify_access_token` dependency above to also reject tokens missing a `role` claim entirely, with a distinct error message from "invalid signature."

**Advanced**
4. Explain, step by step, how an algorithm-confusion attack (RS256 → HS256) would work against a verifier that trusts the token's `alg` header, and write the specific check that prevents it.

## Key Takeaways

- A JWT is `header.payload.signature` — signed for integrity, not encrypted for confidentiality; treat the payload as readable by anyone who has the token.
- Always pin the verification algorithm server-side; never let the token's own `alg` header dictate how it's verified — this is the root cause of the most severe real-world JWT vulnerabilities.
- HS256 shares one secret across signer and verifier; RS256 separates a private signing key from a public verification key, which is safer for multi-service systems.
- JWTs can't be revoked before their `exp` without extra machinery (denylists, key rotation) — keep access-token lifetimes short and pair with a revocable refresh token.
- A valid signature proves authenticity, not permission — authorization logic must still be applied on top of the claims.
