## Agent OS product-routing appendix

This repository participates in the shared Agent OS / Workforce operating layer.

Before material planning or implementation:

1. Read Agent OS `BOOTSTRAP.md` and `registry/product-routing.yaml`.
2. Read this repository's `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present.
3. Identify the canonical owning product or shared capability before selecting agents or skills.
4. Keep implementation inside this product's declared boundary and local regression constraints.
5. Use the portable contracts under `contracts/` for cross-product, context, authorization, capability, or outcome handoffs when their boundary is crossed.
6. Propose adjacent work to the owning product; do not silently duplicate its core responsibility here.
7. Treat Agent OS / Workforce as shared infrastructure, not a separate public product.

Local `.agent-os/` metadata supplements `registry/product-routing.yaml`; it must not create a competing product-role definition.

Cross-market recommendations must follow `policies/CROSS_MARKET_POLICY.md`: deliver the current value first, recommend only a next visible need, and never make an adjacent product mandatory to finish the current workflow.
