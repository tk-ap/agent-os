# Voice Profile — TK Ashwood

**Version:** 0.1.0 (corpus-derived)
**Owner:** Marlo
**Status:** operational for registers R1–R4. R5 thin. R6 has no corpus — see §Gaps.

## Purpose

This profile is the system of record for TK Ashwood's written voice. Every rule below cites the corpus passage that produced it. A rule without a citation is a guess and is marked `[UNVERIFIED]`.

This is a specialized authoring reference, not a style guide for the ecosystem. It describes how one person writes.

## Corpus

| ID | Source | Register | Weight |
|---|---|---|---|
| C1 | `ashwood/dispatch/001-the-mind-is-the-moat/` | Long-form argument | Primary |
| C2 | `ashwood/journal/field-notes/what-counts-as-done/` | Build reflection | Primary |
| C3 | `ashwood/journal/field-notes/2026-08-28-why-this-work.md` | Cross-build reflection | Primary |
| C4 | `ashwood/about/` | Personal / lineage | Primary |
| C5 | `ashwood/ai-from-zero/` | Plain-language explainer | Secondary |
| C6 | `ALVIRA/src/routes/index.tsx` | Product copy (compressed) | Fragmentary |

Corpus is read before drafting. It is not summarized from memory.

---

## The Registers

### R1 — DISPATCH (long-form argument) · C1

The fullest voice. Builds an argument across many short paragraphs, each carrying one beat. Names a contradiction early and stays inside it. Closes on a compressed refrain.

Opens by putting the author inside the problem: *"I'm building with AI at almost the exact moment I'm becoming increasingly uncomfortable with what AI is being used to make. That probably sounds contradictory. It isn't."* (C1)

### R2 — FIELD NOTE (build reflection) · C2, C3

Structured, headed, contemporaneous. C2 uses an explicit four-part frame: **WHAT I THOUGHT / WHAT HAPPENED / WHAT CHANGED / WHAT I BELIEVE NOW**. Each subsection is led by a bolded declarative sentence, then unpacked in two to four plain sentences.

C2's leads, as a pattern to reuse: *"A successful preview felt close to a successful change." / "The previews kept being valid builds and invalid answers." / "READY did not mean verified." / "The acceptance gate is not a weakness."*

Field notes carry a front-matter block: date, type, status, and an editorial role that states what the note is **not** claiming (C3).

### R3 — PERSONAL / LINEAGE · C4

Warmer, longer sentences, em-dash appositives. Family and Jamaica are specific and load-bearing, never decorative: *"My maternal grandmother, Myrtle Alvira Ashwood, was my greatest inspiration, teacher, and cheerleader."* (C4)

Names carry meaning and the meaning is explained: ALVIRA from the grandmother's middle name, ailhat as "Tahlia" reversed, khlear from Khrystal (C4). This register also does careful distinction work — the motto echo is explicitly *"not a translation or rewrite."*

### R4 — EXPLAINER · C5

Numbered sections. Each opens with a short principle line: *"Start with your life, not the technology." / "An answer is not the same as a goal." / "The real skill is deciding what stays with you."* Then a concrete table or list. Second person is permitted **here and only here**, because it is teaching, not selling: *"You do not need to become an AI expert. You need to learn what you can hand off."*

Refuses false completeness: *"Not every AI tool can do every one of these things."*

### R5 — PRODUCT (compressed) · C6 · THIN

Fragments and questions rather than sentences. Declarative, unhurried, no verbs of urgency: *"The harder part is knowing what matters. / What deserves your attention. / What problem is worth solving. / What's worth building — and what doesn't need to be built at all."* (C6)

Only six usable fragments exist. Drafts in R5 are **draft-only regardless of surface** until the corpus grows.

### R6 — SOCIAL · NO CORPUS

No samples exist. Marlo does not have this register. See §Gaps.

---

## Devices

**Beat paragraphs.** One- and two-sentence paragraphs used as turns in an argument, not as formatting. Each earns its break by advancing the claim. (C1, C2)

**Arrow chains.** A process rendered as a sequence, then subverted or replaced by a better one. Used sparingly — roughly once per piece, at the structural hinge:
- *"generate → distribute → measure → optimize → generate again."* (C1)
- *"experience → context → judgment → AI amplification → evaluation → deeper context."* (C1)
- *"request → governed task → context → authorization → agent and skills → harness and host → implementation → preview → human verification → evidence."* (C2)
- *"see the pattern → make it understandable → build the structure → own part of the value."* (C4)

**The flat inversion.** A claim stated as a plain reversal of the expected one, with no hedging around it. *"I increasingly think the human is the scarce input." / "That is not intelligence. It is autonomous enshittification." / "The acceptance gate is not a weakness."* (C1, C2)

**The real distinction.** The signature move: reject the framing, then name the boundary that actually matters. *"The interesting boundary is not human versus machine. It is judgment versus execution."* (C2) *"The interesting choice is not between using AI and rejecting it. It is between deciding what role the technology should play..."* (C1)

**Definition by negation.** *"Not just information. The memory of why something matters. The experience that makes one detail important and another irrelevant."* (C1)

**Concrete people over abstractions.** When the argument needs a population, it names occupations: teacher, nurse, artist, parent, researcher, tradesperson, small-business owner (C1). Never "users," "creators," or "professionals."

**The owned belief.** First person, hedged as belief rather than asserted as fact: *"I think," "I increasingly think," "I do not think," "That distinction matters to me."* (C1) The hedge is not weakness — it is the claim being honest about its status.

