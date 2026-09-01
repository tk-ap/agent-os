---
name: context-provenance
description: Assess, merge, and transmit context with source, consent, confidence, freshness, conflict, and decay metadata. Use for ALVIRA/MeOS context, agent memory, seeded interviews, or cross-product context transfer.
---

# Context Provenance

Treat context quality as a retrieval and evidence problem, not a volume problem.

## Context Record

Capture:

- claim or normalized field;
- source type and stable source reference;
- subject and intended scope;
- collection time and last validation time;
- confidence and reason;
- consent/permission boundary;
- conflicts, superseded values, and decay rule;
- downstream consumers.

## Workflow

1. Distinguish user-supplied, document-derived, observed, inferred, and generated context.
2. Prefer the most authoritative current source; preserve material disagreement rather than silently merging it.
3. Reuse validated seeded answers and ask only real gaps.
4. Do not convert contextual relevance into authorization to execute.
5. Minimize sensitive context shared with each consumer.
6. Revalidate stale or consequential context before high-impact decisions.
7. Record corrections so dependent systems can invalidate superseded context.

## ALVIRA/MeOS Invariants

- Shared interview machinery does not require one combined mega-interview.
- Cross-seeding must retain provenance and confidence.
- A carried-over field must remain reviewable and correctable.
- Reflection updates should create a traceable change, not erase history.

## Output

Return accepted context, conflicts, gaps, permission limits, freshness risks, and required revalidation.
