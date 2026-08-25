# Product Repository Instructions Template for cto.new

Copy or adapt this file into a product repository as `AGENTS.md` or the instruction file that workspace reads.

This product uses the shared Agent OS repository as its workforce operating layer.

## Required Behavior

1. Treat this product repository as the writable implementation workspace.
2. Treat Agent OS as read-only unless the task explicitly targets Agent OS itself.
3. Read Agent OS `adapters/cto-new/BOOTSTRAP.md` before meaningful work.
4. Use Agent OS routing, handoff, autonomy, and skill-resolution policies.
5. Load the minimum sufficient agent roles and approved skills for the task.
6. Preserve this repository's local architecture, naming, design, deployment, security, and testing requirements.
7. Never expose or copy secrets into Agent OS.
8. Do not modify Agent OS merely to make a product task easier.
9. Verify product behavior before declaring completion when verification is possible.
10. Surface unresolved blockers, material dissent, and human-approval requirements explicitly.

## Product-Specific Additions

Add below this line:

- architecture constraints
- coding conventions
- design-system rules
- deployment target
- testing requirements
- protected files or directories
- environment assumptions
- acceptance criteria
