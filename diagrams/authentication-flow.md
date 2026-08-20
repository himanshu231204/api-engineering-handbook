# Authentication Flow

Two of the most common authentication flows in production APIs: a first-party username/password login that issues JWTs, and a third-party OAuth 2.0 login with PKCE.

## Username/Password Login (Access + Refresh Tokens)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Auth API
    participant DB as Database

    C->>API: POST /login (username, password)
    API->>DB: Look up user by username
    DB-->>API: User record (password hash)
    API->>API: Verify password hash
    API->>API: Issue access token (short-lived JWT)
    API->>API: Issue refresh token (long-lived JWT)
    API-->>C: 200 OK { access_token, refresh_token }
    C->>API: Request with Authorization: Bearer access_token
    API->>API: Verify JWT signature + expiry
    API-->>C: 200 OK (protected resource)
```

The server never stores the plaintext password — it stores a salted hash and re-hashes the submitted password to compare. On success, it issues two tokens instead of one: a short-lived **access token** (minutes) used on every request, and a long-lived **refresh token** (days/weeks) used only to obtain a new access token once the old one expires. This split limits the damage of a leaked access token while avoiding forcing the user to re-enter their password constantly. See [Access vs Refresh Tokens](../docs/05-authentication-authorization/access-vs-refresh-tokens.md) for the full rationale.

## OAuth 2.0 Authorization Code Flow with PKCE

```mermaid
sequenceDiagram
    participant U as User
    participant App as Client App
    participant Auth as Authorization Server
    participant API as Resource API

    App->>App: Generate code_verifier + code_challenge
    U->>App: Click "Login with Provider"
    App->>Auth: Redirect with code_challenge
    U->>Auth: Authenticate + consent
    Auth-->>App: Redirect back with authorization code
    App->>Auth: POST /token (code + code_verifier)
    Auth->>Auth: Verify code_verifier matches code_challenge
    Auth-->>App: access_token + refresh_token
    App->>API: Request with Bearer access_token
    API-->>App: Protected resource
```

PKCE (Proof Key for Code Exchange) closes a gap in the plain authorization code flow: a client generates a random `code_verifier`, derives a `code_challenge` from it, and sends only the challenge in the initial redirect. When it later exchanges the authorization code for tokens, it must present the original verifier — so even if the authorization code is intercepted in transit, an attacker without the verifier cannot redeem it. This makes PKCE mandatory for public clients (mobile apps, SPAs) that can't safely hold a client secret. See [OAuth 2.0](../docs/05-authentication-authorization/oauth2.md) for the full protocol walkthrough.

## See Also

- [JWT Deeply Explained](../docs/05-authentication-authorization/jwt-deeply-explained.md)
- [OAuth 2.0](../docs/05-authentication-authorization/oauth2.md)
- [Access vs Refresh Tokens](../docs/05-authentication-authorization/access-vs-refresh-tokens.md)
