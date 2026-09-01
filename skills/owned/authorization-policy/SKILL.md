---
name: authorization-policy
description: Design or evaluate allow, deny, approve, and escalate decisions for agent actions. Use when an action affects external systems, credentials, money, production, communications, personal data, or irreversible state.
---

# Authorization Policy

Keep capability, recommendation, and authority separate.

## Decision Inputs

- actor and authenticated identity;
- requested action and exact resource;
- originating task envelope;
- authority source and scope;
- data sensitivity and external recipients;
- reversibility and blast radius;
- spend/time limit;
- required human or system approval;
- expiration and revocation conditions.

## Decision

Return exactly one state: `allow`, `deny`, `approve-required`, or `clarify`.

Include the policy basis, scope, conditions, expiration, and audit evidence. An `allow` decision applies only to the described action and target.

## Rules

- Default to least privilege, not blanket access.
- Never infer send, publish, merge, deploy, purchase, delete, or credential authority from read access.
- Require fresh approval when target, audience, cost, or irreversibility materially changes.
- Approval UI is not proof that enforcement occurred.
- Agent Control may represent authorization intelligence; LEDGATo enforcement claims require runtime evidence.
- Denials and escalations must be recorded without exposing secrets.

## Verification

Test permitted, denied, expired, revoked, replayed, and scope-escalated cases. Verify enforcement at the action boundary, not only in the interface.
