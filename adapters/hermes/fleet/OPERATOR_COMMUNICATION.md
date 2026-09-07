# Operator communication contract

Status: required behavior for human-facing workforce channels
First implementation surface: Milchik on Telegram

## Purpose

Agent OS must not require its human operator to read engineering logs in order to understand, supervise, or safely approve work.

Human-facing channels are an operator interface, not a raw telemetry pipe. They must translate internal state into plain language first while preserving access to the underlying evidence and technical detail on request.

> Never require the operator to understand implementation terminology to make a safe decision. Never remove the operator's ability to inspect the implementation details.

This is a system-level communication contract. Telegram is the first adapter implementing it; Telegram is not a required Agent OS dependency. Slack, email, a native client, or another channel should be able to implement the same contract later.

## Default hierarchy

Every action-oriented operator message should use progressive disclosure in this order:

1. **Human summary — What happened?**
2. **Consequence — Why does it matter?**
3. **Decision — Does the operator need to do anything?**
4. **Safety — What changes if the operator approves or declines?**
5. **Explain — Teach the relevant concept in plain language when requested.**
6. **Technical details — IDs, paths, policy rules, logs, raw evidence, harness/runtime terminology.**

Do not lead with task IDs, YAML paths, JSON fields, queue/tick language, internal phases, or raw inspector output unless the operator has selected a technical/raw view.

## Message classes

The first line must make urgency legible without reading the whole message.

- **FYI** — work can continue without operator action.
- **Decision required** — work is parked until the operator decides.
- **Problem** — something failed, drifted, or needs intervention.

A message must not imply that action is required when it is merely informational.

## Default review-card shape

A review card should answer the following in as few words as practical:

### What happened
Name the agent or system and the meaningful outcome in human language.

### Why it matters
Explain the consequence, especially whether anything is live, published, deployed, deleted, paid for, externally visible, or otherwise irreversible.

### Safety
State whether an independent check passed, failed, or was unavailable. Do not paste the raw inspection transcript into the default card.

### Decision
Show only the few controls relevant to the current state. The default review surface should favor:

- **Approve**
- **Needs work**
- **Pause**
- **Explain**

More specific feedback choices may be exposed after **Needs work**, rather than forcing the operator to scan a long menu on every review.

Where authorization is involved, the action label must name its scope, for example **Approve once** or **Approve production deploy**, rather than a vague **Yes**.

## Explanations and learning

The operator is not assumed to be a software engineer. That does not mean technical concepts should be hidden.

The default experience should be plain English. **Explain** should reveal the relevant concept and, when useful, pair the plain-language description with the technical term.

Example:

> The code change exists, but it is not live. Technical term: committed but not deployed.

Explanation is educational context, not permission. Opening an explanation must not start, resume, approve, publish, deploy, or otherwise mutate work.

## Explanation levels

Human-facing adapters should support these presentation levels, whether as an explicit setting or equivalent rendering policy:

- **Simple** — human summary, consequence, decision, and safety only.
- **Learning** — Simple plus short concept explanations and technical vocabulary when useful. This is the preferred default for TK.
- **Technical** — includes implementation terminology and evidence references.
- **Raw** — log/state-oriented output for debugging.

Changing the explanation level changes presentation only. It must never widen execution authority.

## Vocabulary rules

Prefer human language in the default view.

| Internal wording | Default operator wording |
| --- | --- |
| `VERDICT: PASS` | Review passed |
| routing proposal | Work assignment |
| owning agent | Agent responsible |
| enqueued | Queued to start |
| next tick | Next time the workforce runs |
| inspection/review loop | Review process |
| unverified task data | A previous record says this happened, but the system has not confirmed it yet |
| committed but not deployed | The code change exists, but it is not live |

Internal terms remain valid in Technical and Raw views.

## Example: routing review

Preferred default:

> **Decision required — Eugene is ready to continue**
>
> The work assignment passed review. W Dog checked it independently and found no problems.
>
> **What this means:** Eugene has been chosen to own this work. No ALVIRA changes have started, and nothing has been published or deployed.
>
> **Safe to approve:** Yes.
>
> **Approve · Needs work · Pause · Explain**

Technical details may then expose values such as task ID, owner registry source, inspection evidence, work ID, and raw verdict.

## Example: approval confirmation

Avoid confirmations such as:

> Accepted. Directed work enqueued for eugene (t_1120ce54) — it runs on the next tick under the same inspection and review loop.

Preferred default:

> **Approved**
>
> Eugene will take this work next. It will go through the same review process before anything consequential happens.
>
> Nothing has been published or deployed yet.
>
> **View progress · Explain what happens next**

## Telegram's role

Telegram is a thin human-interaction adapter for the workforce, not core infrastructure and not a standalone ecosystem product.

It may surface:

- Agent OS review decisions, exceptions, status, and completion receipts;
- LEDGATo authorization requests and post-action verification receipts;
- ailhat opportunity, risk, drift, and work signals when those require or benefit from operator attention.

Core orchestration, authorization, policy, evidence, and state remain in their owning systems. If Telegram is unavailable, those systems must remain valid; only the interaction surface is unavailable.

Canonical authorization flow when LEDGATo is involved:

`Agent -> Agent OS -> LEDGATo boundary -> human-channel approval -> scoped temporary authority -> execution -> LEDGATo verification -> human-channel receipt`

## Implementation requirements for Milchik

The Telegram renderer should converge on this contract rather than reproducing internal checkpoint summaries verbatim.

Required behavior:

1. Render a human summary before technical evidence.
2. Collapse raw W Dog evidence behind Explain/Technical details in the default view.
3. Replace long always-visible feedback menus with a smaller primary decision set and reveal detailed feedback after Needs work where possible.
4. Rewrite post-button confirmation text in human language.
5. Clearly state whether anything became externally visible, published, deployed, deleted, or charged.
6. Preserve raw evidence and internal identifiers for Technical/Raw inspection.
7. Keep explanations read-only and non-authorizing.
8. Keep channel presentation separate from execution authority.

## Acceptance criteria

A human-facing review flow satisfies this contract when:

- a non-engineer can tell what happened and whether action is required without decoding repository/runtime terminology;
- the operator can tell what approving changes and what it does not change;
- technical evidence remains reachable without being the default reading burden;
- no explanation/view control can mutate task state;
- the same underlying decision/evidence model can be rendered through a channel other than Telegram;
- tests cover the human-default message, technical/raw disclosure, and approval confirmation separately.
