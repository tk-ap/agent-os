---
name: audit-evidence-ledger
description: Record traceable evidence for agent decisions, approvals, execution, verification, reversals, and outcomes. Use for governance audits, product learning, Build Journal source material, or contested system state.
---

# Audit Evidence Ledger

Create a factual chain from signal to outcome without turning private operational data into public narrative automatically.

## Evidence Event

Record:

- event ID and timestamp;
- product, environment, and task-envelope ID;
- actor and role;
- event type: signal, decision, approval, execution, verification, reversal, outcome, or correction;
- input references and relevant policy/contract version;
- action or decision summary;
- result and verification evidence;
- confidence, limitations, and follow-up;
- visibility: private, internal, sponsor-safe, or public-candidate.

## Rules

- Preserve immutable history; append corrections rather than rewriting prior events.
- Link claims to evidence and distinguish intended, simulated, preview, deployed, and user-validated states.
- Exclude secrets, raw credentials, unnecessary personal data, and privileged content.
- A Build Journal entry is a curated projection of evidence, not the ledger itself.
- Record reversals and failed deployments because they are part of product learning.

## Output

Return structured events, missing evidence, confidence, visibility classification, and any safe public-journal candidate.
