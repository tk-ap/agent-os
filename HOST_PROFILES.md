# Agent OS Host Profiles

Status: **conceptual documentation only**. This file does not authorize implementation, installation, production access, credential changes, or host migration.

## Why host profiles exist

Agent OS should remain portable across developer workstations and execution environments. A **host** is the human/agent workstation where work is initiated, inspected, and supervised. A **target/runtime** is the environment where an application or workload actually runs.

Those roles must stay distinct:

```text
human + agent workstation (host)
        ↓ explicit access
repository / remote runtime / service (target)
        ↓ governed execution
verification + evidence
```

A host profile may describe useful local tooling and interaction conventions. It must not redefine Agent OS ownership, bypass policy, or imply access to a target.

## Core rule: Agent OS is host-agnostic

No workstation environment is a hard dependency of Agent OS.

A host profile may provide:

- terminal, shell, editor, browser, and workspace conventions;
- local agent/harness tooling;
- session and window-management patterns;
- repository checkout and inspection workflows;
- a clear human-visible place to approve, interrupt, and verify work.

A host profile does **not** provide by default:

- production authorization;
- deployment permission;
- secrets or a secrets registry;
- an agent control plane;
- autonomous escalation of privileges;
- authority to merge or mutate protected branches.

## Omarchy host concept

Omarchy is a candidate **Linux workstation host profile** for Agent OS, not a separate Agent OS product and not a required runtime.

The useful hypothesis is that an Omarchy workstation can package a coherent developer surface around terminal sessions, tmux, editor workflows, browser access, and agent-facing development tools while preserving an obvious boundary between the local workstation and remote targets.

In this model:

- **Omarchy owns the workstation experience.** It may organize local windows, sessions, tools, and developer ergonomics.
- **Agent OS owns workforce policy.** Agent identity, routing, skill resolution, handoffs, autonomy rules, and verification remain portable.
- **Repositories own product truth.** Product-specific instructions and code remain authoritative in their own repositories.
- **Remote targets own runtime state.** VPS, cloud, container, CI, and production environments are not treated as extensions of the workstation merely because the host can connect to them.
- **Authorization remains explicit.** A convenient host must not collapse the difference between being able to reach a system and being authorized to change it.

## Security and privacy boundary

The host is a security boundary, not a place to make credentials portable by copying them into Agent OS.

Host-profile documentation and declarative setup artifacts must not contain:

- API keys, tokens, passwords, private keys, or recovery material;
- production credentials or reusable session material;
- hidden assumptions that a local agent has production access;
- instructions that weaken repository, provider, or operating-system protections just to reduce friction.

Where credentials are needed, the profile should refer only to the approved host-level or provider-level mechanism. Secrets stay outside this repository.

## Reversibility requirement

Adopting a host profile must be reversible. A user should be able to move the same Agent OS repository and policies to another supported host without rewriting the organizational model.

That means Omarchy-specific behavior should live in an adapter/profile layer if implementation is later approved, rather than leaking into agent identities, product routing, or shared policy.

## Working acceptance criteria

The Omarchy host concept is worth implementing only if a later, separately approved experiment can show that it:

1. reduces workstation setup and task-switching friction without changing Agent OS policy semantics;
2. preserves a visible host-versus-target boundary;
3. keeps secrets out of Agent OS and declarative repository artifacts;
4. requires explicit authorization for production or privileged targets;
5. supports interruption, inspection, and verification by the human operator;
6. remains optional and does not make other host environments second-class at the core-policy level.

Failure on the security, authorization, or portability criteria should block adoption regardless of ergonomic gains.

## Gated next step

A future implementation proposal may define an `adapters/omarchy/` or equivalent host-profile contract. That work is intentionally **not part of this documentation change** and requires its own approval, branch, review, and verification.
