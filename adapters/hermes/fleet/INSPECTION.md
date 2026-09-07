# The inspection loop

This file explains, in plain language, what happens to a piece of finished
work before it is shown to TK for a decision. The behaviour lives in
`adapters/hermes/fleet/telegram.py` (the functions `request_inspection`,
`read_inspection_verdicts`, `run_revisions`, and `collect_reviews`). The rule it
follows is written in `policies/HANDOFF_POLICY.md`, under "Producer / Inspector
Loops".

A few words used below:

- **Agent** — a program that carries out one piece of work using an AI model.
- **Producer** — the agent that did the work.
- **W Dog** — a different agent whose only job is to check other agents' work.
- **Card** — a message sent to TK in Telegram, sometimes with buttons.
- **Publish** — save the work permanently, for example by committing files. In
  this adapter nothing ever leaves the machine; there is no sending or deploying.

## The short version

1. An agent finishes a piece of work.
2. Before TK sees anything, W Dog checks that work independently.
3. Only after that check does a card reach TK asking what to do.

Work is never shown to TK on the word of the single agent that produced it.

## Step by step

### 1. A check is requested (`request_inspection`)

When a piece of work is marked finished, the system creates a separate checking
job and gives it to W Dog. The job carries instructions that tell W Dog to:

- **change no files** — it is there to judge, not to produce. This is written
  into the job as a rule, and confirming it changed nothing is one of the things
  W Dog has to report back. It is an instruction, not a locked door: the job is
  still given access to the files, and nothing in this code physically stops a
  write. The safeguard is that W Dog is told not to and must say whether it kept
  to that.
- **not take the producer's word for it** — W Dog has to open what the work
  claims to have changed and look for itself.
- **say PASS or FAIL for every point** the original work was supposed to meet,
  name the file or output it looked at for each one, and say what it could not
  check.

The checking job is also marked top priority — the highest level this system
uses. That is a label on the job. Whether a top-priority job actually runs
before other waiting work is decided by the queue, which is not part of these
functions and is not described here.

A checking job is itself a piece of work that finishes. The code will not create
a check of a check, so this cannot loop forever.

If the checking job cannot be started at all, that is written down as
"unavailable". TK is then told plainly that the check did not happen, rather than
being left to assume it did.

### 2. The result is read (`read_inspection_verdicts`)

When W Dog's check is done, the system reads the short summary W Dog wrote and
turns it into a single word: `pass` or `fail`.

**How it decides:** it searches the text of that summary for the letters
`FAIL`. If those letters appear anywhere, or the summary is empty, the result is
`fail`. Otherwise the result is `pass`. It is a text search, not an
understanding of the report.

### 3. Failed work goes back, within limits (`run_revisions`)

If the result is `fail` and the work has not been published:

- The work is sent back to the producer. The producer is given only the points
  that failed, plus an instruction not to redo the parts that passed and not to
  make the job bigger.
- **This can happen at most twice.** The limit on revision cycles is set to two.
- The loop also stops early if the same failure comes back unchanged, or if the
  work could not be sent back.
- When the loop stops without a pass, it **escalates**: a card goes to TK saying
  the agent could not get it right and the system has stopped trying. The card
  states what was asked, why it stopped, and what is still wrong. Nothing is
  published. The files are left on the machine exactly as the agent left them.
  The card says this now needs TK or a different owner.

### 4. The card for TK is built (`collect_reviews`)

- If there is no result yet, **no card is sent**. The work is held, not dropped.
  It reaches TK checked, or not at all.
- If the result was `pass`, the card tells TK that W Dog checked the work
  independently and found no problems, and includes W Dog's summary.
- If the result was `fail`, the card tells TK that problems were found, shows
  them, and warns that saying yes accepts work that failed its own checks.
- If the check could not run, the card says there is no second opinion, that the
  work has been seen only by the agent that did it, and that this is not meant to
  happen.

Every card also states that nothing is published, deployed, or visible to anyone
outside the machine, and offers three choices: publish the declared files, send
it back, or pause.

## What is known to be limited

This loop is a real safeguard, not a finished one. The honest limits:

- **The pass/fail decision is a text search.** It looks for the letters `FAIL`
  in W Dog's summary. A report that finds real problems but never writes that
  word would be read as a pass. A summary that happens to contain words like
  "failure" or "no failures" would be read as a fail. An empty summary is read
  as a fail.
- **The revision limit is two.** After two failed rounds the loop gives up and
  escalates to TK. It does not keep trying and it does not decide the work is
  good enough on its own.
- **"Independent" is narrow.** The checker is a separate job with read-only
  access. It is the same kind of program as the producer, running with the same
  tools minus the ability to write files. It is not a human and not a different
  system.
- **The whole path has not been run end to end.** As described in
  `adapters/hermes/fleet/TELEGRAM.md`, no real fleet work has yet reached this
  stage, so the buttons on these cards have been exercised only against
  stand-ins in tests.
- **A missing checker does not block delivery.** If W Dog cannot be started, the
  work still reaches TK — labelled as unchecked.

## What this file deliberately does not cover

- How a piece of work is created, given to an agent, run, retried, or marked
  finished. That is the fleet queue, described in
  `adapters/hermes/fleet/README.md`.
- What happens after TK presses a button — how files are committed and the
  checks around that (`perform_publish` in the same source file).
- The other jobs the same once-a-minute tick performs: commit digests,
  directives, fleet events, and drift or memory signals.
- How W Dog forms its judgement internally, and what a good or bad inspection
  report looks like.
- The database tables and the exact wording of each card.
- Setting up and pairing the Telegram bot, which is covered in
  `adapters/hermes/fleet/TELEGRAM.md`.
