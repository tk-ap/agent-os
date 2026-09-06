# Routine Run Evidence

Run records for the routines defined in `routines/`. Approved 2026-09-06.

Separate from `docs/security/evidence/`, which holds security acceptance and attestation evidence. Routine runs are operational history, not security control evidence, and mixing them would dilute both.

## Layout

```
docs/evidence/routines/<routine-id>/<YYYY-MM-DD>-<run-id>.json
```

One file per run, including no-op runs. A routine that skipped still records that it ran and found nothing — silence in this directory must mean "did not run," never "ran and had nothing to say."

## Record shape

Fields follow the evidence event in `skills/owned/audit-evidence-ledger/SKILL.md`:

| Field | Notes |
|---|---|
| `event_id` | Unique run ID |
| `timestamp` | ISO 8601, UTC |
| `routine_id` | Matches the filename under `routines/` |
| `task_envelope_id` | The envelope this run executed under |
| `product` | Affected product(s) per `registry/product-routing.yaml` |
| `environment` | Host and harness the run executed on |
| `actor` | Executing agent identity, and the harness it ran through — these are distinct |
| `event_type` | `execution`, plus `signal` / `decision` / `verification` / `reversal` / `outcome` as applicable |
| `trigger` | What fired the run, and the evidence condition evaluated |
| `decision` | `published`, `pr_opened`, `skipped`, `suspended`, `failed` |
| `inputs` | Source record IDs consumed, with provenance |
| `actions` | What changed, with target paths or URLs |
| `validation` | Per-rule pass/fail from the routine's validation section |
| `verification` | Independent check result and method |
| `cost` | Input/output/cache tokens and dollar cost when available |
| `limitations` | What this run could not establish |
| `visibility` | `private` / `internal` / `sponsor-safe` / `public-candidate` |
| `reversal_path` | Concrete command or steps to undo |

## Rules

- Append-only. Corrections are new records that reference the corrected `event_id`; prior records are never rewritten.
- Reversals and failed runs are recorded, not deleted — they are the part of the history most worth keeping.
- No secrets, credentials, tokens, or unnecessary personal data.
- `intended`, `simulated`, `preview`, `deployed`, and `user-validated` states stay distinct in every record.
- A run that publishes without writing a record here is a **failed run**, even when the page itself is correct.
