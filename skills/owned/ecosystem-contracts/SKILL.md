---
name: ecosystem-contracts
description: Define or review boundaries, interfaces, shared schemas, and source-of-truth rules across Agent OS products and execution environments. Use when work crosses product, repository, data, or authority boundaries.
---

# Ecosystem Contracts

Make cross-system assumptions explicit before implementation.

## Contract Record

For each boundary, identify:

- producer and consumer;
- purpose and owner;
- input/output schema or artifact;
- source of truth and precedence;
- freshness, version, and compatibility expectations;
- permission and data-classification requirements;
- failure behavior, fallback, and rollback;
- verification evidence.

## Workflow

1. Read product-local instructions before shared Agent OS guidance.
2. Confirm the public/product boundary; do not invent a standalone offering to simplify architecture.
3. Separate implemented behavior from intended behavior.
4. Reuse an existing contract when it is authoritative and compatible.
5. Record additive versus breaking changes and affected consumers.
6. Route technical contract decisions to Eugene, contradiction review to W Dog, authorization implications to Rook, and sequencing to Bill.
7. Do not call the integration complete until producer and consumer behavior are both verified.

## Ecosystem Invariants

- Agent OS/Workforce is shared execution infrastructure, not a separate public product.
- ALVIRA/MeOS context is not automatically permission to act.
- ailhat signals propose or prioritize work; they do not silently authorize execution.
- Agent Control owns authorization intelligence.
- LEDGATo enforcement must not be described as production-proven without runtime evidence.
- ASHWOOD publishes selected evidence and narrative; it is not the operational source of truth.

## Output

Return a concise contract, affected systems, unresolved assumptions, migration/rollback needs, and the evidence required to accept it.
