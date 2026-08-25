# Agent OS

Portable multi-agent operating system for W Dog, Zoie, Bill, Eugene, and Router.

## Structure

- `BOOTSTRAP.md` — workspace entry point and load order.
- `agents/` — stable agent identities.
- `registry/agents.yaml` — routing, ownership, and capability domains.
- `registry/skills.yaml` — skill catalog, trust model, and discovery sources.
- `skills/skill-resolver/SKILL.md` — just-in-time skill selection and external discovery policy.
- `policies/HANDOFF_POLICY.md` — ownership transitions and multi-agent council behavior.

## Design Principle

**Identity is stable. Capability is composable. Context is workspace-specific.**

Use the minimum sufficient team and minimum sufficient skill set for each task.
