Run the discoverability and route integrity audit defined in
/home/tk/Work/agent-os/routines/discoverability-audit.md.

Read that contract first and follow it exactly. It governs this run; this prompt
does not restate or override it. Read its task envelope too:
/home/tk/Work/agent-os/routines/envelopes/env-discoverability-audit.md

Binding constraints from the contract, repeated here because violating one is a
failed run rather than a judgment call:

- Read-only and anonymous. Hold no credentials. Authenticate to nothing.
- Extract head/meta/canonical/link elements OUTSIDE the model and pass only those.
  Do not read raw page HTML into context — §6 and §16.
- Open a DRAFT pull request. Never merge, never deploy.
- Mechanical fixes only. Anything that changes what the site SAYS — copy,
  headlines, positioning language in titles or meta descriptions, pricing,
  new pages, navigation — is reported as a recommendation in the PR
  description and never implemented. §7.
- De-indexing risk is the highest severity class. Escalate rather than fix. §12.
- At most one open audit PR per surface. Update the existing branch rather than
  opening a second. §9.
- Ceiling of 60 URL fetches. §14.
- For the first three runs: report findings only, no diff. §11.

Skip conditions are real outcomes. If nothing is above threshold, open no PR,
change nothing, and record the run as a skip. Do not lower the threshold to
produce output.

Write the run's evidence record to
docs/evidence/routines/discoverability-audit/<YYYY-MM-DD>-<run-id>.json
following docs/evidence/routines/README.md. Include measured input, output, and
cache token counts — the cost caps in §16 are projections and the first three
runs are what replaces them with measurement.

A run that completes without writing an evidence record is a failed run.
