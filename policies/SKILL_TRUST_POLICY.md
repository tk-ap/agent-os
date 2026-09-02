# Agent OS Skill Trust Policy

## Purpose

Treat every external skill, prompt package, plugin, script bundle, MCP configuration, and skill dependency as untrusted supply-chain input until Agent OS admits an immutable reviewed version.

A skill provides method. It does not receive authority merely because an agent can read it.

The security objective is not to prove that a skill author is a good actor. The objective is to keep the blast radius bounded even when a skill is malicious, compromised, misleading, or simply wrong.

## Core rule

**Trust actions, not instructions.**

An instruction inside a skill cannot grant itself filesystem, shell, network, credential, package-install, external-mutation, or control-plane authority. Runtime authority must come from an Agent OS authorization decision outside the skill.

## Trust states

External skill material moves through these states only:

1. `untrusted` — discovered but not inspected; never executable.
2. `quarantined` — immutable source captured for inspection; never executable against real credentials or production state.
3. `under-review` — provenance, dependencies, instructions, scripts, requested capabilities, and policy conflicts are being inspected.
4. `approved` — a specific immutable source digest passed the required review and sandbox checks; approval alone does not grant task authority.
5. `active` — an approved digest may be selected by the skill resolver inside its admitted capability envelope.
6. `suspended` — temporarily unavailable pending investigation or revalidation.
7. `revoked` — denied from future runtime use. Revocation wins over any cached approval.
8. `superseded` — replaced by another reviewed immutable digest; no longer selected for new work.

Discovery, popularity, a package-install command, repository ownership, a verified commit, or prior successful use does not skip a state.

## Root of trust

The following surfaces determine who may act, what may execute, or how trust is evaluated. They are control-plane material:

- `BOOTSTRAP.md`
- `HOST_PROFILES.md`
- `policies/`
- `registry/`
- `agents/`
- `contracts/`
- `skills/skill-resolver/`
- `skills/owned/authorization-policy/`
- `.github/` security, workflow, ownership, and repository-control configuration
- credential, secret, identity, permission, signing, deployment, and host-trust configuration in any bound environment

### Root-of-trust invariants

- A loaded skill may not modify the rules that determine whether that skill is trusted.
- An executing agent may not grant itself additional authority, approve its own skill acquisition, weaken the policy evaluating its authority, or disable the controls observing its execution.
- A third-party skill never receives direct control-plane write authority.
- A control-plane change must be represented as a separate explicit task with its own authorization and evidence, even when an owned skill recommends the change.
- Control-plane mutations require a human or independently authorized control path when they affect identity, credentials, permissions, trust policy, signing, deployment authority, or enforcement.
- Runtime enforcement claims are invalid unless the host/action boundary actually enforces these restrictions.

## Risk classes

### L0 — Reference

Text or static reference material only. No repository reads beyond the supplied material; no writes, shell, network, credentials, or external mutation.

### L1 — Local read

May inspect explicitly scoped project files. No writes, shell, network, credentials, package installation, or external mutation.

### L2 — Local write

May edit explicitly authorized project files inside a bounded task scope. No control-plane writes. Shell/network/package/credentials are denied unless the skill is separately admitted at a higher class.

### L3 — Execution

Requires shell, scripts, local executables, package tooling, build tooling, or other code execution. Admission must inspect the complete executable/dependency surface and sandbox behavior.

### L4 — External

May call network services or cause externally visible/API mutations. Requires an explicit allowlist of systems, domains/actions, and task-time authorization. Real credentials remain task-scoped and least-privilege.

### L5 — Privileged

Would touch production credentials, permissions, identity, money, destructive state, signing, deployment control, or equivalent privileged surfaces. Standing skill-level authority is prohibited. Each privileged action requires fresh authorization and human escalation unless a higher-order policy explicitly provides a narrower enforceable grant.

Risk class is determined by the maximum capability required, not by the skill's marketing description.

## Capability declaration

Before approval, a candidate must have a machine-readable declaration conforming to `contracts/skill-capability.schema.json`.

The declaration must identify:

- exact source repository/artifact and immutable commit/blob/digest;
- filesystem read/write scope;
- shell/script requirements;
- network destinations;
- package-install requirements;
- credential/secret requirements;
- external systems/actions it may mutate;
- required tools and dependencies;
- explicit denial of control-plane writes and self-modification of permissions.

