# T19 - Undo leaves nothing behind, and its printed command works

Wave: 7
Lane: Adoption
Depends on: T13
Estimate: S (~45 min)
Build: build-0.1A

**Must ship: it is the rollback path.**

## Goal

`init.py --undo` returns an adopted project to exactly the state it was in
before adoption, even after the user has run the scaffold's own `scan.py`, and
the undo command that adoption prints works when run as printed.

## Why

Found by T13 (2026-10-05), and verified by the lead on the hash listings:

- **F1:** adopt, then `scan.py` (step 4 of adoption's own "Next", `scripts/init.py:470`), then `--undo`
  leaves one stray file, `.secrets-baseline`. Undo neither removes it nor names
  it. Everything else round-trips byte-identical.
- **F2:** adoption prints `python scripts/init.py --undo {target.name}`
  (`scripts/init.py:444`), a bare folder name. Run as printed from the template
  folder, it fails: `<template>\jlgc6 is not a directory`.

## Owns

- `scripts/init.py` - the `undo()` function and the "If you want out" message
  block (`:441-446`) only
- `tests/adopt.py`
- `docs/plan/tasks/T19-undo-leaves-nothing.md` - Handoff only

## Scope - do exactly this

1. Write the tests first (step 4) and watch the first two fail.
2. **F2.** The printed undo line becomes
   `python scripts/init.py --undo "<absolute target path>"`, using the resolved
   target and double quotes (paths such as `JLGC - Copy` contain spaces).
3. **F1.** In `undo()`, after the manifest files are handled, deal with the two
   files `scan.py` writes at the target root: `.secrets-baseline` and
   `.secrets-baseline.raw.json`. For each one that exists:
   - **not tracked by git** in the target: remove it (unless `--dry-run`) and
     say so: `removed .secrets-baseline - written by scan.py, never committed`;
   - **tracked by git**: keep it and name it, under the existing `kept` warning
     style: `kept .secrets-baseline - it is committed; git rm it if you are
     backing out`.
   Test "tracked" with `git ls-files --error-unmatch <name>`. If the target has
   no git, treat the file as untracked.
4. `tests/adopt.py`, three new cases, each a new check function:

   | Case | Setup | Expect |
   |---|---|---|
   | undo after scan restores exactly | adopt; run the target's `scripts/scan.py`; undo | `paths_of` and `inventory` equal the before snapshot, as `undo_is_exact` tests |
   | printed undo command runs | adopt; take the `--undo` line from adoption's output; run it with the **template** as the working directory | exit 0; the target's paths equal the before snapshot |
   | committed baseline is kept `[+]` | adopt; scan; `git add .secrets-baseline` and commit; undo | `.secrets-baseline` still exists; undo output contains `kept .secrets-baseline` |

## Do not

- Change the manifest format, `scan.py`, or any other part of adoption.
- Remove any other file that adoption did not write.
- Change how existing cases assert. `undo_is_exact` keeps its no-scan setup.

## Acceptance criteria

- [ ] The first two new cases fail before steps 2-3 and pass after; say so in the Handoff.
- [ ] Adopt suite **35/35** (32 + 3).
- [ ] `check.py` exits 0; invariants 51/51; hooks 26/26; scan 8/8.
- [ ] By hand: the T13 round trip (clone any small repo, adopt, `scan.py`,
      the printed undo command) leaves `git status --short --ignored` empty.

## Verify

```bash
python tests/adopt.py          # expected: 35/35 passed
python tests/invariants.py     # expected: 51/51 passed
python scripts/check.py        # expected: exit 0
```

## Commit

```
fix(T19): undo leaves no scan baseline behind

- Remove an uncommitted .secrets-baseline; name a committed one
- Print the undo command with the full target path
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit: `task/T19-undo-leaves-nothing` - see `git log main..task/T19-undo-leaves-nothing`

**What changed**

- `scripts/init.py` "If you want out" block (`:444`): prints
  `python scripts/init.py --undo "<resolved target>"` - absolute, double-quoted.
- `scripts/init.py` `undo()` (`:552-572`, report `:610-613`): after the manifest
  files, checks `.secrets-baseline` and `.secrets-baseline.raw.json` at the
  target root. Untracked (or no git): removed (not under `--dry-run`), reported
  `removed <name> - written by scan.py, never committed` (`would remove` on a
  dry run). Tracked per `git ls-files --error-unmatch`: kept, warned
  `kept <name> - it is committed; git rm it if you are backing out`. If the
  unlink itself fails, it is kept and warned `kept <name> - it could not be
  removed` rather than mislabelled as committed. These files do not affect
  whether the manifest is kept - that still depends only on manifest files.
- `tests/adopt.py`: three cases (`undo_after_scan_is_exact`, `printed_undo_runs`,
  `undo_keeps_committed_baseline`), plus helpers `run_scan` and fixture
  `build_spaced` (folder `case-NN - Copy`, so the printed command is tested
  with a space in the path, as `JLGC - Copy` had). `undo_after_scan_is_exact`
  scans, then delegates to the unchanged `undo_is_exact`. The printed-command
  case takes the `--undo` line from adoption's output, swaps the leading
  `python` for the running interpreter, and runs it through the shell with the
  template (this repo) as cwd. No existing case or assertion was changed.

**How it was verified**

- Before the fix, all three new cases failed: `left behind: ['.secrets-baseline']`;
  `printed undo exited 2` (argparse usage error - the bare, unquoted name);
  `kept .secrets-baseline without saying so`.
- After: `tests/adopt.py` 35/35, `tests/invariants.py` 51/51, `tests/hooks.py`
  26/26, `tests/scan.py` 8/8, `scripts/check.py` exit 0.
- By hand: a local git repo cloned into `toy - Copy`, adopted from the template,
  `python scripts/scan.py` in the clone (wrote `.secrets-baseline`), then the
  printed undo line run verbatim from the template folder: exit 0,
  `removed .secrets-baseline - written by scan.py, never committed`, and
  `git status --short --ignored` in the clone was empty.

**Deviations** (escalations raised, and the answers)

- None. No escalation.

**Follow-ups** (found, not fixed - file and line)

- None found.

**Rollback**

- `git revert <this commit>`: restores the bare-name undo line and the old
  `undo()`; removes the three test cases. No data, manifest or format change.

---

## Lead review

<!-- Lead only. -->
