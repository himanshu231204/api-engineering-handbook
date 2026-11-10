# ABAC

> [!TIP]
> **In one line:** Attribute-based access control decides each request by evaluating policy rules over attributes of the subject, resource, action and environment, instead of looking up a fixed role.
>
> **In plain English:** A bouncer with a clipboard of rules, not a list of names. "Over 21, ticket for tonight, and the venue isn't full" is a rule that works for thousands of strangers without anyone pre-registering them. ABAC lets your API express rules like that.
>
> **You'll be able to:** recognise when RBAC stops scaling and attributes are the better fit · structure a policy decision point and enforcement point with deny-by-default · write and test a small in-process policy engine with an audit trail

## Why This Matters

[RBAC](rbac.md) answers "what kind of user is this, and what can that kind of user do?" It is simple and auditable, and it should be your starting point. But real products accumulate rules that roles cannot express without exploding:

- "A doctor can read a patient's record **only if** that patient is assigned to the doctor's ward."
- "An analyst can export reports **only** for their own region, **only** from the corporate network, and **never** if the report is marked `restricted` unless they hold clearance level 3."
- "A contractor may edit documents **during their contract dates**."
- "Managers can approve expenses **under their approval limit** for people in **their reporting line**."

In RBAC you would model each of these by minting roles: `doctor_ward_7`, `analyst_emea_corporate_network`, `contractor_until_march`. The role count multiplies with every dimension (a problem usually called *role explosion*), and roles turn into per-user permission sets again, which defeats their purpose. The data you need to decide (ward, region, clearance, contract date, amount) already exists as attributes on the user, the resource and the request. ABAC says: stop encoding combinations into role names, and evaluate the attributes directly.

ABAC is also where the "ownership check" that [RBAC](rbac.md) told you to bolt on fits naturally. "The order's `customer_id` equals the caller's `user_id`" is an attribute comparison, and so is "the document's `tenant_id` equals the caller's tenant" (see [Multi-Tenant Authorization](multi-tenant-authorization.md)). Preventing Broken Object Level Authorization is mostly a matter of making this comparison automatic and impossible to forget.

## Core Concept

An ABAC decision takes four groups of attributes and returns a decision:

- **Subject attributes**: who is asking. `user_id`, `department`, `clearance`, `roles`, `tenant_id`, `region`, `employment_type`.
- **Resource attributes**: what is being touched. `owner_id`, `classification`, `status`, `amount`, `tenant_id`, `region`.
- **Action attributes**: what is being attempted. `read`, `update`, `approve`, `export`.
- **Environment (context) attributes**: the circumstances. Time of day, source IP or network zone, device posture, whether MFA was used in this session, request rate.

A **policy** is a rule over those attributes with an **effect** (`permit` or `deny`). The system also needs a way to combine several matching rules and a default when none match.

The standard architecture (from XACML and NIST SP 800-162) names four roles. Knowing them is useful vocabulary even when you build everything in one process:

- **PEP, Policy Enforcement Point**: the code in your API that intercepts the request, asks for a decision, and enforces it (returns 403, filters the query, hides the field).
- **PDP, Policy Decision Point**: the engine that evaluates policies against the attributes and returns permit or deny.
- **PIP, Policy Information Point**: where the PDP gets attributes it was not handed (a database lookup for the resource owner, an HR system for the manager chain).
- **PAP, Policy Administration Point**: where policies are authored, reviewed, versioned and deployed.

Two design choices matter more than any syntax. First, **default deny**: if no rule permits the request, it is denied. Second, a **combining algorithm**: when one rule permits and another denies, which wins? *Deny-overrides* is the safest default, because adding a deny rule can only restrict access.

## Mental Model

Picture a **customs checkpoint with a rulebook** instead of a guest list. The officer (PEP) does not memorise who may pass. They read what is on the traveller (subject attributes), what is in the bag (resource attributes), what the traveller wants to do (action), and the situation (environment: is there an alert today?). They look it up in the rulebook (PDP), phoning another office when they need a fact they don't have (PIP). The rulebook is maintained by a separate team under change control (PAP). Crucially, the sign over the door says **"anything not explicitly allowed is not allowed."** When rules conflict ("residents may pass" versus "nobody with a flagged bag may pass"), the stricter rule wins.

