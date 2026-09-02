# SkillSpector source review — 2026-09-02

## Purpose

Evaluate NVIDIA SkillSpector as a security-tool candidate for Agent OS skill admission without treating a scanner verdict as trust, authorization, or proof of good faith.

## Source

- Repository: `NVIDIA/SkillSpector`
- Pinned commit reviewed: `7805bb94843d91cb9937f57264ca52642164499b`
- License: Apache-2.0
- Primary role: security scanner for AI agent skills before installation/admission

## Useful capability

SkillSpector is materially aligned with the Agent OS threat model because it scans for prompt injection, data exfiltration, privilege escalation, supply-chain risks, dangerous code, excessive agency, memory poisoning, tool misuse, MCP least-privilege/tool-poisoning risks, and related categories.

It can emit JSON/SARIF evidence and supports baselines/fingerprints so later scans can distinguish new findings from reviewed/suppressed findings.

This is useful as an evidence-producing pre-admission tool, especially before manual capability review and adversarial sandboxing.

## Integration posture

Do not install or bind SkillSpector into Agent OS runtime as part of this PR.

Initial evaluation should use:

1. an already captured immutable candidate skill/artifact;
2. an isolated local/container environment;
3. static analysis (`--no-llm`) first;
4. no production credentials;
5. outbound network denied after source capture where practical;
6. machine-readable output retained as admission evidence.

LLM, live vulnerability lookup, MCP, or remote scanning modes are separate capability expansions and require their own review.

## Trust boundary

SkillSpector is a security instrument, not a security authority.

A low score or `safe_to_install` result must never:

- approve a skill automatically;
- grant tool or credential access;
- satisfy the Agent OS capability declaration;
- replace complete-source/dependency inspection;
- replace sandbox/adversarial tests;
- replace Rook/Eugene review or required human approval;
- allow mutable upstream `latest` content to execute.

Likewise, suppressions/baselines are reviewed evidence. They cannot become a mechanism for silently normalizing new risk.

## Risks of SkillSpector itself

The scanner is executable software and therefore must be treated as third-party supply-chain input too.

Relevant risks include:

- Python/package installation and transitive dependency execution;
- optional LLM/provider credentials and outbound network access;
- optional live vulnerability lookups;
- optional MCP server exposure;
- false positives/false negatives and semantic-analysis model variance;
- scanner-version drift changing scores/findings over time.

Its documentation notes that HTTP MCP mode is unauthenticated; Agent OS must not expose that transport on a routable interface without an independent authenticated boundary.

## Decision

Disposition: **candidate security tool; evaluate before integration**.

Usefulness is high enough to place it in the Phase 2 admission-tool shortlist. Runtime activation waits until SkillSpector itself passes the Agent OS zero-trust process and the host can enforce its declared capabilities.

Every future scan result should record the exact scanner version/digest and scan mode so static-only evidence cannot be confused with semantic or sandbox clearance.
