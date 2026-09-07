# Milchik — the Agent OS review inbox and fleet monitor

Milchik uses a dedicated Telegram bot across two chats: a **monitor channel**
(group) that carries read-only fleet awareness, and a **private chat** with TK
that carries approvals, drift, commits, and memory signals.

Two processes drive it, and **no model runs in either**. The existing Hermes
no-model cron tick collects work and delivers cards every minute. A listener
(`milchik-listener.service`) holds a long poll open so a message you send is
answered in seconds rather than on the next tick.

Only one of them polls Telegram at a time. The listener writes a heartbeat; while
that is fresh the tick skips `getUpdates` entirely and does collection and
delivery only. If the listener stops, the heartbeat goes stale after 90 seconds
and the tick takes polling back on its own — you are back to up-to-a-minute
latency, not to a broken inbox. Confirming a `getUpdates` offset makes Telegram
forget every earlier update, so two live pollers would steal each other's
messages.

The gateway must be running for the cron tick to fire at all.

## Process layer (three processes, two clocks, one poller)

The workflow's process wiring is saved in the repo at
`adapters/hermes/fleet/systemd/`, so the inbox can be rebuilt on a new machine
from the repo alone:

1. **Primary clock + poller — the Hermes cron tick** (`Agent OS fleet dispatch`).
   Installed by `adapters/hermes/fleet/install.py`. Runs inside the gateway
   process every minute; dispatches workers and, while the listener heartbeat is
   stale, polls `getUpdates` itself. When the gateway is down, this clock stops.
2. **Listener** — `milchik-listener.service`. Holds the Telegram long poll so
   sent messages are answered in seconds. Writes the heartbeat that makes the
   tick skip polling. Only one of (1) and (2) polls at a time, enforced by the
   90-second heartbeat window.
3. **Fallback clock** — `agent-os-fleet-fallback.timer` +
   `agent-os-fleet-fallback.service`, driving
   `adapters/hermes/fleet/fallback_tick.py`. A systemd user timer fires every
   minute but ticks ONLY when the gateway's own liveness row in
   `~/.hermes/state.db` is stale (~2.5 missed beats), so the two clocks never
   double-fire. When Hermes is healthy it is a no-op; when the gateway dies it
   keeps dispatch and the review inbox moving within one heartbeat window.

Install the units on a new machine:

```bash
install -Dm644 adapters/hermes/fleet/systemd/*.service \
  adapters/hermes/fleet/systemd/*.timer -t ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now milchik-listener.service
systemctl --user enable --now agent-os-fleet-fallback.timer
```

The unit files carry `Documentation=` back to this file and hardcode
`/home/tk/Work/agent-os` paths; adjust for a different home or clone location.

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

## Starting the next piece of backlog work

Send `/next` in the private chat. Milchik takes the highest-ranked backlog item
he is allowed to start, turns it into a directive, and routes it — replying with
what he picked and why.

He will only start an item that is `source: human` or already `approved`
(IDENTITY.md §09). A high rank on an unapproved agent proposal is attention, not
permission, so `/next` skips it and says the top items are waiting on you rather
than starting one.

## Approving, and publishing

A review card offers **Approve & save** and, when the work item permits it,
**Approve & publish** as a separate button on its own row.

- **Approve & save** commits the declared paths. Nothing leaves the machine.
- **Approve & publish** commits and pushes the declared branch, which is what
  makes the change reachable. The card names the URL it makes live.

The consequence belongs to the press, not to the work item. A card that can
publish still offers save, and pressing save publishes nothing. A work item can
narrow what is offered; it can never widen what was pressed.

Publishing refuses if the workspace is on a branch other than the one declared —
pushing an unreviewed branch would put something live nobody looked at — and it
never forces. All refusals happen before anything is committed, so a refused
publish leaves no commit behind.

## Publishing a batch

Send `/publish` in the private chat. Milchik lists every project with commits
that are not yet pushed — branch, how many commits and files, the first few
subjects, and the URL each one makes live — with a button per project.

This is how deployment spend stays deliberate. Every push triggers a build, so
publishing one approval at a time costs a deployment per decision. `Approve &
save` commits without pushing, approvals accumulate on the branch, and one
`/publish` press sends them together as a single build.

It pushes the branch it showed you. If the branch moved between the card and the
press, it refuses and publishes nothing. It never forces.

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

Set `enabled` to false in the private configuration to stop this inbox; both the
tick and the listener check it. Pausing the Hermes fleet cron job also stops the
tick but affects fleet dispatch too. The listener alone is
`systemctl --user stop milchik-listener` — the tick then resumes polling within
90 seconds, so stopping it costs latency, not function.
No credentials are written to logs or repository files. No Telegram connection is
made while configuration is missing or disabled.

## Verification

Tests cover acceptance, identity/chat/message checks, replay, expiry, revocation,
modified files, distinct feedback choices, deduplication, uncertain delivery,
per-product thresholds, absence of network access when unconfigured, two-chat
routing (monitor to group, private to TK, monitor held when unpaired),
fleet-event once-only reporting, and drift/memory signal batching.

Live transport is verified as of 2026-09-06: a message delivered to the private
chat, a `/status` sent from Telegram and consumed by the tick (offset advanced
735430119 to 735430120), the monitor group captured from a `my_chat_member`
event, and a message delivered to that group.

**On-device buttons remain unverified.** No card carrying the approval buttons or
the distinct feedback buttons has been delivered or pressed, because no fleet
task has ever reached review — the decision path is covered by tests against
mocks only.

API behavior was checked against Telegram's official
[Bot API](https://core.telegram.org/bots/api) and
[bot features](https://core.telegram.org/bots/features) documentation.
