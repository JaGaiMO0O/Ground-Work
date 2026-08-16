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

## Real adoption into Name Screening - done, and it found three defects

Target: `Desktop/Ground-Work-Tests/name-screening`, a copy of Maya's clone.

**Held up.** 64 pre-existing files hashed before and after; exactly one content
change, `.gitignore`, appended in a marked block. `check.py` sane with five
declared areas. Hooks resolve and fire from the adopted tree - `.env` read
blocked, `systems/` write blocked, ordinary edit silent. That is ADR 0003's
central claim, tested in the configuration the ADR chose. `usage.py` degraded to
"no transcript directory found" rather than a zero. The project's 4 pytest
collection errors are all pre-existing (missing `metaphone`/`rapidfuzz`, a
missing CSV, duplicate test basenames) - adoption broke nothing.

**Weight: 58 added against 64 existing - 0.91x.** Third data point, after 0.64x
on the dry run and 4.75x on dry bean. The weight complaint is a small-project
artefact. ADR 0003's "still too heavy" consequence can be revised on this
evidence, and should be.

### Defect 1 - the scaffold ships its own content as the project's content

**The worst of the three, and a regression from bf5af80.** Making the repo
describe itself meant adoption now copies real state where it used to copy a
template. Four artefacts, not one:

| Arrived carrying | Contents |
|---|---|
| `STATUS.md` | Ground Work's goal ladder. "Now" reads *"Adoption mechanics on a copy of `Maya/name-screening`"*; a listed blocker is this directory being named `Legacy Modernization` |
| `context/handoffs/` | All three dated handoffs, including this one - 120 lines about `propose_areas` and ADR 0003 |
| `docs/decisions/` | ADRs 0001-0003, including the one arguing about whether the scaffold should be copied at all |
| `AGENTS.md` | see defect 2 |

`AGENTS.md` routes to the first two as authoritative - STATUS.md for "where this
project stands", newest handoff for "what happened last session". So **the first
two files an agent reads describe a different project, confidently.** Every
principle this repo is built on is inverted at once: the map describes the wrong
territory, and it is the always-loaded tier that does it.

Fix: adoption must copy *templates*, never live content. A pristine
`STATUS.template.md`, `_TEMPLATE.md` from `context/handoffs/` and nothing dated,
and `docs/decisions/` seeded with its template only. The general rule worth
writing into `travels()`: **anything this project filled in about itself does not
travel.**

### Defect 2 - AGENTS.md arrives unpersonalized and nothing says to fix it

`<PROJECT_NAME>` and both `<ONE SENTENCE>` placeholders survive adoption. Plain
`init.py` substitutes them; `adopt()` never has. The "Next" list names
project.yaml, RUNBOOK.md, scan.py and usage.py - not AGENTS.md.

The deeper half: **`check.py` passes clean on it**, and reports "Tier 0 ~706
tokens of 1500 budget" on a file whose first four lines are placeholders. A
validator that measures an unfilled router and calls it well within budget is
measuring the wrong thing. Placeholders surviving in Tier 0 should be an error,
not silence - and that rule belongs in core, where it also guards plain `init`.

### Defect 3 - the advertised undo is wrong, both halves

The success message promises `git clean -nd` lists everything adoption added and
`-fd` removes it. False twice over:

- `.gitignore` was **modified**, and `git clean` never touches tracked files.
- `systems/.sync-state.json` sits under a path adoption's own `.gitignore` block
  just ignored - verified `.gitignore:53:systems/` - so plain `git clean -fd`
  skips it. It needs `-x`.

Note the trap in the obvious fix: `-fdx` also deletes venvs and `.env`. The
message must state what it does *not* cover rather than reach for a more
destructive flag. Written this session, wrong the same day - a claim about an
undo path is worth testing before printing it.

**Also:** `systems/.sync-state.json` is not reported at all. (The "53 added"
line is not undercounting - the generated files each get their own `ok` line.)

### Ranking misled again, as predicted

`sota_screening` (16 files) first, `my_name_screening` (10) third. Second
confirmed instance of a reader being pointed at the wrong area first. No longer
a prediction.

### Live hazard

That copy still carries Maya's `origin` and tracks
`origin/feature/phase1-normalization`. Nothing pushes on its own, but a `git
push` from that directory puts 58 scaffold files on her branch. Worth having
`--adopt` warn when the target's origin is not one you own - or at minimum, when
the target tracks a remote branch.

**Next:**

0. **Defects 1 and 2 first, before any further trial.** 1 is a regression that
   makes every adoption actively misleading; 2 is a one-line omission plus a
   missing core rule. 3 is a message and a report line. None is large.
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
