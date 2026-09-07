# Salvage

Content rescued from branches that were deleted, kept as patches so a stale
branch can be removed without losing the change it carried.

## journal-facilitation-evidence-pass.patch

From `tk-ap/ashwood-info`, branch `journal/facilitation-evidence-pass`, tip
`8aac11715551d6ec87c65ffd18703edf695844c5`.

The branch read as 138 unpushed commits. It was 8 — four of them the same commit
message repeated — and the real change was one file, +12/−13 in
`journal/index.html`. The other ~130 were `origin/main` history that arrived via
a merge on 2026-09-04 and were missing from the stale remote branch. PR #12 is
CLOSED, and the branch sat 39 commits behind main.

**Do not apply this patch unmodified.** It deletes the Field Notes doorway from
the journal index:

    - <a class="build-doorway" href="/journal/field-notes/">…</a>

`/journal/field-notes/*` is one of the two paths Marlo may publish to unattended
(`agents/marlo/IDENTITY.md` §09). Removing the doorway would orphan every field
note the routine publishes — still live at its URL, unreachable from the index,
with nothing in the routine able to notice. The live site currently serves that
link and `/journal/field-notes/` returns 200.

What is worth keeping is the LATEST MOVEMENT rewrite, which is newer than what
is on main. Apply that portion to a fresh branch cut from current `origin/main`.
