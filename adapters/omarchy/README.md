# Omarchy LLM Host Adapter

Status: **Host Pilot 01 / bounded implementation**

This adapter makes an Omarchy workstation a first-class, optional Agent OS host without making Omarchy a dependency of Agent OS or a source of authority.

## Purpose

The target operator experience is a local Agent OS console on the workstation:

```text
human
  ↓
Omarchy host
  ↓
Agent OS task / policy / routing / evidence
  ↓
LLM harness
  ↓
remote or local inference provider
  ↓
bounded tools and targets
  ↓
verification + evidence
```

The host provides the local shell, browser/editor surface, repository checkout, local task state, harness availability, interruption, and inspection. Agent OS continues to own routing, authorization boundaries, skill resolution, verification requirements, and evidence semantics.

## Host / target separation

A local credential or reachable remote system does not imply authority to mutate it. Production, deployment, privileged operating-system actions, protected-branch mutation, and other sensitive targets remain separately authorized.

The adapter must never:

- enable blanket passwordless sudo;
- copy secrets into the Agent OS repository;
- make a model or harness authoritative;
- infer production permission from connectivity;
- silently broaden a task because a tool is installed;
- make Omarchy required for Agent OS.

## Local commands

After this adapter is pulled to the host:

```bash
./agent-os doctor
```

reports host, GitHub, workspace, harness, provider, and local-state readiness without printing secrets.

```bash
./agent-os run "inspect ailhat"
```

runs the current governed Agent OS task pipeline.

```bash
./agent-os serve
```

starts the local Task API on `127.0.0.1:8787` only.

## LLM-adjacent model

Host v1 separates **harness** from **inference provider**.

A harness may be Codex, Claude Code, OpenCode, or another approved executor. Its provider may be a remote API-backed model or a local inference service. The same Agent OS task and policy semantics must survive provider changes.

Magnitude is registered here only as an **experimental local inference provider candidate**. It is optional, not automatically installed, and never grants tool or target authority. On constrained hardware, local-model use should be based on measured host capability rather than assumed adequacy.

## Pilot acceptance

Host Pilot 01 is successful only when the workstation can:

1. identify itself and the Agent OS checkout;
2. authenticate to GitHub through host-level credentials;
3. keep local task/runtime state outside version control;
4. expose at least one usable LLM harness path;
5. preserve explicit human authorization boundaries;
6. support interruption, inspection, verification, and evidence;
7. remain portable to another host without rewriting core Agent OS policy.
