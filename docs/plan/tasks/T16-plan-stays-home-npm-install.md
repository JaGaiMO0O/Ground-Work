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

Branch / commit: `task/T16-plan-stays-home-npm-install`, one commit
`fix(T16): keep docs/plan out of new projects` (hash reported to the user;
a commit cannot name its own hash).

**What changed**

- `scripts/_adopt.py:73` - `SKIP_ON_ADOPT_PATHS = {"docs/plan"}`; the
  "must match TEMPLATE_ONLY_DIRS" comment kept.
- `scripts/init.py:48-50` - `TEMPLATE_ONLY_DIRS = ("docs/plan",)`; comment above
  names `docs/plan/`, cross-reference comment kept. The code that applies it
  (`template_only_paths()`, the rmtree loop) is generic and needed no change.
  T11's adopt "Next" block untouched.
- `scripts/_adopt.py` `detect()`, `package.json` branch - gated on "the file is a
  JSON object" instead of "`scripts` is an object". Install is set from the
  lockfile as before (`npm ci` / `yarn install` / `pnpm install`); a non-object
  `scripts` becomes `{}`, so only the scripts-derived commands are skipped.
  `package.json` is still recorded in `sources` (unchanged line above). A
  top-level array still yields no commands (T10's case still passes).
- `tests/adopt.py` `no_live_content` - **assertion retargeted at the lead's
  instruction (brief step 3):** the `context/tasks/` check is replaced by a
  `docs/plan/` check. The old path no longer exists, so the old assertion could
  not fail. Not a weakening: the new one fails on today's leak (see below).
- `tests/adopt.py` - new case `package.json null scripts keeps install`
  (`{"name": "x", "scripts": null}` -> `  install: npm ci`).
- `README.md:78`, `TESTING.md:106` - `context/tasks/` -> `docs/plan/`.

**How it was verified**

- Baseline before any change: `check.py` all invariants hold; adopt 31/31.
- Test first: with only the test edits, `--only "no live content"` failed
  (`our plan travelled: ['docs/plan/DECISIONS.md', ...]`) and
  `--only "null scripts"` failed (`project.yaml has no 'install: npm ci' line` -
  install came from requirements.txt instead).
- After the fix: both 1/1; `--only "package.json array"` 1/1.
- Revert check: step 1 set back to `{"context/tasks"}` -> `no live content`
  0/1 with the same leak message; restored -> passes.
- `python tests/adopt.py` -> 32/32. `python scripts/check.py` -> exit 0.
- Plain init on a throwaway copy outside the repo (scratchpad): copied
  `git ls-files` into it, ran
  `python scripts/init.py --project t --profile general --purpose p --done d`
  -> `ok removed template-only file(s): LICENSE, TESTING.md, docs/plan/`;
  `docs/plan` no longer exists; `docs/` keeps adapters.md, antipatterns.md,
  decisions/, playbook.md, starter-prompt.md.

**Deviations** (escalations raised, and the answers)

- None escalated. One side effect of re-gating the branch: with a non-object
  `scripts`, a `tsconfig.json` now sets `stack.typed: typescript` (before, the
  null-scripts case skipped it along with install). It sits inside the
  `package.json` branch this task owns and is not a command; flagging it for
  review rather than adding a second condition to preserve the old skip.

**Follow-ups** (found, not fixed - file and line)

- None.

**Rollback**

`git revert <T16 commit>` (or the `--no-ff` merge commit with `-m 1`). It
restores `context/tasks` in both constants, so `docs/plan/` leaks again, and
`"scripts": null` drops install again. Self-contained: no data, no migration,
no other task depends on the new constants.

---

## Lead review

<!-- Lead only. -->
