# Task Envelopes

Governed units of work under `skills/owned/task-envelope/SKILL.md`, one per routine in `routines/`.

## Why three, not one

Each envelope defines **what governed work is permitted**; the routine that references it defines **how that permitted work may repeat safely**. The two compose — the routine never replaces the envelope.

Three separate envelopes, because the three routines differ in the fields an envelope exists to pin down: executing agent, target repository and paths, authority class, permitted actions, and success criteria. A single shared envelope would have to grant the union of all three — publish authority over `ashwood-info` *and* write access to the ALVIRA repository — to every routine that referenced it. That is precisely the broadening the skill prohibits: *"Do not broaden the target because adjacent work appears useful."*

The envelopes share an objective. They do not share a blast radius, so they do not share an envelope.

## Index

| Envelope | Routine | Executing agent | Authority |
|---|---|---|---|
| `env-ashwood-build-journal.md` | `ashwood-build-journal` | Marlo | `scoped-publish` |
| `env-ashwood-dispatch.md` | `ashwood-dispatch` | Marlo | `scoped-publish` |
| `env-discoverability-audit.md` | `discoverability-audit` | Eugene | `AUTONOMOUS + AUDIT` |
