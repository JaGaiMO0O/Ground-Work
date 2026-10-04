# T02 - Make the guardrail hooks find Python on any OS, and test the real wiring

Wave: 1
Depends on: T00
Build: build-0.1A

## Goal

The hooks in `.claude/settings.json` run `guard.py` with whichever of `python` /
`python3` exists, keep its exit code, and say so loudly when neither exists. A
test proves the actual hook command - not just `guard.py` - blocks a `.env` read.

## Why

All four hooks (`.claude/settings.json:48,59,70,81`) run bare
`python "${CLAUDE_PROJECT_DIR:-.}/scripts/hooks/guard.py"`. Many Macs and
Debian/Ubuntu machines have only `python3`. There the hook fails, `guard.py`'s
design is to fail open, and the `.env` read block, the `systems/` write block and
the generated-file block all stop - with no message. That is the same failure as
the phase-2 `guard.py` cwd bug: protection quietly gone.

`tests/hooks.py` calls `guard.py` directly (`:27`, `:34`), so it cannot see this:
it tests the guard, never the wiring.

The 10 shims (`scripts/*.sh:4`) try `python3` first. On Windows `python3` is often
the Microsoft Store alias stub, which exists on PATH but does not run Python. So
`python` must come first.

## Files you may change

- `.claude/settings.json` - the four hook `command` strings only
- `scripts/capture.sh`, `scripts/check.sh`, `scripts/handoff.sh`, `scripts/init.sh`,
  `scripts/new-card.sh`, `scripts/query.sh`, `scripts/scan.sh`,
  `scripts/snapshot-db.sh`, `scripts/sync.sh`, `scripts/test.sh` - line 4 only
- `tests/hooks.py`
- `README.md` - the prerequisites paragraph in the *Get it* section only
- `START-HERE.md` - one added sentence, see step 5
- `context/tasks/T02-hooks-find-python.md` - Report section and Status line only

## Do exactly this

1. In `.claude/settings.json`, replace each of the four hook commands with this
   exact shell line (shown unescaped - escape the inner quotes for JSON):

   ```sh
   PY=$(command -v python || command -v python3) || { echo "Ground Work guardrails OFF: no python found" >&2; exit 1; }; exec "$PY" "${CLAUDE_PROJECT_DIR:-.}/scripts/hooks/guard.py"
   ```

   `exec` is what keeps exit code 2 (block) intact. `exit 1` is a visible,
   non-blocking error rather than a silent pass.
2. In each of the 10 shims, change line 4 from
   `PY=$(command -v python3 || command -v python)` to
   `PY=$(command -v python || command -v python3)`. Nothing else in the shims.
3. In `tests/hooks.py`, add two cases that read the hook command string **from
   `.claude/settings.json`** (parse the JSON; do not copy the string into the
   test) and run it through `bash -c`, with `CLAUDE_PROJECT_DIR` set to the repo
   root and a JSON payload on stdin built with `json.dumps` (never hand-built -
   see RUNBOOK *Known rough edges*):
   - a `PreToolUse` `Read` of `.env` -> exit code **2**
   - a `PreToolUse` `Read` of `README.md` -> exit code **0**

   If `bash` is not on PATH, the case must **fail** with a message saying so -
   not skip. Claude Code runs these hooks through a POSIX shell; a machine
   without one cannot run them either.
4. In `README.md`, *Get it* section, after the sentence that states the Python
   and git requirement, add:
   *"On macOS and Linux the command is often `python3` - use that wherever these
   docs say `python`."*
5. In `START-HERE.md`, directly after the line "You do not need to understand the
   whole repo. You need these.", add the same sentence.