**The question that is not rhetorical.** *"How do you participate in a system without allowing its incentives to determine the values of your work?"* (C1) Asked, then genuinely worked, not answered in the next line.

**Compressed refrain at the close.** The piece contracts to a few words. *"The mind." / "Each one, teach one." / "THE MIND IS THE MOAT."* (C1) *"Out of one, many becomings."* (C3, C4)

**The self-limiting guard.** A sentence that narrows the claim before a reader can over-read it. *"These are related at the thesis level. They are not evidence that every product should become a housing-support product."* (C3) This is a required move whenever a piece draws a pattern across products.

---

## Negative Space

Hard bans. These are not preferences and do not yield to a brief.

**The four banned marketing moves** (confirmed by TK, 2026-09-05):

1. **Urgency and scarcity.** No "limited time," no "only N spots," no countdowns, no artificial deadlines.
2. **Social proof and testimonials.** No "trusted by N," no logo walls, no star ratings, no quoted praise — especially no untraceable numbers.
3. **Before/after and pain-agitation.** No "tired of X?", no "stop wasting hours," no inflicting the problem on the reader in order to sell the cure.
4. **CTA stacking and second-person selling.** No repeated call-to-action blocks, no "you'll love," no "imagine if you could." Second person is permitted in R4 explainers only, where it teaches rather than sells.

These are consistent with the argument of C1, which attacks precisely this grammar: *"every audience into a funnel, every improvement in efficiency into an excuse to produce more."*

**Also banned:**

- Exclamation marks. Zero across the entire corpus.
- Hype vocabulary: unlock, supercharge, game-changing, revolutionary, seamless, effortless, "10x your," "the future of."
- Corporate filler: synergy, best-in-class, move the needle, leverage our strengths.
- Manufactured certainty. C4 is explicit: *"The goal is not to manufacture certainty; it is to make complexity understandable enough to act on responsibly."*
- Collapsing evidence states. Implemented, simulated, preview, deployed, and user-validated stay distinct (`registry/product-routing.yaml`). Preview capability is never written as shipped.
- Overclaiming enforcement for ledgato; representing Agent OS / Workforce as a public product; treating ALVIRA Bridge as standalone.
- Claiming every ASHWOOD product is a social-services product (guarded explicitly in C3).
- Resolving a contradiction cheaply. If the piece names a tension, it stays in it. C1's entire structure depends on refusing the easy exit.

### Rejection Log

Append every draft TK rejects, with the passage and the reason. The reason is the artifact; the rejected text is the evidence. Per C2: *"A governed system should remember why an implementation was rejected, not only the final code that survived. Otherwise the next agent can repeat the same mistake with perfect technical confidence."*

_(empty — no drafts rejected yet)_

---

## Overdone — the imitator check

Run this before every handoff. These are the failures of someone imitating the voice well enough to be dangerous.

1. **The beat paragraph, until nothing lands.** The most likely failure. In C1 the one-line paragraph is a turn in an argument. An imitator makes every line a beat, and the rhythm flattens into a drum with no melody. **Check:** could any two adjacent paragraphs be joined without losing a turn? Join them.

2. **Arrow chains everywhere.** The corpus uses roughly one per piece, at the hinge. **Check:** more than two in a piece is decoration.

3. **"Not X. It is Y." on repeat.** The flat inversion is powerful once or twice. Used six times it becomes a tic that signals a machine. **Check:** count them.

4. **Refrain inflation.** Not every piece earns a closing refrain. C2 and C3 do not have one. **Check:** does this piece have a phrase worth compressing to, or am I bolting one on?

5. **Borrowed gravity.** Invoking the grandmother, Jamaica, or family lineage to add weight to a product argument. In the corpus these appear where they are genuinely the subject (C4) or genuinely the origin of the thought (C1's education passage). **Check:** would this sentence survive if the personal detail were removed? If it would, remove it. If the piece collapses, the detail is load-bearing and belongs.

6. **Profundity without a claim.** The voice sounds thoughtful, so an imitator produces thoughtful-sounding text with nothing asserted. **Check:** state the piece's claim in one sentence. If you cannot, there is no piece.

7. **Distinction theater.** "The real question is not A, it is B" — where A and B are the same thing in different words. **Check:** could a reasonable person hold A and reject B? If not, the distinction is fake.

---

## Gaps — what the interview must still supply

The corpus is stronger than expected and covers R1–R4 well. Three gaps remain, and they are the reason samples are still worth collecting:

- **R6 social (no corpus).** Zero samples. Marlo cannot write X or LinkedIn posts in voice. Needs 3–5 real posts, ideally including one that underperformed.
- **R5 product copy (fragmentary).** Six fragments from one landing page. Needs 2–3 pieces of real product/landing copy — a page TK wrote and shipped, and ideally one TK wrote and rejected.
- **Rejected drafts (none).** The negative-space rules above are derived from what the corpus *does not do*, which is weaker evidence than knowing what TK actively threw out and why. Any rejected draft, with the reason, is worth more than another good sample.

Two open questions the corpus cannot answer:

1. **Overclaim boundary.** When a piece needs a claim the evidence does not support, does TK want a refusal, or aspirational copy visibly marked for approval? Marlo currently refuses and marks `[CLAIM UNSUPPORTED — Scout]`. `[UNVERIFIED]`
2. **Compression floor.** How short can the voice go before it stops being the voice? C6 suggests it survives at fragment length, but six fragments is not enough to be sure. `[UNVERIFIED]`
