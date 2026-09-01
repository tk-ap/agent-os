---
name: opportunity-triage
description: Assess an external opportunity signal against the existing portfolio, founder context, reusable leverage, execution demands, and strategic risk; return one primary portfolio recommendation with rationale and calibrated confidence.
---

# Opportunity Triage

Use this skill when ailhat or another trusted source supplies an external signal that needs portfolio interpretation. Do not use it to generate an unbounded list of startup ideas.

## Ownership and evidence

- Scout owns external-signal quality and identifies what is observed versus inferred.
- Zoie owns opportunity interpretation and portfolio recombination.
- Steward owns portfolio attention and initiative priority.
- Bring in Eugene for material technical feasibility, Bill for execution readiness, Ledger for material economics, and Rook for material strategic, permission, privacy, or irreversible risk.
- A signal proposes attention. It does not authorize external action, spending, publishing, or production change.

Preserve the source and capture time. Mark absent, stale, weak, or conflicting evidence explicitly. Do not convert source enthusiasm, category growth, or founder excitement into proof of demand.

## Assessment

1. Restate the underlying problem, affected audience, evidence, and market momentum.
2. Map overlap with existing products, capabilities, workflows, data, distribution, and IP. Identify duplication and cannibalization as well as leverage.
3. Assess founder/context fit only from supplied or approved context; say `unknown` when it is unavailable.
4. Identify capabilities required to act and distinguish existing from missing capabilities.
5. Estimate agent-executable work, human oversight, major dependencies, execution cost, and time-to-learning. Use ranges when precision is unsupported.
6. Test strategic risk: distraction, boundary erosion, positioning conflict, platform dependency, privacy/security, irreversible commitment, and opportunity cost.
7. Select exactly one primary recommendation:
   - `ABSORB` — strengthen a current capability or internal operating layer without expanding the public product promise.
   - `EXTEND` — add to an existing product because the signal fits its current customer and promise.
   - `EXPERIMENT` — run the smallest bounded test needed to resolve a decision-critical uncertainty.
   - `WATCH` — preserve and monitor the signal because evidence, timing, or fit is insufficient for action.
   - `SPIN_OUT` — treat as a potentially distinct venture only when separation is strategically material and evidence justifies further validation.
   - `REJECT` — decline because downside, redundancy, weak fit, or insufficient credible value outweighs learning value.

Prefer absorption or extension when existing portfolio leverage creates the value. Prefer an experiment when one bounded test can cheaply change the decision. `SPIN_OUT` is not the default for an attractive idea.

## Output contract

Return a compact decision record:

```yaml
signal:
  source: string
  captured_at: timestamp
  problem: string
  audience: string
evidence_assessment:
  observed: [string]
  inferred: [string]
  gaps: [string]
portfolio_fit:
  overlap: [string]
  existing_leverage: [string]
  founder_context_fit: strong | moderate | weak | unknown
execution:
  required_capabilities: [string]
  agent_execution_estimate: string
  human_oversight: string
  dependencies: [string]
risk:
  level: low | moderate | high
  factors: [string]
recommendation: ABSORB | EXTEND | EXPERIMENT | WATCH | SPIN_OUT | REJECT
rationale: string
confidence: 0-100
next_evidence: string
```

Return one primary recommendation, not a menu. Confidence measures the adequacy and consistency of evidence for the recommendation, not enthusiasm for the opportunity.
