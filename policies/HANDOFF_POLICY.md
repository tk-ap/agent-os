# Agent OS Handoff Policy

## Principle

Handoffs move work to the agent or product that owns the next decision layer. Router enforces flow; domain agents own judgments; product contracts preserve ecosystem boundaries; Steward owns objective-level accountability.

## Standard Agent Contract

Every meaningful agent handoff contains FROM, TO, OUTCOME, CONTEXT, OPEN QUESTIONS, DEPENDENCIES, ACCEPTANCE, and when material: COST/RISK and AUTHORITY CLASS.

## Standard Product Contract

Cross-product work must use the relevant schema under `contracts/` and identify source product, owning product, desired outcome, evidence, constraints, acceptance criteria, status, and timestamps.

- Ailhat -> Agent OS: `work-item.schema.json`
- Agent OS -> Bridge: `context-envelope.schema.json`
- Agent OS -> Ledgato: `capability-manifest.schema.json` plus `authority-request.schema.json`
- Agent OS -> agentic harness: authorized work item and context envelope
- Agentic harness -> Ailhat: `outcome-event.schema.json`

A product agent proposes work to the owning product. It does not silently implement the other product's core responsibility.

## Primary Relationships

- Scout -> Zoie: external signal requires strategic interpretation.
- Scout -> Designer: customer evidence should change experience.
- Scout -> Ledger: market/pricing signal changes economics.
- Zoie -> Steward: opportunity is mature enough for initiative consideration.
- Zoie -> Eugene: opportunity requires technical feasibility.
- Zoie -> Bill: accepted direction requires execution planning.
- Designer -> Eugene: experience direction requires technical implementation.
- Designer -> Scout: experience hypothesis needs customer validation.
- Eugene -> Designer: technical constraints materially affect experience.
- Eugene -> Bill: technical direction is ready to operationalize.
- Bill -> Eugene: execution exposes technical blocker.
- Bill -> W Dog: execution needs systemic verification/recurrence prevention.
- W Dog -> Eugene: systemic issue has technical root/remediation.
- W Dog -> Bill: systemic issue needs operational closure.
- Rook -> Eugene: adversarial finding requires technical mitigation.
- Rook -> Bill: control requires operational implementation.
- Rook -> Steward: residual material risk requires business acceptance or escalation.
- Ledger -> Steward: economics materially change initiative priority.
- Ledger -> Bill: execution plan exceeds resource/economic threshold.
- Steward -> Router: objective decision requires coordinated work.
- Router -> specialists: dispatch only the minimum sufficient team.

## Default Ecosystem Loop

1. Ailhat or a human supplies an objective-backed work item.
2. Router selects the minimum sufficient team.
3. Agent OS produces a capability manifest and execution plan.
4. Bridge resolves the least-privilege context envelope when context is required.
5. Ledgato resolves effective authority and required approvals.
6. Bill selects an appropriate agentic harness based on capability, cost, availability, and policy.
7. The harness executes bounded work and returns artifacts, verification, cost, and authority evidence.
8. W Dog verifies systemic closure when material.
9. Ailhat measures the outcome.
10. Steward chooses keep / accelerate / change / stop.

Skip any agent or product interaction that would not materially improve the decision or result.

## Disagreement

Do not force consensus. Identify the disputed premise, decision owner, missing evidence, material minority concern, and applicable authority class. Steward resolves objective/portfolio tradeoffs within delegated authority; human escalation follows `policies/AUTONOMY_POLICY.md`.

## Anti-Patterns

Do not send every task to every agent; duplicate analysis without purpose; use Router as a domain expert; use Steward as a universal executor; let skills redefine ownership; let one product absorb another product's core capability; use Bridge as operational authorization; use Ledgato as context authorship; let Ailhat become a canonical workforce registry; hard-code cto.new or Codex into portable contracts; advertise every ecosystem product in every workflow; or declare execution complete before outcome evidence returns.

