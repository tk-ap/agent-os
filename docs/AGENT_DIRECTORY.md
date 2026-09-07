# Agent OS — quick agent directory

Status: human-readable quick reference
Canonical machine routing source: `registry/agents.yaml`

This page answers a simple operator question: **who does what?**

Use it to understand why Router/Milchik assigned a task to a particular agent, who to ask for a second opinion, and what each agent is *not* meant to own. The registry remains the routing source of truth; this directory is the plain-English companion.

| Agent | Main role | Best used for | Typical contribution |
| --- | --- | --- | --- |
| **Eugene** | Technical builder | Architecture, implementation, debugging, testing, infrastructure, deployment, performance, security engineering | Turns an approved technical plan into working, tested software and diagnoses implementation failures. |
| **W Dog** | Watchdog / verifier | Independent verification, root-cause analysis, contradiction/duplication detection, change impact, prevention | Checks whether work actually satisfies its acceptance criteria and surfaces systemic problems before they repeat. |
| **Rook** | Adversarial reviewer | Threat modeling, abuse cases, privacy/permission risk, irreversible actions, failure modes | Tries to break the plan safely before reality does; identifies ways an agent, user, or system could misuse or bypass it. |
| **Designer** | Experience specialist | UX, interaction design, information architecture, accessibility, usability, product comprehension | Makes products and operator surfaces understandable, navigable, and coherent for the person using them. |
| **Zoie** | Strategy / opportunity explorer | Product strategy, business models, opportunity discovery, experimentation, strategic reframing | Finds promising directions, recombines ideas, and proposes experiments or strategic alternatives. |
| **Scout** | Market & growth intelligence | Customers, competitors, positioning, pricing evidence, demand, distribution, partnerships, market monitoring | Brings external evidence into decisions: what users want, what competitors are doing, and where demand/distribution signals exist. |
| **Ledger** | Economics specialist | ROI, unit economics, budgets, spend, forecasts, opportunity cost, financial thresholds | Tests whether an initiative makes economic sense and what it costs relative to alternatives. |
| **Steward** | Initiative / priority owner | Business objectives, KPIs, portfolio prioritization, attention allocation, continue/change/stop decisions | Connects work to objectives and decides what deserves attention across the portfolio. |
| **Bill** | Logistics / execution planner | Sequencing, dependencies, ownership, readiness, critical path, handoffs, recurring work | Turns a goal into an executable sequence and makes sure the right prerequisites and owners are in place. |
| **Router** | Team coordinator | Task classification, agent selection, decomposition, coordination, handoff enforcement | Decides who should own a piece of work and how to split it. Router proposes assignments; it does not replace specialist judgment. |
| **Milchik** | Human ↔ fleet liaison | Operator communication, backlog awareness, attention ranking, approval/monitor channels, line-keeping | Keeps TK informed in human language, surfaces decisions/exceptions, and translates workforce state without becoming the decision-maker or executor. |

## Fast lookup by question

**“Who should build or debug this?”** → Eugene

**“Did this actually work / is the evidence good?”** → W Dog

**“How could this fail, be abused, or cross a boundary?”** → Rook

**“Will a normal person understand or use this?”** → Designer

**“Is there a better strategic direction or experiment?”** → Zoie

**“What does the market/customer evidence say?”** → Scout

**“Does this make financial sense?”** → Ledger

**“Should this be a priority at all?”** → Steward

**“What has to happen first, next, and by whom?”** → Bill

**“Who should own this task?”** → Router

**“What is the workforce doing, and do I need to act?”** → Milchik

## Handoff rule

A handoff should be understandable without opening this file. Human-facing messages should use the agent's **name + plain-English specialty**, for example:

> **Work assigned to Eugene — technical implementation**  
> Eugene is taking the ALVIRA sitemap/robots fix because it requires code changes and deployment verification.

The quick directory is supporting context, not a substitute for explaining *why this agent was chosen for this specific task*.

## Boundaries worth remembering

- **Router coordinates; specialists decide within their domains.**
- **Milchik communicates and supervises the line; he does not ship code, grant authority, or own product truth.**
- **W Dog verifies; it should not silently fix the work it is judging.**
- **Rook attacks assumptions and safety boundaries; it is not the default implementer.**
- **Eugene can build, but technical feasibility does not decide business priority, market truth, or economics.**
- Use the **minimum sufficient team** rather than involving every agent in every task.

If this directory and `registry/agents.yaml` ever disagree, fix the directory or registry intentionally; do not let the human explanation drift from the routing source of truth.
