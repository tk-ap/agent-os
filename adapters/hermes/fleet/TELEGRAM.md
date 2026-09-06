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

## Monitor channel

`monitor` pairs one Telegram group for read-only cards — fleet lifecycle events
with no buttons and no acceptance path.

```bash
python /home/tk/Work/agent-os/adapters/hermes/fleet_cli.py telegram monitor
```

**Adding the bot to the group is enough.** The membership change fires a
`my_chat_member` update, which Telegram delivers even under privacy mode, and
the tick captures the chat id from it.

Two fallbacks, in order of reliability: forward one message from the group into
your private chat (carries the origin chat id, and the only path that works for
channels), or send a message directly in the group — which works only if the bot
can see it. `getMe` reports `can_read_all_group_messages: false`, so under
default privacy mode a non-admin bot cannot. Adding it as an administrator lifts
that, and also lets `/status` work in the group.

The fleet tick captures the designation; the `monitor` command prints the
instructions and waits for it. **Do not pause the scheduler while pairing** —
the tick is what does the capturing. There is deliberately no second poller:
confirming a `getUpdates` offset makes Telegram forget every earlier update, so
two pollers cannot coexist and the pairing message would be lost to whichever
called first.

Only the paired founder can designate a monitor channel, and only one monitor
chat is supported — `monitor_chat_id` is a single value. A second group cannot
receive cards without a schema change.

Until a monitor channel is paired, monitor cards stay `pending` and are never
delivered to the private chat instead.

The split is deliberate: **group for visibility, private chat for approvals.**
Buttons never appear in the group, so no group member can approve anything.

The rule the split follows: **the private chat is only for work that cannot
proceed without TK.** A review card, a failed routing, an escalation after the
revision loop gave up — those stop until he acts. Commit digests, drift signals,
fleet lifecycle and contribution reports all go to the group, because the work
continues whether or not he reads them.

## Giving a directive

Prefix it: `> ship the sitemap fix` or `/do ship the sitemap fix`, in the private
chat.

Milchik records it as a numbered directive, echoes back what he wrote, and
enqueues a routing task attributed to Router. Router proposes one owning agent,
a priority, and a lane, with reasoning, and returns it as a review card to
accept. Nothing is assigned or started by the act of speaking.

**Capture is not execution.** Writing a row and reporting the row is not obeying
an instruction, which is why the standing rule still holds: free-form Telegram
text is not an agent prompt and grants no authority. Choosing an owner is
judgement and runs in a worker with a model, never in the scheduler tick.

An unprefixed message gets a one-line reply saying it was not recorded. Silently
ignoring it would look identical to a directive that was captured and never ran.

## Asking for status

Send `/status` in the private chat or the monitor group. Milchik replies with a
per-project view: open PRs split ready/draft, commits in the last day,
uncommitted work, overlapping repositories, what awaits your decision, what is
blocked, your open directives, and what is next for attention.

It answers only the paired founder, and only in the paired chats. It reads state
and reports it: it starts nothing, decides nothing, and grants nothing.

`/status` and a prefixed directive are the only text this bot acts on.

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
reporting, and drift/memory signal batching.

Live transport is verified as of 2026-09-06: a message delivered to the private
chat, a `/status` sent from Telegram and consumed by the tick (offset advanced
735430119 to 735430120), the monitor group captured from a `my_chat_member`
event, and a message delivered to that group.

**On-device buttons remain unverified.** No card carrying Accept / Needs changes
/ Pause has been delivered or pressed, because no fleet task has ever reached
review — the acceptance path is covered by tests against mocks only.

API behavior was checked against Telegram's official
[Bot API](https://core.telegram.org/bots/api) and
[bot features](https://core.telegram.org/bots/features) documentation.
