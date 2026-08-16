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

## Choosing the second trial subject

Surveyed at the end of this session, because the plan assumed a project existed
that could test both halves at once. None does.

**Only two projects on this machine have real session history:** Playground (13
sessions) and dry bean (12). Everything else has one or three. Playground is 10
files with no git. So `usage.py`'s re-read analysis - the flagship metric, and
the only one that needs history to mean anything - can currently be re-run
against **dry bean and nothing else**.

Name Screening exists in three copies, and they split the two properties the
trial needs:

| Copy | Files | git | Sessions |
|---|---|---|---|
| `Desktop/RedKeys/Name_Screening` | 93 | **no** | 1 |
| `Desktop/dry-bean classification/Maya/name-screening` | 83 | yes, 4 commits, clean | 0 |
| `Desktop/Name_Screening` | 52 | yes, 1 commit | 0 |

Baselined the one with history anyway: 95% cache, 49k starting context, 29%
orientation, peak 158k over 115 turns. Re-reads read "nothing in 3+ separate
sessions", which with one session is **structurally unavailable, not zero** -
exactly the distinction `_transcripts.py` exists to preserve, and worth checking
that a reader of that line understands it.

**So the two halves are now separate trials.** Adoption mechanics go to Name
Screening; the measurement re-run stays on dry bean.

### Dry run against Maya's clone - nothing written

```
areas     sota_screening, src, my_name_screening, tests, web
scaffold: 53 added
```

Three findings, none of them predicted:

- **53 scaffold files against 83 project files - 0.64x, against 4.75x on dry
  bean.** The weight complaint that prompted ADR 0003 looks like a *small
  project* problem rather than a general one. Not yet written into the ADR: one
  dry run is not a measurement, and it should be confirmed on a real adopt.
- **`web/` was proposed and holds exactly one code file** (`app.js`; `.html` and
  `.css` are not in `CODE_SUFFIXES`). First confirmation from a real repository
  that dropping the two-file threshold does what it was meant to.
- **The ranking is backwards here, and the reason generalises.**
  `my_name_screening` - the thing the project is actually about - ranks third,
  behind the reference implementation nobody is editing. With 4 commits of
  history, churn is nearly flat, so size decides, and the largest directory is
  the dead one. Churn ranking needs more history than a young repo has. The
  output does say the areas are a guess, so this is a heuristic limit rather
  than a defect - but it is the first case seen where a reader following the
  advice would card the wrong area first.

**Next:**

1. **Adoption mechanics - Name Screening.** Adopt into a *copy* of
   `Maya/name-screening`, not the clone: it is on her branch with her remote,
   and 53 files in that working tree is noise the next `git pull` will meet.
   Watch whether `check.py` stays sane with five declared areas, and whether the
   ranking above misleads.
2. **Measurement - dry bean.** Unchanged and still the only subject for it.
   `git init` it, adopt for real, card `src/`, leave it a week, then re-measure
   against the recorded baseline: 33% orientation, 41 files re-read across 3+
   sessions.
3. Only then decide whether 59 files is too many. Do not tune it further from a
   chair - the estimate of what mattered has been wrong twice, and the 0.64x
   above is the second time.