## How It Works

1. **Collect attributes.** Subject attributes come from the verified token (see [JWT Deeply Explained](jwt-deeply-explained.md)) and, when needed, a directory lookup. Resource attributes come from loading the record. Environment attributes come from the request itself (IP, time) or the session (auth strength). **Never accept attributes about the subject from request parameters**: a caller-supplied `clearance=3` is not an attribute, it is a wish.
2. **Build the decision request.** Package `subject`, `resource`, `action`, `environment`.
3. **Evaluate.** The PDP finds the policies whose *target* (action and resource type) matches, evaluates each *condition*, and collects the effects.
4. **Combine.** Apply deny-overrides: any deny wins; otherwise any permit wins; otherwise default deny. A rule that fails to evaluate (missing attribute, type error) must fail closed: a permit rule counts as *not matching*, and a deny rule counts as *matching*, so the request is denied either way.
5. **Enforce.** The PEP acts on the decision: return 403 (or 404 to avoid leaking existence), or run the action.
6. **Record.** Log the decision with the attributes used, the matched policy ids and the policy version. This is what makes ABAC auditable. Without it, "why was this allowed?" is unanswerable, which is its biggest operational weakness.

### Where attributes can mislead you

- **Stale attributes.** A role claim in a one-hour token is an hour old. For high-risk rules, load fresh attributes from the source of truth.
- **Missing attributes.** If `resource.region` is null, `subject.region == resource.region` is false, which is fine for permit rules but can accidentally allow when written negatively (`!=` in a deny rule is false when either side is missing). Design so that absence leads to denial.
- **Attribute provenance.** Each attribute has an owner who is authoritative for it. HR owns `department`, the owning service owns `owner_id`. If a client can influence an attribute, the rule is only as trustworthy as the client.

### Combining with RBAC

ABAC and RBAC are not rivals. A practical hybrid: use roles as one *subject attribute* ("has role `support_agent`") for coarse access, and add attribute conditions for the fine-grained parts. Many systems evolve this way: start with roles, then add conditions only where roles fail. The cost of ABAC is the loss of simple answers: "who can read this?" is easy in RBAC (list the roles) and genuinely hard in ABAC (it depends on evaluating rules over every user's attributes).

## Architecture

```mermaid
flowchart LR
    C["Client"] -->|"1. request + token"| PEP["API handler\n(PEP)"]
    PEP -->|"2. subject, resource,\naction, environment"| PDP["Policy engine\n(PDP)"]
    PDP -->|"3. fetch missing\nattributes"| PIP[("Attribute sources\n(PIP)")]
    PAP["Policy repo\n(PAP)"] -->|"versioned policies"| PDP
    PDP -->|"4. permit / deny\n+ matched rules"| PEP
    PEP -->|"5. enforce"| R["Resource / DB"]
    PDP -.->|"decision log"| AUD["Audit log"]
```

## Request / Response Example

A project manager tries to approve an expense. Policy: approvers may approve amounts up to their limit, only for their own department, only from a session that used MFA.

```http
POST /expenses/771/approve HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json

{"comment": "Conference travel"}
```

The PDP sees (derived server-side, not from the body): subject `{id: u_42, department: "eng", approval_limit: 500, mfa: true}`, resource `{type: "expense", department: "eng", amount: 1800}`, action `approve`. The amount exceeds the limit, so no permit rule matches and the default applies:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": "access_denied",
  "reason": "no_matching_permit",
  "request_id": "req_8f2c61"
}
```

Note what the response does *not* say: it does not echo the limit, the amount comparison or the rule text. Detailed reasons go to the audit log, not to the caller, or you hand an attacker a map of your policy. The audit record for this decision (internal) is richer:

```json
{
  "ts": "2026-11-10T09:14:03Z", "decision": "deny", "default_deny": true,
  "subject": "u_42", "action": "expense:approve", "resource": "expense/771",
  "matched_permit": [], "matched_deny": [], "policy_version": "2026-11-05.3"
}
```

## Code Example

A small, in-process PDP: policies are plain Python predicates over a decision request, combined with deny-overrides and default-deny, with a decision log. This is deliberately tiny. For production, prefer a purpose-built engine (Open Policy Agent with Rego, Cedar, Casbin, or a hosted authorization service) when policies must be authored, reviewed and tested outside application code.

```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal

