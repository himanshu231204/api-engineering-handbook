# Secrets Management

## Why This Matters

Every API talks to something it needs a secret to trust: a database password, a JWT signing key (see [JWT Deeply Explained](../05-authentication-authorization/jwt-deeply-explained.md)), a third-party API key, a webhook signing secret (see `webhook-security.md`, planned), or credentials for cloud infrastructure. If any one of those secrets leaks — committed to a public repo, printed in a log, baked into a Docker image, pasted into a Slack channel — an attacker doesn't need to find a clever vulnerability at all. They just log in as you. Secrets management is the discipline of making sure that never happens: secrets are never stored where source code lives, are only accessible to the systems that legitimately need them, are rotated on a schedule and immediately after any suspected exposure, and are revocable within minutes rather than days. It is one of the least glamorous parts of API engineering and one of the most consequential — a huge share of real-world breaches trace back to a leaked credential, not a zero-day exploit.

## Core Concept

A **secret** is any value that grants access or trust and would cause harm if disclosed: passwords, API keys, private keys, signing secrets, encryption keys, and connection strings that embed credentials. Secrets management covers the full lifecycle of these values:

- **Storage** — where the secret physically lives at rest (never in source code or version control).
- **Distribution** — how a running process gets the secret value at startup or runtime, without a human copy-pasting it insecurely.
- **Access control** — which services, environments, and people are allowed to read which secrets.
- **Rotation** — replacing a secret's value periodically, and immediately after any suspected leak, without causing downtime.
- **Auditing** — knowing who or what accessed a secret and when.

The core principle underlying all of this is: **secrets must be separate from code, and code should only ever reference secrets by name, never by value.** Your application reads `DATABASE_PASSWORD` from its environment; it never has the literal password typed into a `.py` file.

## Mental Model

Think of secrets like the keys to a building. You would never staple a copy of the master key to the blueprints (the source code) that get photocopied and handed to every contractor, intern, and eventually posted publicly when the building's plans go up on a public archive (a public GitHub repo). Instead, keys are held in a locked key cabinet (a secret manager) that logs every checkout, issues different keys to different roles (least privilege), and can have a specific key deactivated and reissued the moment it's lost — without having to change the locks on every door in the building (redeploying every service). Environment variables are like handing someone a physical key for their shift: convenient and simple, but the key itself still exists in a form that can be dropped, photographed, or forgotten in a pocket if you're not careful about where that environment is defined and who can read it.

## How It Works

**1. Never hardcode secrets in source.** A hardcoded secret ends up in version control history forever — even if you delete it in a later commit, `git log` and forks retain it indefinitely. It also gets copied into every clone, every CI log that echoes the file, and every backup of the repository.

**2. Use environment variables as the baseline distribution mechanism.** Twelve-factor app practice is to inject configuration, including secrets, via environment variables set by the deployment platform (container orchestrator, PaaS, CI/CD system) rather than files checked into the repo. The application reads `os.environ["DATABASE_URL"]` at startup. This decouples the *code* (which is the same across environments) from the *secret value* (which differs between dev, staging, and production).

**3. For anything beyond a single small service, use a dedicated secret manager.** Environment variables are a good baseline but have real limits: they're often visible to anything that can inspect a running process, they don't rotate themselves, and there's no audit trail of who read what. Tools like **HashiCorp Vault**, **AWS Secrets Manager**, **Google Secret Manager**, and **Azure Key Vault** solve this by centralizing secrets behind an API that requires authenticated, audited access, and that can automatically rotate credentials (e.g., rotating a database password and updating the database in the same operation). Conceptually, they all do the same three things: store secrets encrypted at rest, authenticate and authorize who/what can fetch a given secret, and log every access.

**4. Inject secrets at deploy/runtime, not build time.** A secret baked into a Docker image at build time ends up in every layer of that image, is extractable by anyone who can pull it, and can't be rotated without rebuilding. Instead, secrets should be injected when the container starts (as environment variables from an orchestrator's secret store, or fetched live from a secret manager on process startup).

**5. Rotate on a schedule, and immediately on suspected leak.** Rotation means generating a new secret value and retiring the old one. Routine rotation limits the blast radius of a leak nobody has noticed yet; emergency rotation is the direct response to a confirmed or suspected leak.

## Architecture

