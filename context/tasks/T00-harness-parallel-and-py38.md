# T00 - Make the test harnesses parallel-safe and Python 3.8-safe

Status: accepted
Wave: 0
Depends on: none
Build: build-0.1A

## Goal

All three test suites run correctly on Python 3.8 through 3.13, and two copies of
the same suite can run at the same time without interfering.

## Why

- `tests/adopt.py:65` and `tests/invariants.py:136` call
  `shutil.rmtree(path, onexc=force)`. `onexc` exists only from Python 3.12. On
  3.8-3.11 it raises an uncaught `TypeError`, yet `TESTING.md` tells testers 3.8+.
- Each suite works in one fixed temp directory - `adopt-harness`,
  `invariant-harness`, `guard-tests` (`tests/hooks.py:28`) - and deletes it on
  start. Every later wave runs several tasks at once in this folder, so two runs
  of one suite would delete each other's work mid-run.

This task lands alone, first, because every other task depends on the suites.

## Files you may change

- `tests/adopt.py`
- `tests/invariants.py`
- `tests/hooks.py`
- `context/tasks/T00-harness-parallel-and-py38.md` - Report section and Status line only

## Do exactly this

1. In `tests/adopt.py` and `tests/invariants.py`, replace the `rmtree` call inside
   `nuke()` so it works on every version: pass `onexc=force` when
   `sys.version_info >= (3, 12)`, otherwise `onerror=force`. The existing
   `force(func, target, _exc)` callback already fits both signatures - keep it.
2. Make each harness's temp directory unique to the run by appending the process
   ID:
   - `tests/adopt.py:39` -> `adopt-harness-{os.getpid()}`
   - `tests/invariants.py:38` -> `invariant-harness-{os.getpid()}`
     (`PRISTINE` and `WORK` already derive from `BASE` - check they still do)
   - `tests/hooks.py:28` -> `guard-tests-{os.getpid()}`
3. Wherever a suite supports `--keep`, print the temp directory's path at the end
   of the run when `--keep` is given, so the user can find it now that the name
   varies.
4. If `tests/hooks.py` deletes its temp directory with `rmtree`, apply step 1
   there too.
5. Change nothing else - no new cases, no renamed cases, no changed assertions.

## Do not

- Add or alter test cases. The case counts must not move.
- Touch any file under `scripts/`.
- Add cleanup of old, differently named temp directories from previous runs.

## Acceptance criteria

- [ ] No `onexc=` remains unguarded in `tests/`.
- [ ] Each suite's temp directory name includes the PID.
- [ ] Counts unchanged: invariants **39**, hooks **21**, adopt **22**, all passing.
- [ ] Two simultaneous runs of `tests/adopt.py` both pass.

## Verify

```bash
python tests/invariants.py      # expected: 39/39 passed
python tests/hooks.py           # expected: 21/21 passed
python tests/adopt.py           # expected: 22/22 passed

# Parallel safety - run two at once; both must pass:
python tests/adopt.py > /tmp/a1.txt 2>&1 & python tests/adopt.py > /tmp/a2.txt 2>&1 & wait
tail -1 /tmp/a1.txt /tmp/a2.txt # expected: 22/22 passed, twice

# Older Python, if one is installed:
py -0                           # lists installed versions (Windows)
py -3.11 tests/adopt.py         # use the oldest available below 3.12
```

If no Python below 3.12 is installed, say so in Report - do not install one.

## Commit

```
test(T00): make harnesses parallel and 3.8-safe
- rmtree onexc on 3.12+, onerror below
- per-run temp dirs named with the PID
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: the `test(T00)` commit on branch `claude/kind-villani-c2858e`. The hash
cannot sit in the commit it names, so it went to the user.

**What changed**

- `tests/adopt.py`, `tests/invariants.py`: `nuke()` passes `onexc=force` on
  3.12+ and `onerror=force` below that. `force` is unchanged.
- `BASE` is now `adopt-harness-{pid}` / `invariant-harness-{pid}`. `PRISTINE` and
  `WORK` (and the per-case `WORK` in `fresh()`) still derive from `BASE`.
- `--keep` prints `kept: <BASE>` before the closing rule, so the
  `N/N passed` line stays last.
- `tests/hooks.py`: `TMP` is now `guard-tests-{pid}`. Steps 3 and 4 do not apply:
  it has no `--keep` flag and no `rmtree`.
- No cases added, renamed or changed.

**Verify output** (Python 3.12.10, Windows 11)

```
python tests/invariants.py   -> 39/39 passed in 93s
python tests/hooks.py        -> 21/21 passed
python tests/adopt.py        -> 22/22 passed in 56s
two adopt.py at once (11:29:07 -> 11:30:13, so they overlapped):
  /tmp/a1.txt -> 22/22 passed in 65s
  /tmp/a2.txt -> 22/22 passed in 65s
  no adopt-harness-* left in %TEMP% afterwards
adopt.py --only "undo keeps" --keep  -> kept: ...\Temp\adopt-harness-16400, 1/1 passed
invariants.py --only derived --keep  -> kept: ...\Temp\invariant-harness-22160, 1/1 passed
grep onexc= tests/           -> only the two calls inside the version check
py -0                        -> 3.14, 3.12 only
```

No Python below 3.12 is installed, so the `onerror=` branch has not been run.
Nothing was installed.

**Deviation requests**

None.

**Found, not fixed**

- `tests/hooks.py:57-62`: nothing ever deletes `TMP`. With a fixed name, one
  folder got reused. With the PID in the name, every run now leaves its own
  `guard-tests-<pid>/` with a ~176KB `big.py` in it, and they pile up in `%TEMP%`.
- "Why" above says each suite deletes its temp dir on start. `tests/hooks.py`
  never does. Only `adopt.py` and `invariants.py` do.
- Old fixed-name dirs from earlier runs stay in `%TEMP%` (`guard-tests` is still
  there). They are left alone, per "Do not".
- 3.8 support is only checked for `rmtree`. No 3.8 interpreter has run any of
  the three suites.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Fast-forwarded into `main` as `7bfbb3a`
(branch `claude/kind-villani-c2858e`). In scope, minimal, honest report.

- The `onerror` branch is unexercised: no Python below 3.12 on this machine.
  Carried to T13.
- *Found, not fixed* item 1 (hooks.py leaves its temp dir behind) is folded
  into T02, which owns `tests/hooks.py` in wave 1.
- **Gate on `main`:** check exit 0, invariants 39/39 (150s), hooks 21/21,
  adopt **21/22**. The failure is not T00's: with this worktree living under
  `.claude/worktrees/`, adoption copied it into every target (199 files added).
  Pre-existing leak, exposed by the worktree workflow. T01 rewritten to fix the
  root cause - the template's file list now comes from git.
