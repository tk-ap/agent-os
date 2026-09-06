# Milchik — the Agent OS review inbox and fleet monitor

Milchik uses a dedicated Telegram bot across two chats: a **monitor channel**
(group) that carries read-only fleet awareness, and a **private chat** with TK
that carries approvals, drift, commits, and memory signals. The existing Hermes
no-model cron tick drives delivery and button handling. No extra daemon or model
is involved. The gateway must be running; delivery and button processing may
take about one minute.

## Private setup

Create the bot through Telegram's BotFather, display name **Milchik**. Its
username must be available; the display name does not determine its username.
Enter the issued token in your own terminal, never in a conversation or command argument:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram setup
```

The prompt hides the token. Open the one-time pairing link it prints in your own
Telegram account and press Start. Only that private chat/user can receive reports
and act on cards. The pairing challenge expires after three minutes.

## Monitor channel (second chat)

The same bot is added to a Telegram group that becomes the read-only fleet
monitor. Pair it after setup:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram monitor
```

Add the bot to a group and send any message; the command captures that group's
`chat_id` as `monitor_chat_id` without touching the token or the private chat.
Monitor cards carry no buttons and no acceptance path — awareness only, never a
decision surface.

The token and paired IDs are stored in `~/.hermes/agent-os-telegram.json` with mode
0600, outside the repository. This dedicated bot must not also be configured as a
Hermes chat-gateway bot or attached to another polling consumer/webhook. The setup
refuses to replace an existing configuration and refuses an existing webhook.

## What arrives

**Private chat (TK):**

- One card for each fleet task entering review, blocked, or revoked state.
- Task/product, worker summary, acceptance criteria, worker-reported checks,
  unverified deployment/independent-acceptance status, and local evidence location.
- **Accept result**: records human acceptance of the exact local Git snapshot and
  closes the task. It does not merge, publish, deploy, purchase, or extend authority.
- **Needs changes**: records the decision and revokes further task execution.
  A revised task needs a fresh bounded work order after the requested changes are clarified.
- **Pause**: revokes execution. It does not discard files or evidence.
- **Signals**: batched drift/memory observations (see below), positive and negative.

**Monitor channel (group):**

- One line per fleet lifecycle event — queued, claim, start, result, phase — for
  every task, read-only, no buttons.

Acceptance binds a random single-use card ID, paired user ID, chat ID, Telegram
message ID, task status, work-order digest, and current Git/file fingerprint.
Cards expire after 24 hours. Changed files, revoked tasks, wrong actors, wrong
messages, and replays cannot approve anything. Acceptance uses a Hermes review
claim and completes only that claim. Unverifiable/oversized/non-Git workspaces
receive an informational card without the acceptance button.

Free-form Telegram messages are not agent prompts and cannot grant authority.
This version handles fleet result acceptance, not the legacy Task API's HUMAN_GATE
or approval/execution of deployments. Those require separate action-specific bindings.

## Drift and memory signals

Ingest a drift or memory observation (scope + polarity + text); it is delivered to
the private chat on the next tick. Signals never grant or revoke authority:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram record-signal \
  --scope skill-gap --polarity negative --text 'marlo lacks the X skill for this task'
```

- **positive** — a new/changed lesson or an under-utilized skill discovered.
- **negative** — drift, a correction, or a removal; or a locked-context violation.

## Asking for status

Send `/status` in the private chat or the monitor group. Mr. Milchik replies with
what is being worked on, what is waiting on you, what is blocked, and the most
recent recorded changes.

It answers only the paired founder (`user_id`), and only in the paired private
chat or the paired monitor group. It reads state and reports it: it starts
nothing, decides nothing, and grants nothing. **`/status` is the only text this
bot acts on.** Every other message is ignored — free-form Telegram text is not
an agent prompt and cannot grant authority.

Status is a pull. Cards are a push. Neither replaces the other.

## Monitor channel

`monitor` pairs a Telegram group for read-only cards — fleet lifecycle events
with no buttons and no acceptance path.

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram monitor
```

Add the bot to the group, then send any message there within three minutes. Only
a group or supergroup is accepted, and it may not be the paired private chat.
Until a monitor channel is paired, monitor cards stay `pending` and are never
delivered to the private chat instead.

**Pause the scheduler while pairing.** The fleet tick polls `getUpdates` every
minute, and confirming an offset makes Telegram forget every earlier update —
including the group message the pairing is waiting for. Pause first, pair, then
resume:

```bash
hermes cron pause <job-id>     # "Agent OS fleet dispatch"
# …pair the group…
hermes cron resume <job-id>
```

The split is deliberate: **group for visibility, private chat for approvals.**
Buttons never appear in the group, so no group member can approve anything.

## Optional change summaries

Default is review alerts only. To also send a digest every five new local commits
per product, choose this during initial setup:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram setup --basis commit --every 5
```

ASHWOOD and ALVIRA are baselined at setup; old history does not generate a flood.
Branch switches/history rewrites rebaseline. Commit counts are explicitly not live
deployment counts. The number is configurable from 1 to 100.

For deployment-based summaries use `--basis deployment --every 5`. This needs a
post-deployment producer to record stable deployment receipts; it does not scrape
pages or infer deployment from a Git commit:

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram record-change \
  --product ashwood --kind deployment --revision DEPLOYMENT_ID \
  --summary 'Producer receipt: production deployment URL and verification evidence reference'
```

This ingestion command is ready, but no live deployment producer has been connected.
The digest labels records as producer evidence, not an independent visual verification.
The same deployment ID is counted once per product. Partial batches stay queued.

## Delivery and stop controls

At most five messages are sent per minute tick. Cards are deduplicated. An ambiguous
send is recorded as `uncertain` and never automatically retried, preventing duplicate
approval prompts after a timeout. Use `telegram preview` to inspect messages and
delivery/decision state locally. This command never sends a message.

Set `enabled` to false in the private configuration to stop this inbox. Pausing the
existing Hermes fleet cron job also stops polling but affects fleet dispatch too.
No credentials are written to logs or repository files. No Telegram connection is
made while configuration is missing or disabled.

## Verification

Tests cover acceptance, identity/chat/message checks, replay, expiry, revocation,
modified files, change requests, deduplication, uncertain delivery, per-product
thresholds, absence of network access when unconfigured, two-chat routing (monitor
to group, private to TK, monitor held when unpaired), fleet-event once-only
reporting, and drift/memory signal batching. The actual Telegram transport and
on-device buttons remain unverified until pairing and a live test are completed.

API behavior was checked against Telegram's official
[Bot API](https://core.telegram.org/bots/api) and
[bot features](https://core.telegram.org/bots/features) documentation.
