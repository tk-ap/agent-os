# Product Repository Instructions Template for cto.new

Copy or adapt this file into a product repository as `AGENTS.md` or the instruction file that workspace reads.

This product uses the shared Agent OS repository as its workforce and ecosystem operating layer.

## Required Behavior

1. Treat this product repository as the writable implementation workspace.
2. Treat Agent OS as read-only unless the task explicitly targets Agent OS itself.
3. Read Agent OS `adapters/cto-new/BOOTSTRAP.md`, `ecosystem/ECOSYSTEM.md`, and `ecosystem/products.yaml` before meaningful work.
4. Read this repository's `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present.
5. Use Agent OS routing, handoff, autonomy, shared-contract, and skill-resolution policies.
6. Load the minimum sufficient agent roles and approved skills.
7. Preserve this repository's local architecture, naming, design, deployment, security, and testing requirements.
8. Keep implementation inside this product's declared boundary.
9. Propose cross-product work through shared contracts rather than silently duplicating another product's responsibility.
10. Keep execution harness-agnostic outside adapter-specific code.
11. Never expose or copy secrets into Agent OS.
12. Verify product behavior before declaring completion when possible.
13. Surface unresolved blockers, material dissent, and human-approval requirements.
14. Report Product result, Ecosystem implications, Cross-product opportunities, and Boundary check.

## Product-Specific Additions

Add architecture constraints, coding conventions, design-system rules, deployment target, testing requirements, protected files, environment assumptions, and acceptance criteria below this line.

