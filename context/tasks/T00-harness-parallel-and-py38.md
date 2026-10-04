# T00 - Make the test harnesses parallel-safe and Python 3.8-safe

Status: ready
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

Commit:

**What changed**

**Verify output**

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
