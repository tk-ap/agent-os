# Independent Verifier — reusable AgentOS role

## Why this role exists

AgentOS needs a reusable verification capability for cases where the executor cannot legitimately certify its own work.

The concrete trigger was the LEDGATo enforcement stress-test cycle:

1. Claude executed the enforcement work and live stress test.
2. Claude found and remediated multiple defects.
3. Codex independently reviewed the changes and found additional blockers.
4. Claude remediated those blockers.
5. The boundary reached `PARTIALLY_VERIFIED`, but Claude was no longer eligible to provide final `VERIFIED` attestation because it had authored and remediated the work.

This was not a missing implementation-agent problem. It exposed a missing **independence contract**.

The correct solution is a reusable AgentOS role/capability, not another permanent named agent.

---

## Role

**Independent Verifier**

Purpose: independently determine whether a claimed result is actually true after execution and remediation, before final release/governance approval.

The verifier answers a narrower question than the executor or reviewer:

> **Does the evidence and live system state support the claimed outcome?**

The verifier does not own implementation, remediation, or release authority.

---

## Eligibility rule

A verifier is **ineligible** for a verification cycle if it:

- authored the work being verified;
- materially modified the work being verified;
- authored a remediation for a defect in the current verification cycle;
- materially participated in the implementation decisions whose result is being attested;
- would otherwise be approving its own work.

Changing model names, opening a new chat, or renaming an agent does not by itself create independence if the same execution identity is carrying forward authorship/remediation responsibility.

When eligibility is ambiguous, treat the candidate verifier as ineligible and route to another execution identity.

---

## Required operating behavior

The Independent Verifier must:

1. Start from the canonical code/state to be verified, not the executor's local assumptions.
2. Read the verification contract and prior evidence before running checks.
3. Re-run the required live or provider-backed tests where the claim depends on live behavior.
4. Use fresh credentials or a fresh verification context when the verification standard requires them.
5. Confirm downstream/provider state independently rather than trusting executor-reported output.
6. Check that known defects have corresponding remediation and qualifying retest evidence.
7. Record limitations and scope explicitly.
8. Produce durable evidence for the next governance step.

The verifier must **not** silently repair a failed verification and then certify the repaired state in the same cycle.

If a defect is found:

```text
Independent Verifier
        |
        v
   NOT VERIFIED
        |
        v
     Executor
        |
   remediation
        |
        v
fresh Independent Verifier pass
```

A verifier may describe the smallest fix needed, but implementation returns to the executor/remediation role.

---

## Allowed outcomes

The role returns only one of these terminal states:

### `VERIFIED`

The documented verification contract is satisfied for the stated scope and the evidence supports the claim.

### `NOT VERIFIED`

The claim is false, a bypass/failure was reproduced, required evidence contradicts the claim, or a blocking defect remains.

### `BLOCKED`

The verifier cannot reach a valid conclusion because required access, credentials, environment, provider state, test fixture, or evidence is unavailable.

`BLOCKED` must not be converted into `VERIFIED` by inference.

---

## Independence vs secondary review

Independent verification is not the same as normal code review.

A secondary reviewer asks questions such as:

- Is the implementation sound?
- Are there bugs or security flaws?
- Does the code match the intended design?

The Independent Verifier asks:

- Does the claimed outcome actually hold in the relevant environment?
- Did the protected/required action happen or not happen as claimed?
- Does provider state agree with AgentOS/agent evidence?
- Are remediated failures actually closed by a fresh retest?

Both may be required in one workflow.

---

## Relationship to Milchik and human authority

The roles stay separate:

```text
Executor
   |
secondary review
   |
remediation
   |
Independent Verifier
   |
VERIFIED / NOT VERIFIED / BLOCKED
   |
Milchik release/governance check
   |
TK / required human authority
```

**Independent Verifier:** determines whether the technical/evidentiary claim is true.

**Milchik:** determines whether the work satisfies release/governance requirements and is ready to advance.

**TK / human authority:** provides final human authorization where required.

Verification must not implicitly grant release authority.

---

## LEDGATo reference case

For the `github_lab_merge` enforcement boundary, the role exists to solve the exact transition:

```text
PARTIALLY_VERIFIED
        |
fresh independent live rerun
        |
provider readback + attack-suite evidence
        |
VERIFIED / NOT VERIFIED / BLOCKED
```

A valid independent verifier for this case must, at minimum:

- verify against canonical state containing the final blocker fixes;
- use a fresh lab-scoped GitHub credential rather than the executor's revoked credential;
- rerun the required live enforcement suite against the preserved disposable lab;
- re-confirm all defined attack families;
- independently confirm denied actions did not reach GitHub;
- confirm the authorized path executes exactly once;
- confirm replay is refused;
- confirm no unresolved bypass remains;
- record the attestation with the verifier identity and scope.

The result means verified **against the documented lab architecture and attack suite**, not universal or mathematical proof that no bypass can ever exist.

---

## Generalization across the ecosystem

This role should be callable by workflows involving:

- LEDGATo enforcement claims;
- production deployment verification;
- ALVIRA release claims;
- AgentOS execution outcomes;
- ailhat-routed consequential work;
- security-sensitive remediation;
- high-impact changes where "done" must be independently demonstrated.

The role should not be invoked for every trivial task. Use it when a workflow makes a consequential factual claim that should not be self-attested by the executor.

---

## AgentOS design rule

Do **not** create a permanent named agent solely for this function.

Model Independent Verifier as a role/capability that can be assigned to any eligible execution identity satisfying the independence contract.

This keeps the workforce small while making verification structurally enforceable.
