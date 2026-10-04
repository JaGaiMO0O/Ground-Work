# T01 - Keep context/tasks/ out of every project made from the template

Status: ready
Wave: 1
Depends on: T00
Build: build-0.1A

## Goal

Neither `init.py --adopt` nor plain `init.py` carries `context/tasks/` into
somebody else's project.

## Why

`context/tasks/` is Ground Work's own work log. Today `scripts/_adopt.py`
copies all of `context/`, so the next adoption would ship these task files into
the target - the fourth instance of "the repo ships its own content into another
project" (STATUS, handoffs and ADRs were the first three, fixed by rule 4 in
`_adopt.py`'s docstring). Plain `init.py` removes template-only paths through
`TEMPLATE_ONLY_DIRS` (`scripts/init.py:49`), which is currently empty.

## Files you may change

- `scripts/_adopt.py`
- `scripts/init.py`
- `tests/adopt.py`
- `context/tasks/T01-tasks-dir-stays-home.md` - Report section and Status line only

## Do exactly this

1. `scripts/_adopt.py`: add a constant `SKIP_ON_ADOPT_PATHS = {"context/tasks"}`
   next to `SKIP_ON_ADOPT_DIRS`, with a one-line comment that it must match
   `TEMPLATE_ONLY_DIRS` in `init.py`. In `travels()`, return `False` for any path
   equal to, or under, an entry in that set.
2. `scripts/init.py:49`: set `TEMPLATE_ONLY_DIRS = ("context/tasks",)`, with a
   one-line comment that it must match `SKIP_ON_ADOPT_PATHS` in `_adopt.py`.
   Check that the code at `init.py:77-78` handles a nested path such as
   `context/tasks` - `ROOT / "context/tasks"` - and fix it within this function if
   it does not.
3. `tests/adopt.py`: extend the existing `no_live_content` assertion so it also
   fails if any path under `context/tasks/` reaches the target. The repo will have
   real files there by the time this runs, so this is a live test, not a
   hypothetical.

## Do not

- Move or merge `TEMPLATE_ONLY_*` and `SKIP_ON_ADOPT_*` into one shared module.
  Two cross-referenced constants are acceptable for now.
- Touch `context/handoffs/` or `docs/decisions/` handling - rule 4 already
  covers those.

## Acceptance criteria

- [ ] An adoption from this repo produces no `context/tasks/` in the target.
- [ ] Plain `init.py` on a fresh copy deletes `context/tasks/`.
- [ ] `no live content travels` case fails if the exclusion is removed - check
      this by temporarily reverting step 1, running the case, then restoring.
- [ ] adopt suite: 22/22.

## Verify

```bash
python tests/adopt.py --only "no live content"   # expected: 1/1 passed
python tests/adopt.py                             # expected: 22/22 passed
python scripts/check.py                           # expected: exit 0

# Plain init on a throwaway copy (outside the repo):
#   copy the tracked files to a temp dir, run
#   python scripts/init.py --project t --profile general --purpose p --done d
#   then confirm context/tasks/ is gone. Record the commands and result.
```

## Commit

```
fix(T01): keep context/tasks out of new projects
- Skip it on --adopt and delete it on plain init
- Assert it in the no-live-content adopt case
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit:

**What changed**

**Verify output**

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
