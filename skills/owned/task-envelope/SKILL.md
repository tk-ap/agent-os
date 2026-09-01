---
name: task-envelope
description: Turn a signal, objective, or request into a governed unit of work with ownership, context, authority, budget, success criteria, and verification. Use before cross-agent, cross-product, or externally mutating execution.
---

# Task Envelope

Create the smallest complete work packet an agent can execute safely.

## Required Fields

- objective and expected user/business outcome;
- originating signal and evidence;
- owning product/shared capability from `registry/product-routing.yaml`;
- accountable owner and executing agent(s);
- repositories, environments, and exact targets;
- relevant context plus provenance;
- constraints and protected regression boundaries;
- permitted actions and required approvals;
- estimated execution cost and human oversight;
- success criteria, verification method, and evidence destination;
- stop conditions, rollback, and handoff state.

## Portable Contract Mapping

Use these only when their boundary is actually crossed:

- `contracts/work-item.schema.json` — serialize a proposed/accepted task that crosses a product or workspace boundary.
- `contracts/capability-manifest.schema.json` — describe the minimum agents, skills, tools, resources, and harness candidates for material coordinated work.
- `contracts/context-envelope.schema.json` — carry least-privilege ALVIRA-derived context references with provenance.
- `contracts/authorization-request.schema.json` — request authorization intelligence from Agent Control before governed action.
- `contracts/outcome-event.schema.json` — return bounded execution status, artifacts, verification, authority evidence, cost, and measured outcome.

## Rules

- Missing authority is not an implementation detail. Pause before the mutation.
- Keep inferred context distinguishable from supplied or verified context.
- Do not broaden the target because adjacent work appears useful.
- Do not duplicate another product's core responsibility; route a work item to the owner instead.
- Prefer reversible steps and preview branches for uncertain public-facing changes.
- A task is not complete when code exists; it is complete when the intended result is verified and material evidence has a destination.
- ailhat findings and Growth intelligence enter the workforce as proposed task envelopes, not direct commands.
- LEDGATo is involved only when governance/enforcement is materially relevant; Agent Control remains the authorization-intelligence owner where integrated.

## Routing

Router classifies and coordinates. Steward owns objective priority. Bill owns sequencing. Ledger owns budget analysis. Rook owns adversarial and permission-risk review. Agent Control owns authorization intelligence where required. Eugene owns implementation. W Dog owns independent verification and contradiction detection.

## Output

Return the task envelope, missing fields, owning product/shared capability, authorization state, portable contracts required (if any), evidence destination, and the next permitted action.
