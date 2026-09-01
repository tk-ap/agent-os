# Cross-Market Policy

Cross-product recommendations are a continuation of delivered value, not a requirement to advertise every product in the ecosystem.

## Eligibility Test

A cross-product recommendation is allowed only when all are true:

1. The current product or workflow has delivered its core value moment.
2. The adjacent product solves the user's next visible problem.
3. The benefit is explainable in one sentence.
4. Relevant state can carry forward, or the recommendation clearly states what will not carry forward.
5. Declining the recommendation does not block completion of the current workflow.
6. The recommended capability is implemented or clearly labeled as preview/planned; do not imply an integration exists when it has not been verified.

## Routing Rules

- Use `registry/product-routing.yaml` to identify the adjacent product or shared capability that actually owns the next problem.
- Prefer a portable handoff/work item over duplicating the adjacent product's core capability.
- Preserve context provenance and permission boundaries when state crosses products.
- Do not bypass authorization requirements merely because a cross-product handoff is convenient.
- Shared Agent OS / Workforce capabilities may support multiple products but should not be marketed as a separate public product by default.

## Prohibited Patterns

- generic ecosystem banners without a relevant next need;
- blocking a completed workflow with an unrelated product pitch;
- recommending every adjacent product merely because it exists;
- claiming a live integration before implementation and verification;
- copying another product's core responsibility to avoid a handoff;
- using cross-marketing to override product boundaries or authorization controls.

## Evidence

When a cross-market recommendation materially affects a user journey or growth experiment, preserve the originating signal, recommendation rationale, acceptance/decline result when available, and downstream outcome so the portfolio can learn whether the handoff was useful.
