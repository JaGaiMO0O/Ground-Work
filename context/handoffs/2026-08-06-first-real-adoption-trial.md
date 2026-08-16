# Handoff 2026-08-06 - first real adoption trial

**Goal:** test Ground Work against a real project rather than a fixture, and find
out what breaks.

**Subject:** `Desktop/dry-bean classification/misc/dry-bean-classification` - a
20-file ML project. Chosen because `usage.py` showed it as the worst re-read case
on this machine. Tested on a **copy**: the original is not a git repo, so
adoption there would have had no undo.

## Baseline, before adoption

Recorded so the "after" has something to compare against. From
`usage.py --path "Desktop/dry-bean classification"`:

| Measure | Value |
|---|---|
| Orientation share | **33%** (292 orienting / 566 working) |
| Files re-read in 3+ separate sessions | 41 |
| Worst | `train.py`, `preprocess.py`, `evaluate.py`, `app.py`, `README.md`, `requirements.txt` - 10 sessions each |
| Peak session | 528k per turn, 11.7x growth |
| Starting context | 45k median |

Note the sessions ran from the **parent** directory; the project has since been
moved into `misc/`, so those recorded paths no longer resolve. Any future
measurement taken from the project's new location starts a separate transcript
history - compare against the numbers above by hand, not by re-running.

**Done:**

- Adoption is genuinely non-destructive: **0 pre-existing files modified**.
- Detection correct: python, `install: pip install -r requirements.txt` from
  `requirements.txt`. `data/` and `models/` correctly excluded from areas.
- `check.py` runs in the adopted project and exits 2 with two accurate warnings.
- Two bugs found and fixed during the trial (see below).

## Bugs found and fixed

**`usage.py` could not look at another project.** It reported on the directory it
lived in, so a project could not be baselined *before* adoption - the one moment
the baseline matters. Added `--path`.

**POSIX paths recorded by git-bash were unresolvable.** Transcripts from a
git-bash session record `/c/Users/...`; Windows Python resolves that to
`C:\c\Users\...`, which does not exist. Every file lookup silently failed, so
costable text files degraded to `?` and the headline **understated** waste - 23k
reported against an actual 128k. Fixed with `native_path()` in
`scripts/_transcripts.py`. Same trap as the `guard.py` `cwd` bug: a path style
this OS cannot resolve, failing silently rather than loudly.

## Open - the real finding

**The scaffold is far too heavy for a small project.** A 20-file project became
115 files. The scaffold is 95 files, 4.75x the thing it describes.

| Directory | Files | Needed by this project? |
|---|---|---|
| `scripts/` | 44 | partly - 20 of them are `.sh`/`.ps1` shims preserving old names, and ~7 are adapters it will never call |
| `profiles/` | 15 | **no** - it is a `general` project |
| `.claude/` | 8 | yes |
| `context/` | 7 | yes |
| `docs/` | 6 | partly |
| `tests/` | 3 | no - they test the scaffold, not this code |
| `map/`, `interfaces/` | 2 | yes |

The genuinely useful part is roughly 15 files. The rest is tooling the project
will never invoke.

**Three fixes, smallest first:**

1. **`--adopt` does not prune unused profiles, but plain `init.py` does.** A
   straight inconsistency, and 15 of the 95 files. Small fix in `init.adopt()`.
2. **`--adopt` should skip the `.sh`/`.ps1` shims and unused adapters.** They
   exist to preserve names from the original legacy playbook; a Python project
   has no use for them. Either a `--minimal` flag or make it the adopt default.
3. **Reconsider copy-per-project entirely.** Even pruned this is heavy, and it
   creates two divergent copies of every script - a fix in the adopted project
   does not reach Ground Work. A shared install that projects reference would
   avoid both problems. That is an ADR-level decision, not a patch.

**Also:** `app/app.py` was not proposed as an area, because `propose_areas`
requires 2+ code files in a directory. A single-file serving layer is a real
area. Either lower the threshold or scale it to project size.

**Key files:** `scripts/_adopt.py` (`propose_areas`, `scaffold_plan`),
`scripts/init.py` (`adopt()`), `scripts/_transcripts.py` (`native_path`).

**Gotcha:** the trial subject had **no git repo**, which removed the undo path
the adoption advice assumes (`git clean -fd` after a clean-tree commit). Check
for `.git` before adopting anything, and copy first if it is absent. `--adopt`
warns about churn ranking being unavailable but does not warn that there is no
way back - it should.

**Next:**

1. Fix 1 and 2 above, then re-run this trial and see what 95 drops to.
2. Decide 3 - shared install vs copy - and write it up as ADR 0003.
3. Only then adopt into the real project. It needs `git init` first.
