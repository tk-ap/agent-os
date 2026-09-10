# Harness Routing Persistence Contract

## Separation of concerns

- Task lifecycle state is durable and owned by persistence.
- Agent ownership is durable workforce identity.
- Harness selection is an execution-time routing decision.
- A harness outage or replacement must not mutate or erase task intent/state.

## Required routing record

Each routing decision must be persistable with:
- task id
- agent
- harness
- intelligence tier
- reason
- fallback candidates
- timestamp

## Required attempt record

Each execution attempt must be persistable with:
- task id
- attempt number
- agent
- harness
- intelligence tier
- outcome, drawn from the classes below
- timestamp
- evidence/reference payload when available

## Outcome classes are not interchangeable

An outcome is not a free-form label. Rotation to another harness is justified by
some failures and by no others, and a model that does not distinguish them will
burn every eligible harness on a fault that none of them can fix.

- `executed` — the harness completed. Completion is not acceptance.
- `capacity` — the provider refused for usage/rate/quota reasons. This is the
  only class that justifies rotating to another harness, because it is the only
  one where a different provider would behave differently.
- `permission`, `authentication` — the environment refused. Rotating repeats the
  failure on every harness in turn and consumes the attempt budget for nothing.
  Stop for inspection.
- `failed`, `timeout` — unknown fault. Stop for inspection; an unexplained
  failure is not evidence that a different harness would succeed.

## An outcome must be classified from evidence

The outcome is derived from what the harness produced, never from a status label
it reports about itself and never from an exit code alone. A harness can refuse
and still exit zero: an unauthenticated or untrusted-workspace refusal has been
observed reporting success while changing nothing. A run that could not act must
not be recorded as one that acted.

## Capacity-blocked time does not consume authority

A task parked because every eligible harness was exhausted consumed none of the
authority it was granted. That time is credited back, or the mandate is
otherwise held, so that an operator-approved task cannot expire while waiting for
a provider it was never able to reach. Without this the continuation guarantee
below is void in the exact case it exists for: a cooldown may be as long as the
mandate, so an approved task that never ran can be destroyed by the clock. The
credit is bounded, so repeated parking cannot turn a bounded grant into an
open-ended one.

## A fallback must be able to do the work

A fallback list is a claim of substitutability, not a list of names. A harness
belongs in it only when it can actually take the work:

- its declared capabilities cover what the task class requires; and
- it draws on capacity independent of the harness it would replace. Two entries
  backed by the same exhausted provider are one entry.

A single-harness task is legitimate; recording it honestly as having no fallback
is better than listing a harness that would refuse.

## Verifier independence

Agent-level verifier independence remains mandatory. Harness-level independence is additive. A harness that materially authored, remediated, or participated in the work is ineligible to independently verify it when another eligible harness exists. If independence cannot be satisfied, verification remains blocked.

## Continuation guarantee

A failed or unavailable harness must not complete, cancel, or forget a durable task. The task remains in its lifecycle state until a later eligible execution attempt changes that state through normal evidence-backed workflow transitions.
