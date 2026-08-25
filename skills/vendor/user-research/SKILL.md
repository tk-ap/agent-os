---
name: user-research
description: Plan and structure user research, including interviews, usability tests, surveys, card sorting, diary studies, and A/B tests. Use when Agent OS needs evidence about user needs, behavior, comprehension, or experience rather than relying on internal assumptions.
source_repository: anthropics/knowledge-work-plugins
source_path: design/skills/user-research/SKILL.md
source_commit: 4fa3cb92e2942d6594200fa8d2c800708e086072
license: Apache-2.0
adapted_for: agent-os
---

# User Research

Use research to reduce uncertainty about users before committing product or experience decisions.

## Choose the Method
- Interviews: deep needs, motivations, workflows, constraints.
- Usability testing: whether a specific flow or design works.
- Surveys: quantify attitudes or preferences across larger samples.
- Card sorting: information architecture and grouping.
- Diary studies: behavior over time.
- A/B tests: compare measurable behavior between alternatives when statistical conditions are met.

## Workflow
1. State the decision the research must inform.
2. Separate known facts, assumptions, and open questions.
3. Select the lowest-cost method capable of resolving the material uncertainty.
4. Define participants and recruitment criteria.
5. Write neutral questions or tasks; avoid leading prompts.
6. Collect observations separately from interpretations.
7. Synthesize themes, contradictions, edge cases, and confidence.
8. Route findings to the owning agent: Designer for experience, Scout for external/customer signal, Zoie for opportunity, Steward for initiative implications.

## Interview Guide
Use: warm-up → current context → deep dive → concept/reaction if relevant → wrap-up.

## Output
Return research objective, method, participant criteria, questions/tasks, evidence captured, findings, limitations, and the decisions the evidence supports or does not support.

## Guardrails
Do not infer market demand from a tiny convenience sample. Do not turn anecdotes into prevalence claims. Preserve disconfirming evidence.