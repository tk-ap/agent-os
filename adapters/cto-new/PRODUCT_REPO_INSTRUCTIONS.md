# Product Repository Instructions Template for cto.new

Copy or adapt this file into a product repository as `AGENTS.md` or the instruction file that workspace reads.

This product uses the shared Agent OS repository as its workforce operating layer.

## Required Behavior

1. Treat this product repository as the writable implementation workspace.
2. Treat Agent OS as read-only unless the task explicitly targets Agent OS itself.
3. Read Agent OS `adapters/cto-new/BOOTSTRAP.md` before meaningful work.
4. Read `registry/product-routing.yaml` and identify the canonical product/shared-capability owner before implementation.
5. Read this repository's `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present; local files may add detail but may not redefine canonical product roles.
6. Use Agent OS routing, handoff, autonomy, portable-contract, and skill-resolution policies.
7. Load the minimum sufficient agent roles and approved skills for the task.
8. Preserve this repository's local architecture, naming, design, deployment, security, regression boundaries, and testing requirements.
9. Do not implement another product's core responsibility merely because it is convenient in this repository; produce a handoff/work item instead.
10. Direct writes to another product repository require explicit task authorization.
11. Never expose or copy secrets into Agent OS.
12. Do not modify Agent OS merely to make a product task easier.
13. Verify product behavior before declaring completion when verification is possible.
14. Return material outcome evidence and surface unresolved blockers, dissent, or approval requirements explicitly.

## Product-Specific Additions

Add below this line:

- product key from `registry/product-routing.yaml`
- architecture constraints
- coding conventions
- design-system rules
- deployment target
- testing requirements
- protected files or directories
- environment assumptions
- acceptance criteria
- local integration surfaces
