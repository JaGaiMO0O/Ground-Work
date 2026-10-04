# T01 - Only template files travel: ask git, and keep context/tasks/ home

Wave: 1
Depends on: T00
Build: build-0.1A

## Goal

Adoption, and the invariant harness's copy of the repo, take their file list
**from git** - tracked files plus untracked-but-not-ignored ones - instead of
walking the disk. And `context/tasks/` never reaches a project made from the
template, by `--adopt` or by plain `init.py`.

## Why

**Found at the wave-0 gate (2026-10-04).** Claude Code puts worker worktrees in
`.claude/worktrees/` *inside* this repo. Git ignores them (through
`.git/info/exclude`), so `git status` is clean - but `_adopt.scaffold_plan()`
walks the filesystem. An adoption from `main` with one live worktree planned
**188 files, 124 of them a complete copy of the worktree**; the adopt suite
failed on `main` (`legacy scaffold reaches root`, 199 files added) and the
invariant suite took 150s instead of ~46s, because `build_pristine()`
(`tests/invariants.py`) `copytree`s the whole repo too. The same walk would carry
any gitignored local file - a developer's `.claude/settings.local.json` - into
somebody else's project.

This is the "ask the environment, don't assume it" defect class a fifth time:
the template is what git says it is, not whatever happens to be on disk.

Separately, `context/tasks/` is Ground Work's own work log and **is** tracked, so
the git listing alone will not exclude it. Adoption copies all of `context/`;
plain `init.py`'s `TEMPLATE_ONLY_DIRS` (`scripts/init.py:49`) is empty. Shipping
it would be the fourth "repo ships its own content into another project" defect.

## Files you may change

- `scripts/_lib.py` - one new function, see step 1
- `scripts/_adopt.py`
- `scripts/init.py` - `TEMPLATE_ONLY_DIRS` and the code that applies it only
- `tests/adopt.py`
- `tests/invariants.py` - `build_pristine()` only
- `.gitignore` - one line
- `context/tasks/T01-tasks-dir-stays-home.md` - Report section and Status line only

## Do exactly this

1. **`scripts/_lib.py`**: add `template_files(root) -> list[Path]`, returning
   paths relative to `root`. If `root` is in a git work tree, run
   `git ls-files -z --cached --others --exclude-standard` there (bytes, `-z`,
   split on `\0` - see the newline-translation gotcha in
   `context/handoffs/2026-08-26-adoption-undo-by-manifest.md`), drop any path that
   no longer exists on disk (deleted but not yet committed), and return the rest.
   Otherwise - a template downloaded as a zip has no git - fall back to walking
   the directory. Docstring: why, citing the worktree finding.
2. **`scripts/_adopt.py`**:
   - `import _lib as lib`.
   - In `scaffold_plan()`, build the candidate files from `lib.template_files()`
     filtered to the `include` list, instead of `rglob`. Every existing filter
     (`NOISE`, `examples`, `travels()`, `destination_for()`) still applies on top.
   - Add `SKIP_ON_ADOPT_PATHS = {"context/tasks"}` next to `SKIP_ON_ADOPT_DIRS`,
     with a comment that it must match `TEMPLATE_ONLY_DIRS` in `init.py`, and
     make `travels()` return `False` for anything equal to or under an entry.
3. **`scripts/init.py`**: `TEMPLATE_ONLY_DIRS = ("context/tasks",)`, with a
   comment that it must match `SKIP_ON_ADOPT_PATHS` in `_adopt.py`. Check the code
   at `:77-78` handles a nested path; fix it within that code if not.
4. **`tests/invariants.py`**: `build_pristine()` copies the files listed by
   `_lib.template_files(REPO)` (import `_lib` from `scripts/`) into `PRISTINE`,
   instead of `copytree(REPO, ...)`. Keep excluding `systems/`.
5. **`.gitignore`**: add `.claude/worktrees/`, so the exclusion holds on every
   machine, not only where the app wrote `.git/info/exclude`.
6. **`tests/adopt.py`**:
   - Add a helper that runs a **given** template's `scripts/init.py` (T06 will
     reuse it - name it clearly, e.g. `run_template_init(template, target, *argv)`).
   - Extend `no_live_content` so it also fails if anything under `context/tasks/`
     reaches the target.
   - Add a case **only git's files travel**, harness argv `["--help"]` (makes the
     harness's own run a no-op). The assertion builds a throwaway template: copy
     this repo's `template_files()` into a temp dir, `git init`, commit. Then plant,
     *after* the commit:
     - `.claude/worktrees/w1/scripts/check.py` and `.claude/settings.local.json`,
       both listed in that template's `.git/info/exclude`;
     - `docs/new-note.md`, untracked and **not** ignored.
     Adopt from that template into a fresh `make(...)` target. Assert: no path
     containing `worktrees`, no `settings.local.json`, and `docs/new-note.md`
     present.

## Do not

- Change `scan.py` - a secret scanner *should* read untracked files.
- Change what `travels()` already excludes, or the manifest.
- Merge `TEMPLATE_ONLY_*` and `SKIP_ON_ADOPT_*` into one constant.

## Acceptance criteria