```mermaid
flowchart TB
    subgraph Bad["Anti-Pattern: Secret in Code"]
        Code1["app.py\nDATABASE_PASSWORD = 'hunter2'"] --> Repo1["Git repository"]
        Repo1 --> Public["Public fork / leaked backup\n= permanent exposure"]
    end

    subgraph Good["Recommended: Secret Manager"]
        SM["Secret Manager\n(Vault / AWS Secrets Manager)"]
        App["API Process"]
        Deploy["Deployment Pipeline"]
        Rotate["Rotation Job"]

        Deploy -->|"grants scoped IAM role\nat deploy time"| App
        App -->|"authenticated fetch\nat startup / runtime"| SM
        SM -->|"encrypted secret value\n+ audit log entry"| App
        Rotate -->|"periodically generates\nnew secret value"| SM
        SM -->|"old value revoked"| App
    end
```

## Request / Response Example

Fetching a secret from a manager is itself an authenticated API call. A simplified example against an AWS Secrets Manager–style HTTP API:

```http
POST / HTTP/1.1
Host: secretsmanager.us-east-1.amazonaws.com
Authorization: AWS4-HMAC-SHA256 Credential=AKIA.../20260818/us-east-1/secretsmanager/aws4_request, ...
X-Amz-Target: secretsmanager.GetSecretValue
Content-Type: application/x-amz-json-1.1

{
  "SecretId": "prod/api/database-credentials"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/x-amz-json-1.1

{
  "Name": "prod/api/database-credentials",
  "VersionId": "a1b2c3d4-...",
  "SecretString": "{\"username\":\"api_service\",\"password\":\"[REDACTED]\"}",
  "CreatedDate": 1755500000
}
```

Note that the *request* to fetch a secret is itself authenticated with its own credential (here, an AWS request signature) — access to secrets is gated behind identity, and every call like this is logged for audit.

## Code Example

```python
# settings.py
# Load configuration -- including secrets -- from environment variables using
# pydantic-settings. The application code never contains a literal secret
# value; it only references the *name* of a setting.

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # SecretStr prevents the value from being accidentally printed in logs,
    # tracebacks, or repr() output -- it renders as "**********" instead.
    database_url: SecretStr = Field(..., alias="DATABASE_URL")
    jwt_signing_key: SecretStr = Field(..., alias="JWT_SIGNING_KEY")
    stripe_api_key: SecretStr = Field(..., alias="STRIPE_API_KEY")


settings = Settings()  # raises a validation error at startup if any required secret is missing

# --- NEVER DO THIS ---
# DATABASE_URL = "postgresql://api_service:hunter2@prod-db.internal:5432/app"
# A hardcoded secret like this is permanently in git history the moment it's
# committed, visible to anyone with repo access, and impossible to rotate
# without a code change and redeploy.


def get_database_connection_string() -> str:
    # .get_secret_value() is an explicit, deliberate unwrap -- it can't
    # happen accidentally via logging or an f-string typo.
    return settings.database_url.get_secret_value()


# Conceptual example of fetching from a secret manager instead of a plain
# env var, for services that need rotation and audit logging:
def fetch_secret_from_vault(secret_path: str) -> str:
    """
    In production this would use the Vault or AWS Secrets Manager SDK,
    authenticated via a scoped IAM role or Vault token -- never a hardcoded
    credential to the secret manager itself. The service's identity (e.g.,
    its cloud IAM role) is what's trusted, not a stored password.
    """
    import boto3  # conceptual: AWS Secrets Manager client

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_path)
    return response["SecretString"]
```

## Production Considerations

- **Least privilege access.** Each service should be able to read only the secrets it needs, not every secret in the organization. A compromised low-privilege service should not be able to exfiltrate the database password for an unrelated service.
- **Separate secrets per environment.** Dev, staging, and production must never share the same database password, signing key, or API key. A leak in a less-guarded dev environment should never compromise production.
- **Encrypt secrets at rest and in transit.** Secret managers do this by default; if you roll your own storage, this is not optional.
- **Audit logs are non-negotiable.** When a secret leak is suspected, you need to know exactly which services and people accessed it and when, to scope the incident.
- **Automate rotation where possible.** Manual rotation is skipped under deadline pressure. Database credential rotation, in particular, can often be fully automated by the secret manager coordinating with the database.
- **Short-lived credentials beat long-lived ones.** Where the underlying system supports it (e.g., cloud IAM roles, database tokens with a TTL), prefer credentials that expire in minutes or hours over static, permanent secrets — a leaked short-lived credential has a naturally bounded blast radius.

