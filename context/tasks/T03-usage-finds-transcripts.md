# T03 - Make usage.py find a project's transcripts from any path

Status: accepted
Wave: 2
Depends on: T00, T02
Build: build-0.1A

## Goal

`usage.py` (and `status.py`'s budget line) finds the Claude Code transcripts for
a project whatever characters its path contains, on Windows, macOS and Linux.

## Why

`usage.py` is the instrument that will measure the rollout - the only thing that
can close the "premise unmeasured" blocker. If it misses transcripts it reports
"no telemetry" or an understated number, which reads as good news. That is the
`native_path` failure class again.

- `scripts/_transcripts.py:73-78` `_slug()` replaces only `: \ / space .`.
  Claude Code replaces **every** non-alphanumeric character. Observed on this
  machine: `Desktop/RedKeys/Name_Screening` is stored as
  `C--Users-myaghmour-Desktop-RedKeys-Name-Screening`. Any path with `_ ( ) @ + ~`
  misses the exact match.
- `_slug()` calls `path.resolve()`, which follows symlinks. Claude Code records the
  logical working directory. On macOS `/tmp` resolves to `/private/tmp`, and
  iCloud-synced Desktops resolve elsewhere, so the slug never matches.
- The fallback in `project_dirs_for` (`:161-185`) compares against
  `cwd.resolve()` too, and `break`s after the **first** `.jsonl` in each folder.

## Files you may change

- `scripts/_transcripts.py` - `_slug()` and `project_dirs_for()` only
- `tests/hooks.py`
- `context/tasks/T03-usage-finds-transcripts.md` - Report section and Status line only

## Do exactly this

1. `_slug(path)`: return `re.sub(r"[^A-Za-z0-9]", "-", str(path))` on the path
   **as given** - no `resolve()` inside it. Update its docstring to say this is
   the observed Claude Code rule, and cite the `Name_Screening` example.
2. `project_dirs_for(cwd)`:
   - Build the candidate list: `cwd.absolute()`, then `cwd.resolve()` if it
     differs.
   - Try the exact slug of each candidate, in that order; return the first that
     exists as a directory.
   - In the fallback, compare each recorded `cwd` - passed through the existing
     `native_path()` - against **every** candidate, case-insensitively, with
     `\` and `/` treated as equal.
   - Look at up to **5** `.jsonl` files per folder, stopping at the first one
     that yields a recorded `cwd`, instead of only the first file.
3. `tests/hooks.py`: add a `SLUG_CASES` list of `(input, expected)` pairs, run
   after the existing hook cases, one printed line per case in the same format,
   counted in the final `N/M passed` total:
   - `C:\Users\me\Desktop\RedKeys\Name_Screening` -> `C--Users-me-Desktop-RedKeys-Name-Screening`
   - `C:\Users\me\Desktop\Legacy Modernization` -> `C--Users-me-Desktop-Legacy-Modernization`
   - `/home/me/my_proj (copy)` -> `-home-me-my-proj--copy-`
4. Run the **real-data check** below and paste its output into Report.

## Do not

- Change anything else in `_transcripts.py` - not the schema touch points, not
  `native_path()`, not `read_dirs()`.
- Change `usage.py` or `status.py`.
- Add `CLAUDE_CONFIG_DIR` support (deferred).

## Acceptance criteria

- [ ] `_slug()` maps every non-alphanumeric character to `-` and never resolves.
- [ ] The real-data check reports every transcript folder on this machine
      matching, or lists each mismatch with its recorded `cwd`.
- [ ] hooks suite: **26/26** (23 after T02, plus 3).
- [ ] `python scripts/usage.py --all` still runs and reports the same session
      count as before your change.

## Verify

```bash
python tests/hooks.py               # expected: 26/26 passed
python scripts/usage.py --all | head -6   # note the session count before AND after

# Real-data check - every folder's own recorded cwd must slug to its own name:
python - <<'EOF'
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
import _transcripts as tx
ok = bad = 0
for d in sorted(tx.PROJECTS_DIR.iterdir()):
    if not d.is_dir():
        continue
    cwd = next((c for j in list(d.glob("*.jsonl"))[:5] if (c := tx._peek_cwd(j))), None)
    if cwd is None:
        print("no cwd  ", d.name); continue
    got = tx._slug(tx.native_path(cwd))
    if got == d.name: ok += 1
    else: bad += 1; print("MISMATCH", d.name, "<-", cwd, "->", got)
print(f"{ok} match, {bad} mismatch")
EOF
```

## Commit

```
fix(T03): find transcripts on any path
- Slug every non-alphanumeric, as Claude Code does
- Try the logical path before the resolved one
- Fallback checks up to 5 transcripts per folder
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: the single `fix(T03)` commit on branch `T03-usage-finds-transcripts`
(this Report is part of that commit, so it cannot hold its own hash. The hash
went to the user.)

**What changed**

- `scripts/_transcripts.py` `_slug()`: `re.sub(r"[^A-Za-z0-9]", "-", str(path))`
  on the path as given, with no `resolve()`. The docstring states the observed
  rule and cites `Name_Screening`.
- `scripts/_transcripts.py` `project_dirs_for()`: candidates are `cwd.absolute()`,
  then `cwd.resolve()` if it differs. The exact slug of each is tried in that order.
  The fallback passes each recorded `cwd` through `native_path()` and compares it
  against every candidate, case-insensitively, with `\` equal to `/`. It reads up
  to 5 `.jsonl` per folder and stops at the first one that yields a `cwd`.
- `tests/hooks.py`: `SLUG_CASES` (3 cases) runs after the wiring cases, in the
  same print format, and counts toward the total. `_transcripts` is imported via
  `sys.path` from `scripts/`.
- Nothing else in `_transcripts.py` changed. `usage.py` and `status.py` are untouched.

**Verify output** (include the real-data check output in full)

Setup: the app created this worktree from `1a79a04`, which is older than `main`
and has no `context/tasks/`. The branch had no commits, so I ran
`git merge --ff-only main` (to `d0c3f9f`) before starting. After that, T00 and
T02 showed `Status: accepted`.

`python tests/hooks.py` (Windows, Python 3.12.10, Git Bash):
baseline before the change was `23/23 passed`. After:

```
hook wiring: read .env              exit 2  exit 2  ok  [bash: C:\Program Files\Git\bin\bash.exe]
hook wiring: read README.md         exit 0  exit 0  ok  [bash: C:\Program Files\Git\bin\bash.exe]
slug: C:\Users\me\Desktop\RedKeys\Name_Screening C--Users-me-Desktop-RedKeys-Name-Screening C--Users-me-Desktop-RedKeys-Name-Screening  ok
slug: C:\Users\me\Desktop\Legacy Modernization C--Users-me-Desktop-Legacy-Modernization C--Users-me-Desktop-Legacy-Modernization  ok
slug: /home/me/my_proj (copy)      -home-me-my-proj--copy- -home-me-my-proj--copy-  ok
------------------------------------------------------------------
26/26 passed
```

`python scripts/usage.py --all | head -6`, before and after are identical:

```
  136 session(s) across 41 project(s)   [137 transcript file(s) read]
```

Real-data check, full output:

```
no cwd   C--Users-myaghmour-Downloads-OptimizaIPsHub
41 match, 0 mismatch
```

The `no cwd` folder holds only a `memory/` directory and no `.jsonl`, so there is
no transcript to match. It is not a mismatch.

Extra spot check (not in Verify): `project_dirs_for()` returns this worktree's
folder for `Path.cwd()` and for `Path(".")`, and returns the main checkout's
folder for `C:/Users/myaghmour/Desktop/Legacy Modernization`. With the exact
slug forced to miss, the fallback still finds this worktree's folder.

`python scripts/check.py`: `ok   all invariants hold`.

**Deviation requests**

None. The `--ff-only` sync to `main` was branch setup, not a file change. No file
outside the list was touched.

**Found, not fixed**

- Worktree base: the app started this wave-2 worktree from `1a79a04`, not from
  `main` (`d0c3f9f`). Other wave-2 worktrees may have the same stale base. For
  example, `T05-check-enforces-card-contracts` also showed `1a79a04` in
  `git worktree list`.
- `tests/hooks.py` print format: the `got`/`want` columns are 7 characters wide,
  so the long slug values overflow them and the slug rows do not line up. The
  output is cosmetic only; the pass/fail result is correct.
- `scripts/_transcripts.py` `project_dirs_for()` fallback: `candidate.glob("*.jsonl")`
  is unsorted, so which 5 files are checked depends on filesystem order. The
  brief did not ask for sorting, so I left it as written.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Fast-forwarded into `main` as `92337a7`. Branch `T03-usage-finds-transcripts`, built on `main`
(`d0c3f9f`) after the worker's own fast-forward.

- Gate: hooks 26/26.
- *Found, not fixed*: the stale worktree base is now protocol step 1. The
  slug column width and the unsorted fallback glob are deferred - cosmetic,
  and negligible in practice.
