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

Add the bot to the group, then **forward one message from that group into your
private chat with the bot**. Sending a message directly in the group also works
*if* the bot can see it — but `getMe` reports
`can_read_all_group_messages: false`, so under default privacy mode it usually
cannot. Forwarding carries the origin chat id regardless, and is the only path
that also works for channels.

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
