# Milchik backlog — weighting rationale

`backlog.yaml` is the machine-readable backlog; this file explains *how attention
is allocated* so the ranking is auditable and neither human nor agent work is
starved by the other. `runtime/backlog.py` is the code; this is the prose it
points at.

## The model

Three things decide a work item's place in line. They are kept separate on
purpose so none can silently masquerade as another.

| Axis | What it answers | Where it lives |
|---|---|---|
| **Lane** | what *kind* of work it is | `backlog.py` `lane()` + `LANE_BONUS` |
| **Priority** | how urgent within its lane | `priority.level` p0–p3 |
| **Authorization** | whether it may actually run | `backlog.py` `authority_present()` |

**Lane gates.** `ecosystem` (backend work on the operating layer itself) carries
+30; `directive` (product work) carries 0. The bonus is smaller than a full
priority-band gap (15 per level, 45 from p3 to p0), so it sequences classes of
work — ecosystem drains before the team turns to product directives — without
ever letting a p3 outrank a p0 in the same lane. Lane defaults to `ecosystem`
when absent.

**Priority dominates within a lane.** p0 = 60, p1 = 45, p2 = 30, p3 = 15.
Confidence refines within a band: +confidence×30 (max +30).

## Score

```
attention_score = PRIORITY_BASE[level] + confidence×30 + LANE_BONUS[lane]   # 0..120
```

So an ecosystem p1 (45 + confidence×30 + 30) outranks any directive at the same
priority, but a p0 directive still breaks through ahead of ecosystem p2/p3
rather than starving behind cleanup.

## Origin: confidence default and authorization, never a score bump

Origin (human vs agent vs routine vs ailhat) affects exactly two things:

1. **Confidence default.** A human-triggered item defaults to confidence 1.0 —
   direct human intent is already a high-confidence relevance signal. An
   agent/routine/ailhat item defaults to 0.5 — its relevance is presumed
   unproven until corroborated. An explicit confidence always overrides the
   default, so a well-evidenced agent proposal and a casual human request
   compete on their merits, not their defaults.

2. **Authorization path.** Human work carries known intent, so it is
   pre-authorized to queue. Agent/routine/ailhat work ranks for attention but
   still requires explicit approval before enqueue. `authority_present()` is
   true only for `source: human`.

`ailhat` is intelligence, not authority: its directives enter as ordinary
entries with `source: ailhat`, `lane: directive`, and a `source_ref` back to the
live ailhat record, and are eligible only once explicitly `approved`.

## Invariants the tests pin

- Priority dominates origin; origin never changes the score directly.
- Lane gates without letting a p3 beat a p0 in the same lane.
- Human default confidence (1.0) > other default (0.5), but explicit confidence
  always wins over both.
- Ranking is stable and deterministic.
- `authority_present` is true only for `source: human`.

## Lifecycle

`proposed -> approved -> queued (fleet) -> done`. `done` is terminal and carries
evidence; it stays in the file as history rather than being deleted. Milchik
ranks and surfaces the top item(s); approval and enqueue remain the gates they
already are. A backlog entry never grants execution authority by itself.