from fastapi import Depends, FastAPI, HTTPException

log = logging.getLogger("authz.decisions")


@dataclass(frozen=True)
class DecisionRequest:
    subject: dict       # built server-side from the verified token + directory
    resource: dict      # loaded from the database, never from the request body
    action: str
    environment: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    id: str
    effect: Literal["permit", "deny"]
    actions: frozenset[str]
    condition: Callable[[DecisionRequest], bool]


def _safe(policy: Policy, req: DecisionRequest) -> bool:
    """A condition that raises (missing key, bad type) cannot be evaluated, so fail closed:
    a permit rule counts as NOT matching, and a deny rule counts as MATCHING.
    Either way the request ends up denied, whatever attribute was missing."""
    try:
        return bool(policy.condition(req))
    except (KeyError, TypeError, AttributeError):
        return policy.effect == "deny"


class PolicyEngine:
    def __init__(self, policies: list[Policy], version: str):
        self.policies, self.version = policies, version

    def decide(self, req: DecisionRequest) -> bool:
        applicable = [p for p in self.policies if req.action in p.actions]
        matched = [p for p in applicable if _safe(p, req)]
        denies = [p.id for p in matched if p.effect == "deny"]
        permits = [p.id for p in matched if p.effect == "permit"]
        # Deny-overrides, then permit, then default deny.
        allowed = not denies and bool(permits)
        log.info(
            "decision=%s action=%s subject=%s resource=%s permits=%s denies=%s version=%s",
            "permit" if allowed else "deny", req.action,
            req.subject.get("id"), req.resource.get("id"), permits, denies, self.version,
        )
        return allowed


def business_hours(req: DecisionRequest) -> bool:
    now: datetime = req.environment["now"]          # timezone-aware UTC
    return 7 <= now.hour < 19 and now.weekday() < 5


POLICIES = [
    Policy("owner-can-read-own-order", "permit", frozenset({"order:read"}),
           lambda r: r.subject["id"] == r.resource["customer_id"]
                     and r.subject["tenant_id"] == r.resource["tenant_id"]),
    Policy("support-can-read-in-tenant", "permit", frozenset({"order:read"}),
           lambda r: "support_agent" in r.subject["roles"]
                     and r.subject["tenant_id"] == r.resource["tenant_id"]),
    Policy("approver-within-limit", "permit", frozenset({"expense:approve"}),
           lambda r: r.subject["department"] == r.resource["department"]
                     and r.resource["amount"] <= r.subject["approval_limit"]
                     and r.environment.get("mfa") is True
                     and business_hours(r)),
    # Deny rule: nobody approves their own expense, whatever else permits it.
    # Fail closed: if the approver or the submitter is unknown (missing or null) we cannot
    # show they are two different people, so this rule matches and approval is denied.
    Policy("no-self-approval", "deny", frozenset({"expense:approve"}),
           lambda r: r.subject.get("id") is None
                     or r.resource.get("submitter_id") in (None, r.subject["id"])),
]
engine = PolicyEngine(POLICIES, version="2026-11-05.3")

app = FastAPI()


def current_subject() -> dict:
    # Placeholder: in production, build this from the VERIFIED token claims plus
    # a directory lookup (see jwt-deeply-explained.md), never from headers.
    return {"id": "u_42", "tenant_id": "acme", "roles": ["support_agent"],
            "department": "eng", "approval_limit": 500}

EXPENSES = {771: {"id": 771, "tenant_id": "acme", "department": "eng",
                  "amount": 1800, "submitter_id": "u_7"}}


