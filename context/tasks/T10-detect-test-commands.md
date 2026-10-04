# T10 - Detect the test command adoption has been missing; first detection tests

Status: ready
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

Commit:

**What changed**

**Verify output**

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
