# Opt-in Account Continuity

## Decision

The ecosystem may share a durable identity across products, but **shared identity does not imply shared product data**.

Cross-product continuity follows this invariant:

**shared identity → explicit consent grant → scoped context exchange → provenance → revocation**

Products remain separate tenants and separate data owners unless a user deliberately authorizes a bounded transfer.

## Hard rules

1. **Same login is not permission to share data.** Authentication continuity only establishes that the same ecosystem user is present.
2. **Every meaningful cross-product transfer requires an explicit user grant.** A grant names the source product, destination product, purpose, and scopes.
3. **No product may directly read another product's database for continuity.** Exchange happens through signed snapshots or scoped API references governed by `contracts/continuity-grant.schema.json`.
4. **Every received context object retains provenance.** The receiving product must be able to distinguish user-entered data from context supplied by ALVIRA, ailhat, another product, or an execution environment.
5. **Revocation is first-class.** New access stops when a grant is revoked or expires. Persisted snapshots must honor the grant's declared persistence mode and remain visibly attributable to their original source.
6. **Consent is progressive, not bundled.** Do not ask users to connect the whole ecosystem at signup when the value of a transfer is not yet clear.
7. **Context does not grant execution authority.** Continuity grants may make context available; Agent Control / applicable authorization policy still decides whether an action is permitted, gated, or requires human approval.
8. **Tenant isolation remains authoritative.** A continuity grant is a narrow bridge between two isolated product contexts, not a reason to collapse their storage or authorization boundaries.

## User-visible continuity levels

### 1. Shared ecosystem identity

The user may choose **Use my existing ecosystem account**.

This can carry the minimum identity needed to recognize the same user across products. It does not expose product context, files, portfolio state, observations, or execution history.

### 2. Basic account continuity

A product may offer a small optional set of account-level preferences where useful, such as display identity, locale, or timezone. These are still explicitly scoped and reviewable.

### 3. Product-context continuity

A product may request permission at the moment context transfer creates obvious value.

Example:

> You already described these products in ALVIRA. Bring over your goals and product context so you do not have to enter them again?

The user must be able to review what will be shared before granting access.

## Progressive-consent pattern

Prefer a value-triggered request:

`user reaches setup step → receiving product detects relevant source context exists → explain concrete benefit → review scopes → user grants → scoped transfer`

Avoid a generic ecosystem-wide permission wall during first signup.

## Example: ALVIRA → ailhat

ALVIRA is the durable Context Intelligence source. ailhat may request a grant for a narrow set of ALVIRA-derived context when that reduces portfolio setup work.

Possible scopes:

- `context.goals.read`
- `context.products.read`
- `context.priorities.read`
- `context.working-preferences.read`

Scopes that should not be implied by those grants:

- raw interview transcripts
- uploaded source documents
- unrelated personal context
- execution authority

A transfer should retain source and freshness metadata, for example:

- source product: `alvira-meos`
- context origin: `alvira-context`
- source updated at
- received at
- continuity grant id
- exact scopes used

`contracts/context-envelope.schema.json` remains the least-privilege ALVIRA context transport. For account-continuity use, the envelope must be authorized by an active continuity grant rather than treated as self-authorizing.

## Example: ailhat → Agent Direct / Agent OS

ailhat may offer a separate user grant when verified portfolio context would materially improve a governed handoff.

That grant makes the approved context available to Agent Direct / Agent OS. It does **not** authorize the requested work. The normal authorization and execution policies still apply.

This produces the intended ecosystem chain:

**ALVIRA (Context Intelligence) → user-authorized context → ailhat (Portfolio Intelligence) → user-authorized work/evidence context → Agent Direct / Agent OS → execution evidence → ailhat verification**

## Grant contract

`contracts/continuity-grant.schema.json` is the portable authorization record for continuity. At minimum a grant identifies:

- ecosystem user;
- source product;
- destination product;
- purpose;
- exact scopes;
- exchange mode;
- persistence behavior;
- active/revoked/expired state;
- grant and revocation timestamps;
- mandatory provenance;
- mandatory user review/revocation capability;
- `direct_database_access: false`.

Product-specific adapters may add narrower scopes, but they may not widen a grant implicitly.

## Persistence and revocation

Supported persistence modes:

- `ephemeral` — use for the immediate authorized operation and do not retain a reusable snapshot;
- `snapshot-until-revoked` — retain the authorized snapshot while the grant is active; revocation prevents continued use as active continuity context;
- `durable-with-provenance` — retain a historical/derived record where product behavior requires it, but preserve source attribution and make clear that the source grant is no longer active after revocation.

Revocation never erases audit/evidence records whose retention is independently required for governance, but revoked context must not continue to function as an active authorization channel.

## Product implementation responsibilities

A participating product must:

1. resolve the shared ecosystem identity without assuming data access;
2. show a human-readable scope review before grant creation;
3. enforce source + destination + scope on every exchange;
4. reject expired/revoked grants;
5. retain provenance on imported context;
6. expose connected-product status and a disconnect/revoke action;
7. avoid cross-product database reads;
8. keep its own tenant authorization checks in place after context arrives;
9. distinguish imported context from locally authored context in reasoning/evidence where material;
10. fail closed when grant state cannot be verified.

## Non-goals

This decision does not create:

- a single shared database for ALVIRA, ailhat, ASHWOOD, or execution products;
- automatic sharing merely because the same email/account exists;
- ecosystem-wide execution authority;
- hidden synchronization of files, interviews, portfolio records, or observations;
- a requirement that every product adopt shared login at once.

The shared contract exists so products can add continuity incrementally without weakening isolation or user control.
