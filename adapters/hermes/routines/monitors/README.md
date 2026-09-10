# Monitor scripts — contract

`discoverability-fingerprint.sh` is currently the only script here. It is the
trigger surface for `routines/discoverability-audit.md`: Hermes cron runs it on a
schedule and wakes the audit agent **only when its output changes**
(`monitor_script` / `--monitor-script`, quoted in `../README.md` from
`hermes_cli/cron.py`).

This file states the contract a second monitor script must satisfy so it is not
written by imitation alone. Every rule below traces to that script,
`../README.md`, or `routines/discoverability-audit.md`. Nothing here describes
Hermes cron behaviour beyond what `../README.md` already records.

## The contract

1. **stdout is the trigger surface.** The script's standard output — nothing
   else — decides whether the agent runs. Output byte-identical to the previous
   run means **no agent run**: "unchanged output means nothing to audit and no
   agent is woken" (script header; `../README.md`, "The monitor-script fit").
   Waking the agent costs money (audit contract §16); the script exists so the
   routine's skip condition (§4) is structural rather than something the model
   re-derives each run.

2. **Output must be a pure function of the watched state.** One line per watched
   input (script header). Given unchanged inputs the output must be identical
   between runs: no timestamps, no run IDs, no run-varying ordering. The
   fingerprint script emits none of these — it iterates fixed, named arrays and
   prints a content digest per input. Anything that changes on every run defeats
   the mechanism by waking the agent on every tick.

3. **Any change in a watched input must move the output.** The fingerprint
   script emits a content fingerprint (`cksum` + byte count) for each fetched
   document, not a presence check, so a changed `sitemap.xml` or `robots.txt`
   moves the output — each is "something the audit should look at" (script
   comments; audit contract §6, §15).

4. **An unreachable or missing input must change the output, not fail
   silently.** The fingerprint script prints `UNREACHABLE`, `MISSING`, `NOGIT`,
   or an explicit `http=<code>` in place of a digest. It runs under
   `set -uo pipefail` **without** `set -e` precisely so one failed probe emits a
   marker line instead of aborting the whole fingerprint, and it still exits `0`
   on a normal run (`apply.sh` preflight treats a non-zero exit as failure). An
   unreachable page is "exactly what this routine exists to notice" (audit
   contract §13; §15 escalates a wholly unreachable surface).

5. **Read-only, anonymous, no credentials, no side effects, no writes.** Stated
   verbatim in the script header and required by the audit contract: the routine
   "holds no credentials and authenticates to nothing" and fetches "as an
   ordinary anonymous visitor" (§5); `../README.md` confirms "no routine here
   needs a credential". A monitor script that writes a file, stores a cookie,
   posts data, or mutates a repository is outside this contract.

6. **Cheaper than the run it guards.** The script uses bounded `curl --max-time`
   probes and `git rev-parse HEAD` rather than fetching route trees. It runs on
   every cron tick whether or not the agent runs, so it must stay far below the
   agent run cost it exists to avoid (`../README.md`; audit contract §16).

7. **Watched targets are declared at the top of the script.** The fingerprint
   script lists its sites, legacy domains, and repos in named arrays. A
   decommissioned or legacy input is kept as a watched line — so that it coming
   back up or starting to redirect is noticed — and labelled as such, not
   deleted (script comments; audit contract §1, §15).

## What this contract deliberately does not document

- **The precise semantics of `--monitor-script`.** `../README.md` quotes a
  single line of `hermes_cli/cron.py`, and `apply.sh` notes the argparse
  spelling was never verified. Whether Hermes compares raw bytes or a hash,
  whether it normalises whitespace, where it stores the previous output, how the
  first run (no prior output) is treated, and whether the script's **exit code
  or stderr** affect triggering are all **unknown** from the material here and
  are not specified by this contract.
- **How often the monitor script itself runs.** That is the `schedule` in
  `../jobs.yaml` / `../apply.sh`, which per `../README.md` have not been applied.
- **Behaviour when `hermes-gateway.service` is down.** Covered by `../README.md`
  ("jobs silently stop firing"); a monitor script cannot compensate for it.
- **What the agent does once triggered.** Governed by
  `routines/discoverability-audit.md` and `../prompts/discoverability-audit.md`.
- **Cost caps and their enforcement.** In the routine contract (§16) and
  `../jobs.yaml`; `../jobs.yaml` states nothing on this host enforces them.
- **Registering, pausing, or deleting a job.** See `../jobs.yaml` and
  `../apply.sh`.
