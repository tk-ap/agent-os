---
name: research-synthesis
description: Synthesize interviews, surveys, usability notes, support tickets, reviews, or other qualitative research into evidence-backed themes, insights, opportunities, and next questions. Use when Agent OS has raw customer evidence that must become decision-ready without overstating certainty.
source_repository: anthropics/knowledge-work-plugins
source_path: design/skills/research-synthesis/SKILL.md
source_blob: 4807340a6ece564451718200b041a379b1c573a0
license: Apache-2.0
adapted_for: agent-os
---

# Research Synthesis

## Workflow
1. Identify the source set, method, participant count, date range, and material limitations.
2. Separate observation from interpretation.
3. Cluster recurring evidence into themes without hiding outliers or contradictions.
4. Quantify prevalence only when the source supports it; prefer `X of Y` to vague terms such as “most.”
5. For each theme record supporting evidence, implication, confidence, and unresolved questions.
6. Convert findings into opportunities, not automatic feature prescriptions.
7. Prioritize recommendations by evidence strength and expected impact.
8. Route implications to the appropriate Agent OS owner.

## Output
- Executive summary
- Key themes with prevalence/evidence
- Contradictions and minority signals
- Insights → opportunities
- User segments only when evidence supports segmentation
- Recommendations with confidence
- Questions for further research
- Methodology limitations

## Guardrails
Never invent participant quotes. Never collapse contradictory evidence into false consensus. A strong synthesis makes uncertainty visible.