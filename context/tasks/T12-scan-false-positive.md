# T12 - scan.py stops flagging code as a password; give it a test suite

Status: ready
Wave: 4
Depends on: T02, T05, T09
Build: build-0.1A

## Goal

`scan.py` no longer reports a code expression as a secret, has a test suite of
its own that proves true positives still fire, and the shell scripts are
executable on macOS and Linux.

## Why

JLGC defect 6: `_NUMERIC_TOKEN = re.compile(` was reported as a
`password-property` secret. The rule (`scripts/scan.py:66-68`) decides on the
left-hand name; its only test of the value is `\S{6,}` to end of line, and the
placeholder filter (`:80-88`) does not catch it. So `os.environ.get("API_KEY")`
and `getpass()` would match too. The scan's own comment warns that a noisy gate
gets switched off.

`scan.py` has no tests at all - nothing in `tests/` imports or runs it.

Every `.sh` shim and adapter is committed as mode `100644`, so
`./scripts/check.sh` fails with "permission denied" on macOS and Linux.

## Files you may change

- `scripts/scan.py` - the `password-property` filtering only
- `tests/scan.py` - new
- `project.yaml` - one line under `commands:`
- `RUNBOOK.md` - the *Test* section only
- file modes of `scripts/*.sh` and `scripts/adapters/**/*.sh` (no content changes)
- `context/tasks/T12-scan-false-positive.md` - Report section and Status line only

## Do exactly this

1. In `scripts/scan.py`, add `looks_like_expression(value)`: true when the value
   contains `(` or `[`. Apply it **only** to `password-property` matches, next to
   where `looks_like_placeholder` is applied: an expression is code, not a
   literal secret. Do not apply it to `password-assignment` - a quoted password
   may legitimately contain brackets.
2. Create `tests/scan.py` in the style of the other suites: a module docstring
   explaining what it proves, a case table, one printed line per case, a final
   `N/M passed`, exit 1 on any failure. Work in a temp directory named with the
   PID (as T00 did for the others). Import `scan` from `scripts/` and call
   `scan.regex_scan(<temp dir>)`, asserting on the rule names it returns. If
   `regex_scan` cannot see files in a plain temp directory (for example because it
   lists files through git), initialise a git repo there and add the files - and
   say so in Report. Cases, each a one-line `.py` file:

   | Case | Line | Expect |
   |---|---|---|
   | unquoted property secret | `DB_PASSWORD=s3cr3tValue9` | `password-property` |
   | quoted assignment secret | `password = "hunter2xyz"` | `password-assignment` |
   | compile call is not a secret `[+]` | `_NUMERIC_TOKEN = re.compile(` | nothing |
   | env lookup is not a secret `[+]` | `api_key = os.environ.get("API_KEY")` | nothing |
   | function call is not a secret `[+]` | `password = getpass()` | nothing |
   | placeholder is not a secret `[+]` | `PASSWORD=changeme` | nothing |

   If any expectation in this table turns out wrong for a reason outside step 1,
   stop and raise a deviation request - do not change the expectation.
3. `project.yaml`, under `commands:`: add `test-scan: python tests/scan.py`.
4. `RUNBOOK.md`, *Test* section: add the scan suite - one sentence on what it
   proves, and the command in a `bash` block - and change "All three must be green
   before a commit" to "All four". (`check.py` requires every declared command to
   appear in the runbook.)
5. Make the shell scripts executable in git, without changing their content:
   `git update-index --chmod=+x scripts/*.sh` and the same for every `.sh` under
   `scripts/adapters/`.

## Do not

- Change any other scan rule or the placeholder filter.
- Touch RUNBOOK's *Open defects* list - T14 does the release bookkeeping.
- Change the content of any `.sh` file.

## Acceptance criteria

- [ ] The three code-expression cases fail before step 1 and pass after - say
      so in Report.
- [ ] `tests/scan.py`: **6/6**.
- [ ] `git ls-files -s scripts/*.sh` shows mode `100755` for every shim.
- [ ] `check.py` exits 0 (the runbook documents `test-scan`).

## Verify

```bash
python tests/scan.py                        # expected: 6/6 passed
python scripts/check.py                     # expected: exit 0
git ls-files -s scripts/*.sh scripts/adapters   # expected: 100755 on every .sh
python scripts/scan.py                      # runs; record its output in Report
```

## Commit

```
fix(T12): stop flagging code as a password
- Expressions are not literal secrets
- Add tests/scan.py, declared as test-scan
- Make .sh shims and adapters executable
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
