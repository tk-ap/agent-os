---
name: agent-identity-design
description: Create or review persistent Agent OS identities with explicit ownership, decision rules, boundaries, handoffs, context requirements, continuity behavior, and first-task validation. Use when a durable new agent role is genuinely justified or an existing identity needs repair.
---

# Agent Identity Design

Design durable Agent OS identities without turning every recurring need or reusable capability into another agent.

This capability is for creating or reviewing persistent workforce identities. It is not permission to dynamically proliferate agents at runtime.

## Agent vs. Skill Test

Before proposing a new persistent agent, ask whether the need can be satisfied by an existing agent plus a reusable skill.

Prefer a **skill** when:

- the capability can be reused by more than one existing agent;
- the task does not require isolated context or materially different permissions;
- the work can remain under an existing domain owner's judgment;
- a different model/runtime is optional rather than essential;
- adding another persistent identity would mainly duplicate ownership.

Consider a **new agent** only when one or more of these are materially true:

- a distinct decision domain needs a durable accountable owner;
- context must be isolated to avoid contamination or excessive loading;
- permissions or trust boundaries must differ materially;
- independent inspection/adversarial judgment must remain organizationally separate from the producer;
- execution characteristics require a materially different model, tool boundary, or environment;
- repeated handoffs demonstrate a stable ownership boundary that existing agents cannot absorb cleanly.

If two proposed agents would share substantially the same state, authority, decision domain, and success criteria, prefer one agent plus skills unless there is a documented separation reason.

## Creation Gate

A new persistent Agent OS identity requires explicit human approval before registry activation.

Router may identify a gap. Steward may identify an accountability gap. Domain agents may recommend specialization. None may silently create and activate a durable agent identity.

## Required Identity Contract

Every persistent identity should define:

- name and role;
- primary function;
- decision domain and explicit ownership;
- north-star/governing questions;
- what evidence/context it requires;
- domain expertise expectations;
- decision framework;
- boundaries and actions it must not take;
- relationship to authorization policy;
- named upstream/downstream handoffs;
- skills it owns or commonly resolves;
- memory/context continuity requirements and provenance rules;
- disagreement/escalation behavior;
- communication style only where it improves operational consistency;
- error-correction/identity-review triggers;
- a first-task or forward test that demonstrates the identity is distinct and useful;
- retirement/merge criteria if the role becomes redundant.

## Identity Review

Review an existing identity when:

- outputs repeatedly overlap another agent;
- Router cannot distinguish ownership cleanly;
- the agent requires too many unrelated skills to function;
- handoffs repeatedly bounce between the same two identities;
- the agent routinely exceeds its stated authority or boundaries;
- memory/context requirements become unclear or excessive;
- the role exists mainly because of a tool/vendor rather than a durable decision domain;
- verification shows the identity adds coordination cost without distinct value.

Possible outcomes are **keep, narrow, merge, convert capability to skill, split with explicit justification, or retire**.

## Producer / Inspector Separation

Do not create a second agent merely to imitate self-review. Use an existing independent owner when the review domain already exists.

Where independent inspection is materially required, Router should pair the producer with the smallest appropriate inspector, for example:

- implementation producer → W Dog verification or Rook adversarial review when applicable;
- experience producer → Scout/user evidence or W Dog verification when applicable;
- execution plan producer → Rook permission/failure review or Ledger economic review when applicable.

Every review loop must have an acceptance condition, maximum cycle count, and escalation owner.

## Output

Return:

- agent-vs-skill decision;
- justification for any persistent identity;
- proposed or revised identity contract;
- overlap/conflict findings;
- required registry and handoff changes;
- forward-test criteria;
- human approval state;
- next permitted action.

## Source Note

This owned capability was informed in part by user-supplied `agent-persona-builder` and `agent-org-planner` reference material. Those packages remain non-executable references until provenance, license, referenced-file layout, and external claims are independently resolved. Agent OS ownership, authorization, routing, and supply-chain policy take precedence.
