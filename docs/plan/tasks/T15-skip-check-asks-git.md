# T15 - The skip-list reference check asks git; interview dates must be real

Wave: 3
Depends on: T05
Build: build-0.1A

## Goal

`check.py`'s *Do not read* reference search looks only at the files git counts
as the project, and a `(per NAME, YYYY-MM-DD)` citation must carry a real date.

## Why

Both found by T05's worker (wave-2 gate, 2026-10-04).

- The reference search in `scripts/check.py` (`code_files` and its caller) walks
  the disk. In a checkout with live worktrees under `.claude/worktrees/` - eight
  were live at this gate - every worktree's copy is searched. That is slow, and
  worse, a worktree's copy of the very file listed under *Do not read* counts as
  "something references it", so the check raises a **false warning**. Any
  adopted project that uses Claude Code worktrees would see it. This is the defect
  T01 fixed for adoption, in a second place: the project is what git says it is,
  not what is on disk. `lib.template_files()` (added by T01) already answers that.
- `(per X, 2026-99-99)` passes - the date is checked for shape only.

## Files you may change

- `scripts/check.py` - the reference search's file listing, and the citation
  match for the `per` form only
- `tests/invariants.py`
- `context/tasks/T15-skip-check-asks-git.md` - Report section and Status line only

## Do exactly this

1. In the *Do not read* reference search, build the candidate file list from
   `lib.template_files(ROOT)` instead of walking the directory. Keep every
   existing filter on top: `lib.CODE_SUFFIXES`, the 1 MB cap, the skipped
   directories, and the exclusion of the listed path itself. Remove the walk.
2. For `(per NAME, YYYY-MM-DD)`: the date must parse with
   `datetime.date.fromisoformat`. If it does not, the claim is **not** cited, and
   the error message must contain **`invalid date`** and the text found.
3. `tests/invariants.py` - two cases:

   | Case | Exit | Text | Notes |
   |---|---|---|---|
   | skip check ignores worktree copies `[+]` | 0 | | needs git (`use_git=True`). A `kind: local` area, a card listing `src/old_report.py` under *Do not read* with a reason, **no** reference to it anywhere in the project - and, planted after the base commit, a copy at `.claude/worktrees/w1/src/old_report.py` plus a file there that mentions `old_report`. The repo's `.gitignore` already ignores `.claude/worktrees/` (T01). |
   | interview date invalid | 1 | `invalid date` | a claim cited `(per Rania, 2026-99-99)` |

## Do not

- Change any other rule, message or case.
- Change `lib.template_files()` - it belongs to T01's design.
- Remove the non-git fallback inside `template_files()`; outside git the walk is
  the only option.

## Acceptance criteria

- [ ] The worktree case fails before step 1 (a false `referenced from` warning)
      and passes after - say so in Report.
- [ ] Invariants **51/51** (49 + 2).
- [ ] `check.py` exits 0 on this repo.

## Verify

```bash
python tests/invariants.py --only "worktree copies"   # expected: 1/1 passed
python tests/invariants.py --only "invalid"           # expected: 1/1 passed
python tests/invariants.py                            # expected: 51/51 passed
python scripts/check.py                               # expected: exit 0
```

## Commit

```
fix(T15): ask git in the skip-list check
- Reference search uses lib.template_files
- Interview citation dates must be real
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: this commit on `T15-skip-check-asks-git` (hash reported in chat)

**What changed**

- Before starting: fast-forwarded the worktree from `1a79a04` to `main`
  (`6d41925`). Clean fast-forward, nothing lost.
- `check.py` `code_files()`: candidate list now comes from
  `lib.template_files(ROOT)`; the `os.walk` is gone (and with it the only use
  of `import os`, so that import is removed). Kept on top: `SKIP_TOP_DIRS` on
  the first path part, `SKIP_ANY_DIRS` on any directory part,
  `lib.CODE_SUFFIXES`, the 1 MB cap. The listed-path exclusion in
  `check_skip_list` is untouched.
- `check.py` citations: the `per` form moved out of `CITE_OTHER` into
  `CITE_PER`; its date must pass `date.fromisoformat`. A claim whose only
  citation is a `per` with a bad date is an error:
  `claim cites an invalid date: (per Rania, 2026-99-99)`. A claim with a bad
  `per` date but another valid citation is still cited (the bad `per` simply
  does not count) - no other rule or message changed.
- `tests/invariants.py`: the two cases from the table.
  - The worktree case assembles the dead file's name at runtime
    (`"old_" + "report"`): `tests/invariants.py` is itself copied into every
    case, so the literal name in it would be a real reference and a real
    warning. What the case asserts is as specified.
- Before/after: with only the tests added, the worktree case exited **2** with
  `` `src/old_report.py` is listed under Do not read but referenced from
  .claude/worktrees/w1/src/app/caller.py `` (the false warning), and the
  invalid-date case exited **0**. After the fix both pass.

**Verify output**

```
python tests/invariants.py --only "worktree copies"   1/1 passed
python tests/invariants.py --only "invalid"           1/1 passed
python tests/invariants.py                            51/51 passed in 138s
python scripts/check.py                               exit 0
```

**Deviation requests**

None.

**Found, not fixed**

- `scripts/check.py` (STATUS goals staleness rule, `from datetime import date`
  inside the function, ~line 707): now redundant with the module-level import
  this task added. Harmless; outside the parts of `check.py` this task owns.

---

## Lead review

<!-- Lead only. -->
