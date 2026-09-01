# Agent OS Handoff Policy

## Principle
Handoffs move work to the agent, product, or shared capability that owns the next decision layer. Router enforces flow; domain agents own judgments; `registry/product-routing.yaml` defines canonical product boundaries; Steward owns objective-level accountability.

## Standard Agent Contract
Every meaningful agent handoff contains WORK REF, FROM, TO, OUTCOME, CONTEXT, AUTHORITY, OPEN QUESTIONS, DEPENDENCIES, ACCEPTANCE, and when material: COST/RISK and LOOP/ESCALATION.

A structured handoff should preserve enough context and evidence for the next owner to act without reconstructing intent, while avoiding unrelated context loading.

If authority, acceptance, or ownership is unclear, the handoff is not ready.

## Agent vs. Skill Boundary
Before creating a new persistent agent to receive a handoff, Router must test whether the need is actually a reusable capability that belongs as a skill under an existing owner.

Prefer a skill when the work can remain inside an existing decision domain and does not require materially isolated context, permissions, independent judgment, or execution characteristics.

A new persistent agent requires a durable ownership/trust boundary and explicit human approval before registry activation. Use `skills/owned/agent-identity-design/SKILL.md` for the design/review contract.

## Producer / Inspector Loops
Use producer/inspector loops only when independent review materially reduces risk or improves evidence quality.

For every loop, define before iteration begins:

- producer;
- inspector and the independent domain being checked;
- acceptance criteria;
- evidence required for acceptance;
- maximum revision-cycle count;
- budget/authority boundaries that terminate the loop early;
- escalation owner if acceptance is not reached.

The inspector must report failed acceptance criteria and evidence, not merely a preference for another iteration.

The producer receives only the actionable failed criteria needed for revision. Do not turn inspection into a free-form conversation loop.

Terminate the loop when:

- acceptance criteria are satisfied;
- the maximum cycle count is reached;
- the same disagreement repeats without new evidence;
- authority or budget limits are reached;
- the next decision belongs to a human or different domain owner.

When the loop terminates without acceptance, escalate. Do not restart the same loop under a different label.

## Recurring-Work Handoffs
Repeated work does not inherit broader authority from prior successful runs.

When a handoff creates or changes recurring work, compose with `skills/owned/recurring-work/SKILL.md` and preserve trigger, skip/no-op condition, output side effects, authority class, cost boundary, verification, stop conditions, and escalation state.

A scheduler is an execution mechanism, not an authority source.

## Portable Cross-Product Contracts

Use portable contracts when work crosses a product, workspace, or execution boundary. The contract makes the handoff explicit; it does not authorize the receiver to ignore local policy.

- `contracts/work-item.schema.json` — use for a proposed or accepted unit of cross-product/cross-workspace work. ailhat findings and Growth intelligence enter the workforce as proposed work, not direct commands.
- `contracts/capability-manifest.schema.json` — use when the receiving workflow needs a machine-readable statement of the minimum agents, skills, tools, resources, and harness candidates required.
- `contracts/context-envelope.schema.json` — use when ALVIRA-derived context must cross into a workflow. Preserve provenance and least-privilege use; ALVIRA remains the context-intelligence source.
- `contracts/authorization-request.schema.json` — use before governed external action when authorization intelligence is required. Agent Control owns that decision layer where integrated.
- `contracts/outcome-event.schema.json` — use after bounded execution to return status, artifacts, verification, authority evidence, cost, and measured outcome to the appropriate evidence/portfolio loop.

LEDGATo may receive or produce governance/enforcement evidence when the work intersects its defined scope. Do not route generic authorization decisions to LEDGATo merely because an action is sensitive.

## Cross-Product Write Rule

A product or agent may propose work to another owner, but must not silently implement the other owner's core responsibility. Direct edits to another product repository require explicit task authorization and must preserve that repository's local instructions and regression boundaries.