@app.post("/expenses/{expense_id}/approve")
async def approve(expense_id: int, subject: dict = Depends(current_subject)):
    expense = EXPENSES.get(expense_id)      # PIP: load the real resource attributes
    # Same response for "missing" and "other tenant" so existence isn't leaked.
    if expense is None or expense["tenant_id"] != subject["tenant_id"]:
        raise HTTPException(404, "Not found")
    req = DecisionRequest(
        subject=subject, resource=expense, action="expense:approve",
        environment={"now": datetime.now(timezone.utc), "mfa": True},  # mfa from session
    )
    if not engine.decide(req):
        raise HTTPException(403, "access_denied")
    return {"status": "approved", "expense_id": expense_id}
```

Test the deny rules directly, since the engine is a pure function (pytest style; run it next to the module above):

```python
from datetime import datetime, timezone

NOW = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)  # a Tuesday, inside business hours
APPROVER = {"id": "u_42", "tenant_id": "acme", "roles": [], "department": "eng", "approval_limit": 5000}
EXPENSE = {"id": 1, "tenant_id": "acme", "department": "eng", "amount": 100, "submitter_id": "u_7"}


def can_approve(subject: dict, resource: dict) -> bool:
    req = DecisionRequest(subject, resource, "expense:approve", {"now": NOW, "mfa": True})
    return engine.decide(req)


def test_normal_approval_is_permitted():
    assert can_approve(APPROVER, EXPENSE) is True


def test_self_approval_is_denied():
    assert can_approve(APPROVER, {**EXPENSE, "submitter_id": "u_42"}) is False


def test_unknown_submitter_is_denied():
    no_submitter = {k: v for k, v in EXPENSE.items() if k != "submitter_id"}
    assert can_approve(APPROVER, no_submitter) is False
    assert can_approve(APPROVER, {**EXPENSE, "submitter_id": None}) is False


def test_missing_or_null_approver_id_is_denied():
    assert can_approve({k: v for k, v in APPROVER.items() if k != "id"}, EXPENSE) is False
    assert can_approve({**APPROVER, "id": None}, EXPENSE) is False
