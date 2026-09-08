# Milchik supervisory continuity

**Status:** approved direction
**Owner:** Milchik / AgentOS runtime
**Priority:** P0 ecosystem reliability
**Recorded:** 2026-09-08

## Problem observed

A real approved ailhat work item was parked after Eugene hit a temporary harness/provider availability limit. Milchik reported that the same task would be reconsidered at a specific future timestamp, but that timestamp passed without a re-evaluation, status update, escalation, or response to TK's Telegram status request.

This is a supervisory failure. A future-time promise in a Telegram message is not a durable retry mechanism.

Milchik must behave as an operational supervisor that preserves continuity of approved work, not merely as a notification formatter.

## Governing invariant

> Milchik may promise a future action only if a durable mechanism exists that will cause that action to be reconsidered.

Silence is never a valid state for owned work after a promised next-action time has elapsed.

## Target loop

```text
work approved
    -> Milchik owns continuity
    -> assign worker/harness
        -> completed -> verify/report
        -> blocked -> park with durable retry_at
                     -> wake/re-evaluate
                     -> resume | reassign | still blocked | needs TK | failed
        -> needs human -> escalate to TK
```

Milchik owns continuity of work, not the executor's implementation domain and not new execution authority.

## Required runtime behavior

### 1. Durable wake event for every parked task

Any task entering `PARKED` / temporary-capacity-blocked state with a future retry must persist a machine-readable wake condition or scheduled event. `retry_at` may not exist only inside display text.

Required persisted data should include at least:

- task/work identifier;
- current owner/executor;
- blocker class and evidence;
- `retry_at` or equivalent wake condition;
- authority scope already granted;
- last supervisory action timestamp;
- next-action owner.

A restart, provider outage, or Telegram disconnect must not erase the wake obligation.

### 2. Wake-loop re-evaluation

When the wake condition is reached, Milchik must read current recorded state and produce one explicit outcome:

- `RESUMED`
- `REASSIGNED`
- `STILL_BLOCKED` with a new durable next check
- `NEEDS_TK`
- `FAILED`

No silent no-op is allowed.

A retry does not create new authority. The same approved task may resume only while the requested action and authority scope remain materially unchanged. Scope changes return through the normal approval path.

### 3. Stale-work watchdog

Milchik must periodically inspect non-terminal governed work, including at minimum:

- `ACTIVE`
- `PARKED`
- `BLOCKED`
- `WAITING_APPROVAL`

For each item, compare recorded state against any promised or required next-action time.

If `now > retry_at` or another promised checkpoint elapsed without the required transition, emit a supervisory incident such as:

`OVERDUE — promised reconsideration missed`

The incident must then trigger immediate re-evaluation, not just an alert.

### 4. Heartbeat

Add a durable supervisory heartbeat at an implementation-appropriate interval. Initial target: at least every few hours while non-terminal work exists, with event-driven wakes taking precedence over the heartbeat.

The heartbeat exists to recover missed scheduler events and stale state, not to create noisy periodic Telegram messages.

### 5. Two-way Telegram status queries

TK's monitor/private-channel messages such as:

- `what's happening?`
- `status`
- `what is blocked?`
- `what's next?`

must resolve to live recorded state rather than being treated as passive chat.

The response should be short and human-readable by default, for example:

```text
ailhat — still blocked

Eugene's provider capacity has not recovered.
The scheduled retry was missed — supervisory error.
The work is re-queued and the next check is 5:00 PM.

Action needed from you: none.
```

Underlying machine detail remains available on request.

### 6. Human-language reporting

Default Telegram output should translate internal state instead of dumping raw enums and implementation metadata.

Prefer:

- `private beta, not ready for launch`
- `65% readiness, medium confidence`
- `needs attention`

rather than exposing raw values such as:

- `PRIVATE_BETA_PRE_LAUNCH`
- `65/MEDIUM`
- `NEEDS_ATTENTION`

Do not show timestamps with seconds unless the precision is operationally relevant.

The concise blocker/status brief must answer:

1. What is blocked?
2. Why?
3. What happens next?
4. What does TK need to do?

If TK needs to do nothing, say so explicitly.

## Ownership boundary

Milchik owns **continuity of approved work**:

- noticing stalled or overdue work;
- preserving the obligation to revisit it;
- waking/re-evaluating it;
- reassigning within existing authority where policy permits;
- escalating when authority or human judgment is required;
- reporting the resulting state clearly.

Milchik does **not** gain product truth, technical feasibility, verification, deployment, or authorization ownership from this loop. Existing AgentOS role and authority boundaries remain intact.

## Acceptance criteria

The change is not complete until all of the following are demonstrated with recorded evidence:

1. A parked task with a future retry creates durable machine-readable wake state.
2. Advancing past `retry_at` causes an automatic re-evaluation without TK prompting it.
3. The re-evaluation records one of the defined explicit outcomes.
4. A deliberately missed/failed wake is caught by the stale-work watchdog and marked overdue.
5. Restarting the AgentOS process does not lose the retry obligation.
6. A provider/harness remaining unavailable produces `STILL_BLOCKED` plus another durable check rather than silence.
7. A provider/harness becoming available causes the same approved work to resume or be reassigned without unnecessary re-approval, provided scope is unchanged.
8. A material scope/authority change routes back to approval instead of being silently resumed.
9. A Telegram `status` / `what's happening?` query returns current recorded state and the next action.
10. Default Telegram output is human-readable and hides unnecessary raw enums/seconds-level timestamps.
11. No heartbeat/status mechanism spams the channel when nothing materially changed.
12. Tests cover the missed-retry failure observed on 2026-09-08.

## Implementation order

1. Durable parked-task wake state.
2. Wake-loop dispatcher/re-evaluation.
3. Stale-work watchdog + heartbeat recovery.
4. Two-way Telegram status-query handler.
5. Human-language Telegram formatter.
6. Failure/restart tests and end-to-end proof using the current ailhat work item or an equivalent controlled fixture.

Do not spend time on additional Milchik personality, visual polish, or notification expansion until this continuity loop is proven.