- [ ] The new case fails before your change (worktree and local settings travel)
      and passes after - say so in Report.
- [ ] `no live content travels` fails if the `context/tasks` exclusion is removed -
      check by reverting it briefly.
- [ ] Adopt suite **23/23** (22 + 1); invariants **39/39**.
- [ ] Plain `init.py` on a fresh copy deletes `context/tasks/`.
- [ ] From `main` with a live worktree present, a dry-run adoption plans no file
      under `.claude/worktrees/` (the lead re-runs this at the gate).

## Verify

```bash
python tests/adopt.py --only "git's files"       # expected: 1/1 passed
python tests/adopt.py --only "no live content"   # expected: 1/1 passed
python tests/adopt.py                             # expected: 23/23 passed
python tests/invariants.py                        # expected: 39/39 passed
python scripts/check.py                           # expected: exit 0
# Plain init on a throwaway copy outside the repo: copy the tracked files, run
#   python scripts/init.py --project t --profile general --purpose p --done d
# and confirm context/tasks/ is gone. Record the commands and result.
```

## Commit

```
fix(T01): only template files travel
- Template file list comes from git, not the disk
- Worktrees and ignored local files stay home
- context/tasks never reaches a new project
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: see `git log` on branch `claude/serene-gauss-1d3d24` (`fix(T01): only template files travel`)

**What changed**

- `scripts/_lib.py`: `template_files(root)` - `git ls-files -z --cached --others
  --exclude-standard` as bytes, split on `\0`, drops paths not on disk, sorted
  and de-duplicated; falls back to `rglob` when `root` is not in a git work tree.
- `scripts/_adopt.py`: `import _lib as lib`; `scaffold_plan()` takes candidates
  from `lib.template_files(template)` filtered by top-level `include` name
  (`rel.parts[0] == name`), all existing filters unchanged on top;
  `SKIP_ON_ADOPT_PATHS = {"context/tasks"}`, honoured in `travels()` for the path
  itself and anything under it.
- `scripts/init.py`: `TEMPLATE_ONLY_DIRS = ("context/tasks",)`. The code at
  `:77-78` already handles a nested path (`(ROOT / n).is_dir()`), no change.
- `tests/invariants.py`: `build_pristine()` copies `_lib.template_files(REPO)`
  file by file, still skipping `systems`, `.git`, `__pycache__`.
- `.gitignore`: `.claude/worktrees/`.
- `tests/adopt.py`: `run_template_init(template, target, *argv)` (`run_init` now
  delegates to it); `no_live_content` fails on any `context/tasks/` path; new
  case `only git's files travel` (throwaway git template, plants an excluded
  worktree file, excluded `settings.local.json`, untracked `docs/new-note.md`;
  adopts into fresh `make(99, ...)`).

**Verify output**

- Before the `_adopt.py` change, with `_lib.template_files` and the test in place:
  - `--only "git's files"` -> 0/1, `an ignored worktree travelled:
    ['.claude/worktrees/w1/scripts/check.py']`; with `--keep`, the target's
    `.claude/` also held `settings.local.json` and `worktrees/`.
  - `--only "no live content"` -> 0/1, `our task log travelled:
    ['context/tasks/README.md', ...]`.
- After:
  - `python tests/adopt.py --only "git's files"` -> 1/1 passed
  - `python tests/adopt.py --only "no live content"` -> 1/1 passed
  - `python tests/adopt.py` -> 23/23 passed in 76s
  - `python tests/invariants.py` -> 39/39 passed in 94s
  - `python scripts/check.py` -> exit 0
- Revert check: `SKIP_ON_ADOPT_PATHS = set()` briefly -> `no live content
  travels` fails with `our task log travelled: [...]`; restored, diff clean.
- Plain init: copied `_lib.template_files(.)` (130 files) to a scratch dir
  outside the repo, ran `python scripts/init.py --project t --profile general
  --purpose p --done d` -> exit 0, printed `removed template-only file(s):
  LICENSE, TESTING.md, context/tasks/`; `context/` left with `glossary.md`,
  `handoffs`, `recipes` only.
- Live-worktree plan: `_adopt.scaffold_plan(<main checkout>, <dummy target>)`
  with 4 live worktrees in `.claude/worktrees/` -> 47 planned, 0 under
  `worktrees`, 0 under `context/tasks`. Same 47 as planning from this worktree.
  The old `rglob` plan minus worktrees was 64; the 17 difference is exactly the
  `context/tasks/` files (incl. `_TEMPLATE.md`).

**Deviation requests**

None.

**Found, not fixed**

- `scripts/init.py:762-763`: the message after removing template-only paths
  says "licence and testing brief are yours to write", which no longer
  describes everything removed now that `context/tasks/` is in the list.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Fast-forwarded into `main` as `0d8a02a`. Branch renamed from `claude/...` to
`T01-tasks-dir-stays-home`.

- Proven both ways, as asked: the planted worktree and the task log travel
  before the change and not after.
- **Wave-1 gate on `main` with five worktrees live: adopt 23/23.** At the
  wave-0 gate the same setup failed with 199 files copied. Root cause fixed.
- *Found, not fixed* (stale init.py message) -> T06 step 7.
