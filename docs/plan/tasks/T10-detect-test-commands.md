# T10 - Detect the test command adoption has been missing; first detection tests

Wave: 3
Depends on: T01, T05, T06
Build: build-0.1A

## Goal

`init.py --adopt` finds the test command in the project layouts it has been
missing, never crashes on an unusual `package.json`, and has tests that assert on
detected commands for the first time.

## Why

JLGC defect 3: a project with 84 tests got `# TODO: how do you test this?` in its
RUNBOOK. All three reported causes are confirmed in `_adopt.detect()`
(`scripts/_adopt.py:170-175`):

- the `requirements.txt` branch never reads the file, so never sees `pytest`;
- a root `requirements.txt` that is just `-r backend/requirements.txt` is not followed;
- `tests/` is looked for at the root only - not `backend/tests`, not `test/`,
  not `conftest.py`.

Also: the `pyproject.toml` branch never checks for a tests directory; Maven and
Gradle ignore `./mvnw` / `./gradlew` wrappers (the estate this targets is Java);
a top-level JSON array in `package.json` raises an uncaught `AttributeError`
(`:133`).

**No test in `tests/adopt.py` asserts on a detected command.** The only manifest
any fixture contains is a one-line `requirements.txt`.

## Files you may change

- `scripts/_adopt.py` - `detect()`, a new helper it calls, the import block, and
  removal of the local `CODE_SUFFIXES`
- `tests/adopt.py`
- `context/tasks/T10-detect-test-commands.md` - Report section and Status line only

## Do exactly this

1. `_adopt.py` already imports `_lib` (T01). Use `lib.CODE_SUFFIXES` (added by
   T05) in place of the local `CODE_SUFFIXES`; delete the local copy.
2. Add a helper that reports whether a Python project has tests: a `tests/` or
   `test/` directory, a `pytest.ini`, or a `conftest.py`, at the root **or** in
   any immediate subdirectory not in `NOISE`.
3. `requirements.txt` branch: read the file. Follow `-r PATH`,
   `--requirement PATH` and `--requirement=PATH` **one level**, relative to that
   file's directory. Set `test: pytest` if any line in either matches
   `^\s*pytest\b` (case-insensitive), or the step-2 helper says yes. The install
   command stays `pip install -r requirements.txt` - pip follows `-r` itself.
4. `pyproject.toml` branch: keep the existing `"pytest" in text` check, and also
   set `test: pytest` when the step-2 helper says yes.
5. Maven: if `mvnw` exists at the root use `./mvnw test` and
   `./mvnw -DskipTests package`; otherwise today's commands. Gradle: if `gradlew`
   exists use `./gradlew test` and `./gradlew build`. Record the actual Gradle file
   name found (`build.gradle` or `build.gradle.kts`) in `sources`.
6. `package.json`: if the parsed JSON is not an object, or its `scripts` is not an
   object, take no commands from it - record the source, do not raise.
7. `tests/adopt.py` - five cases. Each asserts on the target's `project.yaml`
   (the `commands:` block written by `_adopt.project_yaml`, one `  key: command`
   line per command):

   | Case | Fixture (via `make(..., extra=...)`) | Assert |
   |---|---|---|
   | detect pytest in nested tests | `backend/tests/test_x.py` | `  test: pytest` |
   | detect pytest through -r | `requirements.txt` = `-r backend/requirements.txt`; `backend/requirements.txt` = `pytest` + `flask` | `  test: pytest` |
   | detect pytest via pyproject tests dir | `pyproject.toml` without the word pytest; `tests/test_x.py` | `  test: pytest` |
   | detect maven wrapper | `pom.xml`, `mvnw` | `  test: ./mvnw test` |
   | package.json array no crash | `package.json` = `[]` | adopt exits 0; `project.yaml` written |

8. In `tests/adopt.py`, pass `stdin=subprocess.DEVNULL` to **every**
   `subprocess.run` that runs `init.py` - the harness's own call in `main()`,
   `run_template_init()`, and any other. `adopt()` prompts when stdin is a
   terminal and purpose or done is missing, so run from a user's own terminal
   the suite can hang on a prompt nobody can see. Found by T06's worker.

## Do not

- Change language detection's last-match-wins behaviour, or the `.csproj` glob -
  both deferred.
- Change any command other than the test and build commands named above.
- Touch `travels()`, the manifest, or anything T01/T06 changed.

