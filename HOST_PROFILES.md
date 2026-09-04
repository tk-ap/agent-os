# Agent OS Host Profiles

Status: **Omarchy Host Pilot 01 approved and in implementation; all other host profiles remain conceptual unless separately approved.** This file does not grant production access, credential changes, deployment authority, or host migration by itself.

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

## Omarchy Host Pilot 01

Omarchy is the first implemented **Linux workstation host profile** for Agent OS. It is not a separate Agent OS product and not a required runtime.

The pilot target is a local, human-controlled LLM-adjacent workstation where Agent OS governs task routing, policy, authorization gates, harness selection, local task state, verification, and evidence while one or more remote or local inference providers remain replaceable execution dependencies.

The pilot implementation lives under `adapters/omarchy/` and must preserve these boundaries:

- **Omarchy owns the workstation experience.** It may organize local windows, sessions, tools, and developer ergonomics.
- **Agent OS owns workforce policy.** Agent identity, routing, skill resolution, handoffs, autonomy rules, and verification remain portable.
- **Repositories own product truth.** Product-specific instructions and code remain authoritative in their own repositories.
- **Harnesses provide execution surfaces.** Codex, Claude Code, OpenCode, or other approved harnesses may execute bounded tasks but do not grant authority.
- **Inference providers are replaceable.** Remote providers and experimental local providers such as Magnitude may supply model inference without changing Agent OS policy semantics.
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

Blanket passwordless sudo is forbidden for Agent OS execution. Privileged actions require explicit, bounded human authorization and must remain distinguishable from ordinary local task execution.

## Reversibility requirement

Adopting a host profile must be reversible. A user should be able to move the same Agent OS repository and policies to another supported host without rewriting the organizational model.

Omarchy-specific behavior therefore lives in the adapter/profile layer rather than agent identities, product routing, or shared policy.

## Working acceptance criteria

Omarchy Host Pilot 01 is worth adopting only if it can show that it:

1. reduces workstation setup and task-switching friction without changing Agent OS policy semantics;
2. preserves a visible host-versus-target boundary;
3. keeps secrets out of Agent OS and declarative repository artifacts;
4. requires explicit authorization for production or privileged targets;
5. supports interruption, inspection, and verification by the human operator;
6. remains optional and does not make other host environments second-class at the core-policy level;
7. exposes at least one usable LLM harness path while keeping the model/provider replaceable.

Failure on the security, authorization, or portability criteria blocks adoption regardless of ergonomic gains.

## Current pilot surface

The pilot introduces:

- `adapters/omarchy/README.md` — host operating model;
- `adapters/omarchy/HOST_CONTRACT.yaml` — declarative host boundaries;
- `adapters/omarchy/providers/magnitude.yaml` — experimental local-provider candidate;
- `runtime/doctor.py` — read-only host readiness inspection;
- `./agent-os doctor` — local readiness command;
- `./agent-os run` — current governed task pipeline entry point;
- `./agent-os serve` — local Task API bound to `127.0.0.1:8787`.

This pilot surface does **not** yet mean that a production-grade LLM harness has been connected or that remote mutation authority has been enabled. Those are separate verified steps.