```

Behaviours to notice: the engine is a pure function of its inputs (easy to unit test), it logs the policy version with every decision, and the enforcement point runs the resource load first so it can decide on *real* attributes. This example evaluates every applicable policy; at large scale you would index policies by action and resource type.

## Production Considerations

- **Test policies like code.** Keep a table of `(subject, resource, action, environment) -> expected` cases, including every deny and every boundary (amount equal to the limit, the minute business hours begin). A policy change without a regression suite is an outage or a breach waiting to happen.
- **Version and review policies.** Store policy in version control, deploy with a version id, record it in every decision log. Support dry-run ("shadow") evaluation of a new policy set against live traffic to see what *would* change before it takes effect.
- **List endpoints need filtering, not just checking.** Evaluating a policy per record after fetching 10 000 rows is slow and wrong for pagination. Translate the policy into a query filter (`WHERE tenant_id = :t AND department = :d`) or use partial evaluation, then verify per-record only where a rule cannot be expressed in SQL.
- **Latency budget.** An in-process PDP adds microseconds; a remote PDP adds a network hop and a new failure mode. Decide explicitly what happens when the PDP is unreachable: for most APIs, deny (fail closed), with caching of recent permits where staleness is acceptable.
- **Attribute freshness.** Cache attributes with a TTL matched to the risk of staleness. Revoking a user's clearance should not wait out a day-long cache.
- **Auditability is the cost of flexibility.** Log inputs, matched rule ids and version. Be ready to answer "who could read record X on date D?" by replaying the decision with historical attributes, and know that this is hard unless you saved them.
- **Complexity budget.** Every policy is code that can be wrong. If a rule fits a role cleanly, keep it a role.

## Common Mistakes

- **Taking subject attributes from the client** (a header, a body field, an unsigned claim). Attributes the caller can set are not authorisation inputs.
- **Default allow** ("no rule matched, so continue"). The absence of a rule is not permission.
- **Permit-overrides combining** without thought, which lets one over-broad permit defeat a carefully written deny.
- **Rules that fail open** on missing attributes, for example `if resource["classification"] != "secret": permit` when `classification` is absent.
- **Checking after the side effect**, or checking only on the "get one" endpoint and forgetting list, export, bulk and search endpoints that return the same data.
- **Leaking policy details** in error messages, or revealing resource existence to unauthorised callers.
- **No decision log**, so incidents and compliance questions can't be answered.
- **Using ABAC for everything**, including cases a three-role RBAC handles, making the system harder to reason about for no gain.

## Best Practices

- Start from RBAC; introduce attribute conditions where roles would explode or where ownership, tenant, region or time matter.
- Make the decision a pure, unit-testable function of explicit inputs, and centralise it in one module that every handler calls.
- Deny by default, deny-overrides, and fail closed on evaluation errors: an erroring permit rule does not match and an erroring deny rule does.
- Derive attributes server-side from verified credentials and authoritative sources, and know who owns each attribute.
- Log every decision with policy version and matched rule ids, and keep denies searchable.
- Pair with [multi-tenant scoping](multi-tenant-authorization.md) so tenant id is an enforced invariant, not one optional condition.
- Review policies regularly and remove rules nobody can explain.

## AI Engineering Perspective

ABAC suits AI systems because the interesting rules are attribute rules: "this agent may call `tickets:read` only on tickets in the tenant of the user it is acting for," "this retrieval may return only chunks whose `acl` includes the requesting user's groups," "block tool calls to `payments:refund` when `amount > 100` unless a human approved." These are attributes of the *delegating user*, the *agent*, the *resource* and the *context*, evaluated at the tool-call boundary rather than trusted to the model. See [RAG APIs](../16-rag-apis/README.md) for filtering retrieval by document ACL metadata before the prompt is built (post-filtering after generation is too late), and [AI agents and MCP](../17-ai-agents-and-mcp/README.md) for enforcing per-tool policy.

Treat model output as untrusted input: an LLM can be induced to request any action, so the policy decision must depend on attributes the model cannot write (the authenticated user, the tool's declared scope, the resource's real owner), never on arguments the model supplies about itself. The decision log doubles as the audit trail for agent behaviour.

## Exercises

**Beginner**
1. List the subject, resource, action and environment attributes needed to express "a nurse can read a patient chart only for patients on her ward, during her shift."
2. Explain why default-deny matters. Give an example of how a default-allow engine could grant access by accident.

**Intermediate**
3. Add a policy to the code example that denies `order:read` when `resource["classification"] == "restricted"` unless `subject["clearance"] >= 3`. Write four test cases, including one where `classification` is missing.
4. Add a `permit-overrides` mode to `PolicyEngine`, and demonstrate a scenario where it grants access that deny-overrides would block.

**Advanced**
5. Design how `GET /expenses` (a paginated list) applies the "same tenant and department" policy without loading all rows and filtering in Python. What can't be pushed into SQL, and what do you do about it?
6. Propose a shadow-evaluation rollout for a new policy set: what do you log, how do you compare decisions, and what threshold of differences blocks the rollout?

## Key Takeaways

- ABAC decides from attributes of the subject, resource, action and environment, which avoids role explosion and expresses ownership and context rules directly.
- Separate enforcement (PEP) from decision (PDP), use deny-overrides with default-deny, and fail closed.
- Attributes must come from verified or authoritative sources, never from caller-controlled input.
- Flexibility costs explainability: log every decision with policy version and matched rules, and test policies as code.

### Check Yourself

<details markdown="1">
<summary>1. What are the four attribute categories an ABAC decision uses?</summary>

Subject (who), resource (what is touched), action (what is attempted) and environment (context such as time, network, MFA status). A policy is a rule over these, with an effect of permit or deny.

</details>

<details markdown="1">
<summary>2. Why prefer deny-overrides with a default of deny?</summary>

It makes the system fail safe: a new deny rule can only reduce access, and a request nobody wrote a permit for is blocked. With permit-overrides or default-allow, a gap or an over-broad rule silently grants access.

</details>

<details markdown="1">
<summary>3. Your policy says analysts may export only their own region's reports, and the API reads the region from a `?region=` query parameter. What is wrong and how do you fix it?</summary>

The subject's region is being supplied by the caller, so any analyst can claim any region. Derive the subject's region from the verified token or a directory lookup, and compare it with the resource's stored region, loaded from the database.

</details>

---
Back to the [Part 5 README](README.md).
