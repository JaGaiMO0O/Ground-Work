# Handoff 2026-10-27 - build 0.1A release

Goal: release build-0.1A to a small rollout. The tag is the lead's, on `main`,
on the user's go-ahead.

Done: every 0.1A task is merged into `main` (hash = merge commit on `main`).
- T00 `7bfbb3a` - harnesses parallel-safe and 3.8-safe
- T01 `0d8a02a` - only template files travel (git, not disk)
- T02 `fdf06cf` - hooks find Python on any OS
- T03 `92337a7` - usage.py finds transcripts on any path
- T04 `70e8839` - card templates require citations
- T05 `f214843` - check.py enforces card contracts
- T06 `c86f435` - second-gen adopt; build label in manifest
- T07 `befa2f5` - interview before writing a card
- T08 `332eb65` - AGENTS.md: a card is a map
- T09 `684ac0b` - docs drift; derived build label
- T10 `183474c` - detect missed test commands
- T11 `f4e29bd` - ADR 0004: cards grow from tasks
- T12 `b3710ef` - scan.py false positive; scan suite
- T13 `3dc8f55` - QA end to end: 7 passed, 1 failed, 2 could not verify
  (the failure, undo leaving `.secrets-baseline`, was fixed by T19)
- T14 - this release prep (merge hash set by the lead)
- T15 `2cf05ce` - skip-list check asks git
- T16 `71dddaf` - docs/plan stays home; null scripts keep install
- T17 `6f9a0e3` - security: scan repos under build/vendor dirs
- T18 `cf1e185` - last survey-first messages
- T19 `303655e` - undo leaves nothing behind; printed command works
- T20 `0a495ac` - starter prompts follow 0.1A's card rules

Open:
- T13 F3: detected `test: pytest` is wrong when tests sit in a nested dir that
  imports top-level modules (JLGC: run from `backend/`).
- T13 F4: the C2 reference check counts the scaffold's own `scripts/` as
  project code, so a Do-not-read entry such as `__pycache__/` warns.
- T13 F5: a clone into a deep folder on Windows fails `Filename too long`
  (tester note now in TESTING.md).
- T13 F6: adopt prompts run together on one line when stdin is not a TTY.
- Deferred: `--update` for adopted projects; `.ps1` adapters on macOS (`pwsh`);
  `CLAUDE_CONFIG_DIR`; nested `.csproj`; the dead `tests/invariants.py` allow
  entry in adopted `settings.json`; promoting cards from `usage.py` counts; an
  ADR correcting 0003's weight claim; on Windows, with no `python` but the
  Microsoft Store `python3` stub on PATH, the hooks run the stub and fail
  visibly without blocking (T02).
- Full list: known issues in `docs/plan/ROADMAP.md`.

Key files: `TESTING.md` (Track D), `RUNBOOK.md`, `STATUS.md`,
`docs/plan/ROADMAP.md`.

Gotcha: the failure is step 6. After undo, the tree is not byte-identical to
before - it has one extra file, `.secrets-baseline` (T13; fixed by T19).

Next: rollout with at least one Mac and one Java/Maven project; the original
tester re-runs review tasks 1 and 4; rename the directory to `Ground Work`
with no session open.