6. In `tests/hooks.py`, delete `TMP` at the end of every run, using the
   version-guarded `rmtree` pattern T00 added to the other suites. Since T00
   named it per process, each run otherwise leaves a ~176KB folder in temp
   (found by T00's worker).

## Do not

- Change the allow-list entries (`Bash(python scripts/...)`). Deferred.
- Touch `.ps1` shims - they already try `python` first.
- Touch `scripts/adapters/` or `scripts/hooks/guard.py`.
- Rewrite the commands throughout the docs to `python3`.

## Acceptance criteria

- [ ] All four hook commands are the new line; `settings.json` is valid JSON.
- [ ] All 10 shims try `python` first.
- [ ] The two new cases pass, and the `.env` case **fails** if you temporarily
      change the hook command back to bare `python` while pointing PATH at a
      directory with no `python` - or, if that cannot be arranged on this
      machine, say so in Report and show the `.env` case passing.
- [ ] hooks suite: **23/23**.
- [ ] A run of `tests/hooks.py` leaves no `guard-tests-*` folder behind.

## Verify

```bash
python -c "import json; json.load(open('.claude/settings.json'))"   # no error
python tests/hooks.py               # expected: 23/23 passed
python scripts/check.py             # expected: exit 0
grep -n "command -v" scripts/*.sh   # expected: python first on all 10
```

## Commit

```
fix(T02): resolve python for hooks on any OS
- Hooks try python then python3 and exec guard.py
- Fail visibly when neither exists
- Test the real hook command from settings.json
- Shims try python first; docs note python3
- hooks.py cleans up its temp dir
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: the single `fix(T02)` commit on branch `claude/goofy-chaum-b122af`
(a commit cannot hold its own hash, so the hash is in the hand-off message).

**What changed**

- `.claude/settings.json`: all four hook commands are now the step-1 line.
  Nothing else in the file changed.
- 10 `scripts/*.sh` shims, line 4: `python` first, then `python3`.
- `README.md` (*Get it*) and `START-HERE.md`: the `python3` sentence, placed
  where steps 4 and 5 say.
- `tests/hooks.py`:
  - `hook_command()` reads the command from `settings.json`.
  - `fire_hook()` runs it with `bash -c`, `CLAUDE_PROJECT_DIR` set to the repo
    root and a `json.dumps` payload on stdin.
  - Two wiring cases check exit codes: `.env` must give 2 and `README.md` must
    give 0.
  - `find_bash()` follows the approved deviation below. Each wiring line
    prints the bash it used.
  - `nuke(TMP)` runs in a `finally`, using the same version-guarded `rmtree`
    and retry pattern as `tests/invariants.py`.

**Verify output** (Windows 11, Python 3.12.10)

- `json.load(.claude/settings.json)`: no error.
- `python tests/hooks.py`: **23/23 passed**, from both Git Bash and
  PowerShell. Both runs printed `[bash: C:\Program Files\Git\bin\bash.exe]`.
- `python scripts/check.py`: `ok all invariants hold`, exit 0.
- `grep -n "command -v" scripts/*.sh`: all 10 shims read
  `command -v python || command -v python3`.
- Negative check: `settings.json` was set back to bare `python` for a moment,
  with no Python on PATH (PATH = `/usr/bin` plus `Git/cmd`). The `.env` case
  gave **exit 127** and **FAILED** (21/23). The file was then restored and the
  diff checked.
- New command, same PATH with no Python: **exit 1**, FAILED. This is the
  intended visible failure.
- PATH that has only `python3`: 23/23. The fallback works.
- PATH with no Git (`C:\WINDOWS\system32` only): both wiring cases FAILED with
  "no Git Bash found - Claude Code needs Git for Windows (or
  CLAUDE_CODE_GIT_BASH_PATH) to run hooks". The test did not fall back to WSL.
- Temp folders: a run leaves no `guard-tests-<pid>` behind. Two older folders
  are still there and were not made by these runs (see below).

**Deviation requests**

```
DEVIATION REQUEST T02
What:        Choose bash for the two wiring cases as Claude Code does on
             Windows: use CLAUDE_CODE_GIT_BASH_PATH, else Git's
             bin/bash.exe (found from shutil.which("git")). Elsewhere,
             plain shutil.which("bash"). If none is found, the case FAILS.
Why:         From PowerShell/cmd, shutil.which("bash") returns
             C:\WINDOWS\system32\bash.EXE (the WSL launcher). Its only
             distro here is docker-desktop, which has no /bin/bash, so the
             suite gave 21/23. From Git Bash it gave 23/23.
Impact:      tests/hooks.py only. Asserts and the case count (23) unchanged.
Alternative: Keep plain shutil.which("bash") and record the difference
             between shells.
```

Answer: **APPROVED, with conditions**, all of them met:
1. Find Git Bash by walking up from the directory of `shutil.which("git")`,
   at most 3 levels, to the first that contains `bin/bash.exe`.
2. On Windows, never fall back to System32 `bash.exe`. Fail with a message
   that Claude Code needs Git for Windows (or `CLAUDE_CODE_GIT_BASH_PATH`).
   Off Windows, use plain `shutil.which("bash")`.
3. Print the bash path on each wiring case's output line.

**Found, not fixed**

- Old temp folders `%TEMP%\guard-tests` (2026-08-06, before T00 added the pid
  suffix) and `%TEMP%\guard-tests-4196` (made earlier today, before this task)
  are still there. Neither was made by this task's runs, so I left them.
- `.claude/settings.json:22-33`: the allow-list entries still use
  `Bash(python scripts/...)`. On a machine with only `python3` they will not
  match. The task defers this.
- Windows: if `python` is missing but the Microsoft Store `python3.exe` stub
  is on PATH (this machine has it in `WindowsApps`), the hook will `exec` the
  stub. The stub exits non-zero with its own message, so the hook does not
  block, though the message is visible. This was not tested here.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Cherry-picked into `main` as `fdf06cf`. Branch renamed from `claude/...` to
`T02-hooks-find-python`.

- Deviation approved with three conditions; all met and shown in Verify.
- Reproduced the original silent failure (exit 127) before fixing it, and
  proved the test never falls back to WSL. Gate: hooks 23/23, both wiring
  cases on `C:\Program Files\Git\bin\bash.exe`.
- *Found, not fixed*: allow-list `python` entries (already deferred); the
  Windows Store `python3` stub case -> T14's deferred list. Old temp folders
  predate the task - harmless.