Local `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` files may declare repository-specific integration details, but they may not redefine product ownership established in `registry/product-routing.yaml`.

## Primary Relationships
- Scout → Zoie: external signal requires strategic interpretation.
- Scout → Designer: customer evidence should change experience.
- Scout → Ledger: market/pricing signal changes economics.
- Scout → Router: accepted Market Truth / Growth experiment needs a governed work item.
- Zoie → Steward: opportunity is mature enough for initiative consideration.
- Zoie → Eugene: opportunity requires technical feasibility.
- Zoie → Bill: accepted direction requires execution planning.
- Designer → Eugene: experience direction requires technical implementation.
- Designer → Scout: experience hypothesis needs customer validation.
- Eugene → Designer: technical constraints materially affect experience.
- Eugene → Bill: technical direction is ready to operationalize.
- Bill → Eugene: execution exposes technical blocker.
- Bill → W Dog: execution needs systemic verification/recurrence prevention.
- Bill → Rook: recurring/external work needs permission or failure-mode review.
- Bill → Ledger: recurring/execution work has material cost or budget exposure.
- W Dog → Eugene: systemic issue has technical root/remediation.
- W Dog → Bill: systemic issue needs operational closure.
- Rook → Eugene: adversarial finding requires technical mitigation.
- Rook → Bill: control requires operational implementation.
- Rook → Steward: residual material risk requires business acceptance or escalation.
- Ledger → Steward: economics materially change initiative priority.
- Ledger → Bill: execution plan exceeds resource/economic threshold.
- Steward → Router: objective decision requires coordinated work.
- Router → specialists: dispatch only the minimum sufficient team.

## Default Initiative Loop
1. Establish the owning product/shared capability from `registry/product-routing.yaml`.
2. Scout supplies external evidence when relevant.
3. Zoie frames opportunity and leverage.
4. Ledger tests economics when material.
5. Steward decides initiative priority within authority.
6. Designer defines customer experience when applicable.
7. Eugene defines technical truth when applicable.
8. Rook attacks material risk, abuse, permissions, and irreversibility.
9. Router/Bill convert accepted direction into a task envelope and, when useful, a `work-item` plus `capability-manifest`; Bill defines a recurring-work contract when repetition is required.
10. Request ALVIRA context and/or Agent Control authorization only when the work actually needs those decision layers.
11. The selected harness executes bounded work.
12. W Dog verifies systemic closure, propagation, recurrence prevention, and material routine verification when applicable.
13. Return an `outcome-event` or equivalent evidence to the relevant portfolio/evidence loop.
14. Steward reviews outcome versus KPI and chooses keep / accelerate / change / stop.
15. Router coordinates and synthesizes throughout without replacing domain ownership.

Skip any agent, product, contract, or review loop whose perspective or data would not materially improve the decision.

## Disagreement
Do not force consensus. Identify the disputed premise, decision owner, missing evidence, material minority concern, and applicable authority class. Steward resolves objective/portfolio tradeoffs within delegated authority; human escalation follows `policies/AUTONOMY_POLICY.md`.

Repeated disagreement without new evidence is a loop-termination condition, not a reason to continue cycling agents.

## Anti-Patterns
Do not send every task to every agent; duplicate analysis without purpose; use Router as a domain expert; use Steward as a universal executor or universal ecosystem owner; let skills redefine ownership; create a new persistent agent when an existing owner plus skill is sufficient; dynamically activate persistent agents without human approval; let Zoie decide technical truth; let Eugene decide market demand; let Bill silently change architecture; let Designer infer customer demand without evidence when evidence is obtainable; let Ledger optimize only for cost; let Rook become a blanket blocker; let W Dog become the default implementer; let producer/inspector loops run without acceptance and termination conditions; treat a recurring schedule as permission to expand scope; create a second product-role registry; treat Agent OS / Workforce as a standalone public product; treat ALVIRA Bridge as a separate public product; or assign generic authorization intelligence to LEDGATo.
