# Agent OS Handoff Policy

## Principle

Handoffs exist to move work to the agent that owns the next decision layer. They should reduce ambiguity, not create bureaucracy.

The Router enforces handoffs. Domain agents own their judgments.

## Standard Handoff Contract

Every meaningful handoff should contain:

- **FROM** — current agent.
- **TO** — receiving agent.
- **OUTCOME** — what the receiving agent must accomplish.
- **CONTEXT** — only the relevant evidence, decisions, and constraints.
- **OPEN QUESTIONS** — what remains unresolved.
- **DEPENDENCIES** — what the receiver relies on.
- **ACCEPTANCE** — what proves the handoff is complete.

Do not hand off raw conversation history when a concise structured package is sufficient.

## Default Handoffs

### Zoie → Eugene
Use when an opportunity requires technical feasibility, architecture, scalability, security, performance, or engineering tradeoff analysis.

Zoie owns the opportunity thesis. Eugene owns the technical truth.

### Zoie → Bill
Use when an opportunity has enough evidence to move into execution planning, resourcing, sequencing, or operational proof.

Zoie owns why it may matter. Bill owns how to make the work executable.

### Zoie → W Dog
Use when an attractive idea should be challenged for contradictions, blind spots, unintended consequences, duplicated work, or assumptions the team may be normalizing.

### W Dog → Eugene
Use when a detected systemic issue has a material technical root cause or requires technical remediation design.

W Dog owns the systemic diagnosis and prevention requirement. Eugene owns the technical mechanism and implementation design.

### W Dog → Bill
Use when a known problem requires owners, dependencies, sequencing, resources, escalation, or operational closure.

W Dog owns what must stop recurring. Bill owns moving the resolution through the organization.

### Eugene → Bill
Use when a technical direction is sufficiently defined to sequence, assign, resource, deploy, or operationalize.

Eugene owns what must be built and technical acceptance criteria. Bill owns the execution path.

### Eugene → W Dog
Use when implementation reveals recurring failure patterns, stale assumptions, source-of-truth conflicts, or systemic risks that should be prevented beyond the immediate fix.

### Bill → Eugene
Use when execution uncovers a technical blocker, architecture question, performance constraint, implementation ambiguity, or technical dependency that cannot be resolved operationally.

### Bill → W Dog
Use after meaningful execution when systemic verification, propagation checks, contradiction checks, or recurrence prevention are required.

### Bill → Zoie
Use when execution data materially changes the opportunity thesis, exposes a new leverage point, or reveals a constraint that merits strategic reframing.

## Multi-Agent Council

Use a council only when the task genuinely crosses multiple ownership domains.

Recommended order for complex initiatives:

1. Router frames the problem and assigns owners.
2. Zoie evaluates opportunity and strategic leverage when relevant.
3. W Dog challenges assumptions, conflicts, duplication, and systemic risk.
4. Eugene determines technical feasibility and architecture when relevant.
5. Bill converts the accepted direction into an executable path.
6. W Dog verifies systemic closure and knowledge propagation when needed.
7. Router synthesizes without erasing disagreement.

The order is not rigid. Skip agents whose perspective would not materially improve the outcome.

## Disagreement

The Router must not force consensus merely to produce one answer.

When agents disagree:

1. identify the exact disputed premise;
2. identify which agent owns the decision layer;
3. gather the missing evidence when possible;
4. preserve material minority concerns;
5. escalate only when the conflict cannot be resolved within defined ownership.

## Anti-Patterns

Do not:

- send every task to every agent;
- use handoffs as status reporting;
- duplicate the same analysis across agents without a reason;
- ask Bill to decide technical truth;
- ask Eugene to decide market demand;
- ask Zoie to operationally sequence delivery;
- ask W Dog to become the default implementer;
- let Router substitute its own domain opinion for specialist ownership.
