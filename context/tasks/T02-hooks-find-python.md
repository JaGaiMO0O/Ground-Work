# T02 - Make the guardrail hooks find Python on any OS, and test the real wiring

Status: ready
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