## Acceptance criteria

- [ ] All five cases fail before your `_adopt.py` change (the crash case errors)
      and pass after - say so in Report.
- [ ] Adopt suite: **31/31** (26 + 5).
- [ ] `_adopt.py` no longer defines its own `CODE_SUFFIXES`.

## Verify

```bash
python tests/adopt.py --only detect       # expected: 4/4 passed
python tests/adopt.py --only package      # expected: 1/1 passed
python tests/adopt.py                     # expected: 31/31 passed
grep -n "^CODE_SUFFIXES" scripts/_adopt.py   # expected: nothing
python scripts/check.py                   # expected: exit 0
```

## Commit

```
fix(T10): detect test commands that were missed
- Read requirements, follow one -r, nested tests
- Prefer mvnw / gradlew wrappers
- Survive a package.json that is not an object
- First adopt cases asserting detected commands
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: on branch `T10-detect-test-commands` (hash reported to the user; a
commit cannot hold its own hash)

**What changed**

- `scripts/_adopt.py`
  - Deleted the local `CODE_SUFFIXES`; `propose_areas()` uses `lib.CODE_SUFFIXES`.
  - New `_has_python_tests(target)`: `tests/`, `test/`, `pytest.ini` or
    `conftest.py` at the root or in any immediate subdirectory not in `NOISE`.
  - New `_requirements_mention_pytest(path)`: reads the file, follows `-r PATH`,
    `--requirement PATH`, `--requirement=PATH` one level, relative to the
    including file's directory, then matches `^\s*pytest\b` (case-insensitive).
  - `requirements.txt` branch: `test: pytest` from either helper. Install
    command unchanged.
  - `pyproject.toml` branch: `"pytest" in text` or `_has_python_tests()`.
  - Maven: `./mvnw test` / `./mvnw -DskipTests package` when `mvnw` is at the
    root. Gradle: `./gradlew test` / `./gradlew build` when `gradlew` is.
    The trigger is still the `build.gradle*` glob. `sources` records the name
    of the first file that glob matched (sorted), not a hard-coded `build.gradle`.
  - `package.json`: `JSONDecodeError`, a non-object document, or a non-object
    `scripts` gives no commands. The source is still recorded, and nothing raises.
- `tests/adopt.py`
  - Five cases, each with the fixture and assertion from step 7.
    `command_detected(line)` checks for an exact `  key: command` line in
    `project.yaml`.
  - `stdin=subprocess.DEVNULL` on both `subprocess.run` calls that run
    `init.py`, in `run_template_init()` and `main()`. Every other caller goes
    through `run_template_init()`, and the other `subprocess.run` calls run
    git, not init.py.

Before the `_adopt.py` change (tests written first): `--only detect` was
0/4. Each case failed with `project.yaml has no 'test: ...' line`.
`--only package` was 0/1, because adopt crashed with
`AttributeError: 'list' object has no attribute 'get'` at `_adopt.py:141`.
After the change, all five pass.

**Verify output**

```
python tests/adopt.py --only detect      -> 4/4 passed in 17s
python tests/adopt.py --only package     -> 1/1 passed in 4s
python tests/adopt.py                    -> 31/31 passed in 123s
grep -n "^CODE_SUFFIXES" scripts/_adopt.py -> nothing (exit 1)
python scripts/check.py                  -> ok all invariants hold, exit 0
```

**Deviation requests**

None.

**Found, not fixed**

- `scripts/_lib.py:76-78` - the comment above `CODE_SUFFIXES` still calls it
  "a copy of the set in _adopt.py, which should import it from here (T10 does
  that)". It is now the only copy. Not in my files.
- `scripts/_adopt.py` Maven/Gradle - on Windows the wrapper is `mvnw.cmd` /
  `gradlew.bat`, and `./mvnw` does not run in cmd or PowerShell. Step 5 named
  only `mvnw` / `gradlew`, so the command is POSIX-only.
- `scripts/_adopt.py` `package.json` - `"scripts": null` now gives no commands,
  `install` included. The old `or {}` treated it as an empty mapping. That
  follows step 6 (null is not an object), but it is a change in behaviour.
- `tests/adopt.py` - the case name `detect pytest via pyproject tests dir` is
  37 characters, one more than the 36-wide name column, so its row prints out of
  line. Cosmetic only. The name was kept so `--only detect` matches.

---

## Lead review

<!-- Lead only. -->
