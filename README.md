# Agent OS

Portable multi-agent operating system for an autonomous business workforce: Router, Steward, Zoie, Scout, Designer, Ledger, Eugene, Rook, Bill, and W Dog.

## Structure

- `BOOTSTRAP.md` — universal workspace entry point and adapter detection.
- `agents/` — stable agent identities and organizational ownership.
- `registry/agents.yaml` — routing, ownership, and capability domains.
- `registry/skills.yaml` — approved/planned skill catalog, trust model, provenance, and discovery sources.
- `skills/skill-resolver/SKILL.md` — just-in-time skill selection, acquisition, and external discovery policy.
- `skills/vendor/` — reviewed third-party skills adapted/pinned for Agent OS runtime.
- `policies/AUTONOMY_POLICY.md` — autonomous action, control-check, and human-escalation rules.
- `policies/HANDOFF_POLICY.md` — ownership transitions and multi-agent council behavior.
- `adapters/` — environment-specific integration contracts.

## cto.new Adapter

`adapters/cto-new/` defines how Agent OS operates when a cto.new project has access to both a product repository and this repository.

- `BOOTSTRAP.md` — execution model and load order.
- `WORKSPACE_CONTRACT.yaml` — machine-readable repository/precedence/permission contract.
- `PRODUCT_REPO_INSTRUCTIONS.md` — template to copy or adapt into a product repository as `AGENTS.md` or equivalent.

Default model: the product repository is writable and authoritative for product-specific rules; Agent OS is read-only and authoritative for workforce policy, routing, handoffs, autonomy, and approved skills.

## Design Principle

**Identity is stable. Capability is composable. Context is workspace-specific.**

Use the minimum sufficient team and minimum sufficient skill set for each task. Adapters translate this operating model into each execution environment without changing organizational ownership.
