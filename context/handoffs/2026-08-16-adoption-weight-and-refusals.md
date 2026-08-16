# Handoff 2026-08-16 - adoption weight and refusals

**Goal:** clear the fixes the first adoption trial found
([2026-08-06](2026-08-06-first-real-adoption-trial.md)), and settle the design
question that gated the largest of them.

**Done:**

- **Adoption carries one profile, not all of them.** `init.py --adopt` now does
  what plain `init.py` always did. `--keep-profiles` opts back in.
- **Adoption refuses on a project with no git repository**, rather than warning
  about churn ranking and writing dozens of files anyway. `--force` overrides.
  On a tracked repo it now prints the undo (`git clean -nd`, then `-fd`).
- **A single-file directory can be an area.** `propose_areas` required two code
  files, which silently dropped `app/app.py` - the serving layer every session
  reads. One file is enough; the churn-first sort means one-file directories
  only take a slot when there is nothing better.
- **A profile's `scaffold/` now reaches the project root on adopt.** It was
  being copied to `profiles/<name>/scaffold/` and left there, so an adopted
  legacy project never received `integration/`, `map/_TEMPLATE/seams.md` or the
  legacy recipes. Nobody had noticed; nothing tested it.
- **Adoption carries only what the project runs** - see the ADR below. Dropped:
  `tests/**`, `init.py`, `_adopt.py`, the 20 `.sh`/`.ps1` shims.
- **`tests/adopt.py`** - 13 cases, 21s. New, and the reason the rest of this
  list is trustworthy.

Measured on the trial's shape of project: **95 scaffold files down to 59**,
`scripts/` from 44 to 22. Still zero pre-existing files modified.

## The decision

[ADR 0003](../../docs/decisions/0003-copy-per-project.md) - **copy per project,
not a shared install**, and copy less. The install was rejected on one argument:
`.claude/settings.json` points hooks at `scripts/hooks/guard.py` inside the
project, and under a shared install that path resolves against whatever Python
Claude Code happens to invoke. When it fails it fails *silently* - the hooks stop
firing with no error. That exact failure has already happened here once. The
divergence complaint that motivated the install is really a request for version
pinning, which copying already provides.

**Open:** the ADR creates one item and does not close it - an adopted project has
no way to say which version of the scaffold it holds, and no way to refresh it. A
stamp plus `init.py --update <dir>` is the answer. Nothing depends on it yet.

**Key files:** `scripts/_adopt.py` (`travels`, `destination_for`,
`propose_areas`), `scripts/init.py` (`adopt`), `tests/adopt.py`.

**Gotcha:** four of the new test cases were run against the *pre-fix* code first,
by stashing the two changed scripts, to confirm each one actually fails. Do that.
Two of these bugs had been sitting behind a passing 35-case suite for two weeks,
because the suite only ever ran `check.py` - it had no way to see a write path.
A rule with no test that has been seen to fail is a rule you are guessing about.

**Next:**

1. `git init` the real dry bean project and adopt it for real. Baseline first
   with `usage.py --path`, since adoption changes what the transcripts contain.
2. Write one card, for `src/`. Then leave it a week and re-measure against the
   trial's recorded baseline: 33% orientation, 41 files re-read across 3+
   sessions.
3. Only then decide whether 59 files is still too many. Do not tune it further
   from a chair - the previous estimate of what mattered was wrong twice.