## Common Mistakes

- **Committing a `.env` file with real values to version control** because it wasn't added to `.gitignore`, or because someone force-added it "just this once."
- **Logging entire request/response payloads or config objects** that happen to include a secret field, leaking it into log aggregation systems that many engineers can read.
- **Reusing the same secret across dev, staging, and production**, so a leak in the least-protected environment compromises all of them.
- **Baking secrets into a Docker image** via a build argument or `COPY` of a config file, making them extractable from any pulled image layer.
- **Treating rotation as a one-time setup task** instead of an ongoing scheduled process, so credentials go years without changing.
- **Pasting a secret into a chat tool, ticket, or email "temporarily"** to unblock a teammate — these are rarely deleted and are usually indexed/searchable indefinitely.

## Best Practices

- Never write a secret value directly in source code; reference secrets only by name/environment variable.
- Use `.env` files for local development only, and always `.gitignore` them; use environment variables or a secret manager for every deployed environment.
- Use a dedicated secret manager (Vault, AWS/GCP/Azure equivalents) once you have more than a couple of services or need audit trails and automated rotation.
- Scope access to secrets per service/role using least privilege, and prefer short-lived, auto-expiring credentials over static ones.
- Have a documented, rehearsed **leak response plan**: revoke/rotate the specific secret immediately, audit access logs to scope the exposure, check for any unauthorized use during the exposure window, and only then investigate root cause — speed of revocation matters more than root-causing first.

## AI Engineering Perspective

AI systems introduce their own secret sprawl: provider API keys (OpenAI, Anthropic, etc.), vector database credentials, and — often overlooked — the secrets embedded inside tool-calling configurations for agents (see [Part 17 — AI Agents & MCP](../17-ai-agents-and-mcp/README.md)), where an agent might be configured with credentials for a downstream service it calls on the user's behalf. A distinctive risk in AI systems is a secret leaking *through the model itself*: if API keys or credentials ever end up in a prompt, in retrieved document content, or in logs that get fed back into a fine-tuning or evaluation pipeline, they can be echoed back in a completion or become discoverable through prompt injection against an agent with file or shell access. When building an LLM gateway (see [Part 15 — Production AI Systems](../15-production-ai-systems/README.md)) that manages multiple provider keys, treat each provider key exactly like a database credential: store it in a secret manager, scope it to the minimum required service, and rotate it on the same schedule as any other production credential — not as a special exception because "it's just an API key for a chat model."

## Exercises

**Beginner**
1. Find a public GitHub repository search technique (conceptually — do not actually search for real leaked secrets) that security teams use to detect accidentally committed `.env` files or API keys, and explain why `git rm` alone does not fix a secret that was already committed.

**Intermediate**
2. Using the `Settings` class in the Code Example, add a new required secret `WEBHOOK_SIGNING_SECRET` and explain what happens at application startup if the corresponding environment variable is missing.

**Advanced**
3. Design a rotation strategy for a database password used by three horizontally scaled API instances, such that rotation causes zero downtime (i.e., no instance is ever left holding a fully revoked credential mid-request). Describe the sequence of steps a secret manager and database would need to coordinate.

## Key Takeaways

- Secrets must live outside source code entirely — code references secrets by name, never by literal value, and `.env` files never belong in version control.
- Environment variables are a reasonable baseline; dedicated secret managers (Vault, AWS/GCP/Azure Secrets Manager) add centralized access control, automated rotation, and audit logging as systems grow.
- Rotate secrets on a schedule and immediately upon any suspected leak; prefer short-lived credentials over static ones wherever the underlying system supports it.
- When a leak happens, revoke/rotate first and investigate root cause second — speed limits the blast radius.
- AI systems add new leak surfaces (prompts, retrieved content, agent tool configs) that deserve the same discipline as any database credential.

See also: [CORS](cors.md), [SQL Injection](sql-injection.md), [Input Validation](input-validation.md), [OWASP API Security Top 10](owasp-api-security.md), and the [glossary](../../resources/glossary.md).

[← Back to Part 10 — API Security](README.md)