Undeclared capability requests fail closed at runtime. A convincing explanation inside the skill is not authorization.

## Admission evidence

Approval requires evidence appropriate to risk:

- immutable source captured and hashed/pinned;
- provenance and license reviewed;
- `SKILL.md` and all referenced files inspected;
- scripts, package manifests, install hooks, workflow files, MCP/server configuration, remote URLs, binary/download behavior, environment variables, and transitive execution assumptions inspected where applicable;
- instruction-injection/self-install/self-escalation behavior identified and removed or blocked;
- capability declaration reviewed against actual behavior;
- sandbox/forward test completed for L2+ and whenever executable behavior exists;
- reviewer(s), date, findings, known risks, and revocation conditions recorded;
- approval is for the immutable reviewed digest only.

## High-signal review findings

These require explicit investigation and usually raise risk or block admission:

- `curl | bash`, remote bootstrap, dynamic code download, or mutable installer behavior;
- `eval`, shell construction from untrusted text, obfuscated/base64 payload execution, or hidden binaries;
- credential enumeration, home-directory crawling, SSH/keychain access, or reading secret stores not required by scope;
- unexpected outbound network calls or telemetry;
- changing git remotes, repository permissions, branch/ruleset controls, signing, or workflow security;
- instructions to ignore/replace higher-order policy, approve itself, install itself globally, disable review, or rewrite Agent OS trust configuration;
- package `preinstall`/`install`/`postinstall` hooks or transitive dependencies with unexplained execution;
- requests for broad wildcard filesystem/network/credential access where a narrower grant would work;
- attempts to disable validation, logging, authorization, sandboxing, or evidence capture.

A red flag is an investigation trigger, not automatic proof of malicious intent. The system still fails closed until resolved.

## Runtime isolation

Approval is not a credential grant.

At execution time:

- select the minimum sufficient approved skill set;
- bind only task-authorized files/resources;
- supply ephemeral or task-scoped credentials only when needed;
- deny undeclared network/package/shell capabilities;
- do not inherit an agent's unrelated authority into a skill;
- enforce external mutations at the action boundary through `authorization-policy`;
- log the immutable skill digest and capability envelope used;
- preserve rollback/incident evidence where applicable.

The security model is explicitly:

`skill != agent identity != tool capability != credential != authorization`

## Sandbox requirements

For L2+ candidates, and all candidates containing executable logic, sandbox tests should attempt both the stated workflow and adversarial boundary cases.

Use synthetic projects and fake/honeytoken secrets. Prefer denied or monitored outbound network access. Test attempts to:

- read outside the admitted filesystem scope;
- write control-plane/security files;
- enumerate environment variables or credentials;
- run undeclared shell commands;
- install undeclared dependencies;
- contact undeclared domains;
- mutate external systems;
- change its own capability declaration or admission record;
- instruct the reviewer/agent to bypass higher-order policy.

An undeclared access attempt is evidence against admission even when the primary task succeeds.

## Separation of duties

- A skill cannot approve itself.
- The producer of an external skill review cannot unilaterally grant L4/L5 runtime authority.
- Rook owns security review; Eugene may review executable/dependency behavior; W Dog may review systemic consistency; the relevant domain owner reviews capability necessity.
- L4 external mutation requires authorization-policy compatibility.
- L5 privileged behavior requires fresh human approval unless an explicitly narrower enforceable policy exists.

## Revocation

`revoked` and `suspended` records must fail closed even if a skill is already cached or vendored.

Triggers include:

- upstream compromise or maintainer/account incident;
- malicious or undeclared runtime behavior;
- newly discovered vulnerability;
- dependency compromise;
- mismatch between pinned/reviewed material and runtime material;
- loss of provenance;
- repeated policy violations or unsafe false assumptions.

A replacement version enters through quarantine again. Trust does not automatically transfer to a newer commit.

## Repository enforcement requirements

Policy text alone is not enforcement. The Agent OS repository should require protected `main`, review for root-of-trust changes, and code ownership for control-plane surfaces. `.github/CODEOWNERS` records the intended owner, but repository branch/ruleset settings must actually require that review before Agent OS can claim the GitHub root of trust is enforced.

As of the introduction of this policy, repository-side enforcement must be verified separately before making a protected-control-plane claim.
