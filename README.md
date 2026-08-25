# Agent OS

Portable multi-agent operating system for an autonomous business workforce: Router, Steward, Zoie, Scout, Designer, Ledger, Eugene, Rook, Bill, and W Dog.

## Structure

- `BOOTSTRAP.md` - universal workspace entry point, ecosystem load order, and adapter detection.
- `ecosystem/` - canonical product boundaries, journeys, integration map, and cross-market policy.
- `products/` - product-specific agent directives.
- `contracts/` - portable work-item, context, capability, authority, and outcome contracts.
- `agents/` - stable agent identities and organizational ownership.
- `registry/agents.yaml` - routing, ownership, and capability domains.
- `registry/skills.yaml` - approved/planned skill catalog, trust model, provenance, and discovery sources.
- `skills/skill-resolver/SKILL.md` - just-in-time skill selection, acquisition, and external discovery policy.
- `skills/vendor/` - reviewed third-party skills adapted/pinned for Agent OS runtime.
- `policies/AUTONOMY_POLICY.md` - autonomous action, control-check, and human-escalation rules.
- `policies/HANDOFF_POLICY.md` - ownership transitions, cross-product handoffs, and multi-agent council behavior.
- `adapters/` - environment- and product-repository integration contracts.

## Ecosystem Model

- **ALVIRA** owns context intelligence.
- **ALVIRA Bridge** owns permissioned context distribution.
- **Ailhat** owns portfolio intelligence and outcome measurement.
- **Agent OS / Workflow Studio** owns workforce organization and routing.
- **Ledgato** owns operational authorization and evidence.
- **Agentic harnesses** provide replaceable execution leverage.

Bridge governs what agents may know. Ledgato governs what agents may do.

## Product Repository Adapter

Each ecosystem product repository should include:

- `AGENTS.md` with the ecosystem-awareness appendix;
- `.agent-os/product.yaml` declaring ownership and boundaries;
- `.agent-os/integration-surface.yaml` declaring handoffs and cross-market triggers;
- `.agent-os/ecosystem-version` pinning the contract version.

Templates live in `adapters/product-repo/`.

## cto.new Adapter

`adapters/cto-new/` defines how Agent OS operates when a cto.new project has access to both a product repository and this repository.

Default model: the product repository is writable and authoritative for product-specific rules; Agent OS is read-only and authoritative for workforce policy, ecosystem boundaries, routing, handoffs, autonomy, and approved skills.

cto.new is one agentic harness, not a privileged architectural dependency.

## Design Principle

**Identity is stable. Capability is composable. Context is workspace-specific. Execution harnesses are replaceable.**

Use the minimum sufficient team and skill set. Protect product boundaries, communicate through shared contracts, and close every execution loop with evidence and outcome measurement.

