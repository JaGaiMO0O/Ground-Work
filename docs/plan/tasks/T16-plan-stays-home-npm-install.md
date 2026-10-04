# T16 - Keep docs/plan/ out of new projects; null scripts keep npm install

Wave: 4
Lane: Adoption
Depends on: T10
Estimate: S (~30 min)
Build: build-0.1A

## Goal

Neither `init.py --adopt` nor plain `init.py` carries `docs/plan/` into a project
made from the template, and a `package.json` whose `"scripts"` is `null` still
gets an install command.

## Why

- **The move created a leak (lead-caused, 2026-10-04).** Ground Work's own plan -
  roadmap, decisions, briefs - moved from `context/tasks/` to `docs/plan/` (D-09).
  The exclusions T01 added still name `context/tasks`:
  `SKIP_ON_ADOPT_PATHS` in `scripts/_adopt.py` and `TEMPLATE_ONLY_DIRS` in
  `scripts/init.py`. That path no longer exists, and `docs/` is on adoption's copy
  list - so `docs/plan/` now travels into every adopted project and survives plain
  `init.py`. The fifth "the repo ships its own content into somebody else's
  project" defect.
- **A regression the T10 brief caused.** T10 step 6 said a `package.json` whose
  `scripts` is not an object yields no commands. With `"scripts": null` that now
  drops the **install** command too, but install comes from the lockfile, not from
  `scripts`. Found by T10's worker.

## Owns

- `scripts/_adopt.py` - `SKIP_ON_ADOPT_PATHS`, and the `package.json` branch of `detect()`
- `scripts/init.py` - `TEMPLATE_ONLY_DIRS` and the code that applies it **only**.
  T11 owns the adopt "Next" message block of the same file in this wave.
- `tests/adopt.py`
- `README.md` - the one line naming what `init.py` deletes
- `TESTING.md` - the one post-init expectation naming `context/tasks/`
- `docs/plan/tasks/T16-plan-stays-home-npm-install.md` - Handoff only

## Scope - do exactly this

1. `scripts/_adopt.py`: `SKIP_ON_ADOPT_PATHS = {"docs/plan"}`, replacing
   `context/tasks`. Keep the comment that it must match `TEMPLATE_ONLY_DIRS`.
2. `scripts/init.py`: `TEMPLATE_ONLY_DIRS = ("docs/plan",)`, replacing
   `context/tasks`. Keep the cross-reference comment, and update the comment
   above it (`init.py:48`) so it names `docs/plan/`.
3. `tests/adopt.py`, `no_live_content`: assert that nothing under `docs/plan/`
   reaches the target, **in place of** the `context/tasks/` assertion - that path
   no longer exists, so asserting on it proves nothing. This retargets an
   assertion at the lead's instruction; say so in the Handoff.
4. `scripts/_adopt.py`, `package.json` branch: when `scripts` is not an object,
   still set `install` from the lockfile exactly as today (`npm ci`, `yarn
   install` or `pnpm install`) and record the source; skip only the
   scripts-derived commands. When the whole file is not an object, keep T10's
   behaviour (no commands).
5. `tests/adopt.py`: add the case **package.json null scripts keeps install** -
   `package.json` = `{"name": "x", "scripts": null}`; assert the target's
   `project.yaml` has `  install: npm ci`.
6. `README.md`: the list of what `init.py` deletes names `docs/plan/` in place of
   `context/tasks/`.
7. `TESTING.md`: the post-init expectation names `docs/plan/` in place of
   `context/tasks/`.

## Do not

- Touch `init.py`'s adopt "Next" message - T11's block.
- Change any other detection branch, or `travels()` beyond the constant.

## Acceptance criteria

- [ ] `no live content travels` fails if the `docs/plan` exclusion is removed -
      check by reverting step 1 briefly - and passes with it.
- [ ] The new case fails before step 4 and passes after.
- [ ] Plain `init.py` on a fresh copy deletes `docs/plan/`.
- [ ] Adopt suite **32/32** (31 + 1); `check.py` exits 0.

## Verify

```bash
python tests/adopt.py --only "no live content"   # expected: 1/1 passed
python tests/adopt.py --only "null scripts"      # expected: 1/1 passed
python tests/adopt.py                            # expected: 32/32 passed
python scripts/check.py                          # expected: exit 0
# Plain init on a throwaway copy outside the repo: copy the tracked files, run
#   python scripts/init.py --project t --profile general --purpose p --done d
# and confirm docs/plan/ is gone. Record the commands and result.
```

## Commit

```
fix(T16): keep docs/plan out of new projects

- docs/plan replaces context/tasks in both exclusions
- package.json with null scripts keeps install
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit:

**What changed**

**How it was verified**

**Deviations** (escalations raised, and the answers)

**Follow-ups** (found, not fixed - file and line)

**Rollback**

---

## Lead review

<!-- Lead only. -->
