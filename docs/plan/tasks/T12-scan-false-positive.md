# T12 - scan.py stops flagging code as a password; give it a test suite

Wave: 4
Depends on: T02, T05, T09
Lane: Scan
Estimate: S (~30 min)
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

## Owns

- `scripts/scan.py` - the `password-property` filtering only
- `tests/scan.py` - new
- `project.yaml` - one line under `commands:`
- `RUNBOOK.md` - the *Test* section only
- file modes of `scripts/*.sh` and `scripts/adapters/**/*.sh` (no content changes)
- `docs/plan/tasks/T12-scan-false-positive.md` - Handoff only

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
   say so in Handoff. Cases, each a one-line `.py` file:

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
      so in Handoff.
- [ ] `tests/scan.py`: **6/6**.
- [ ] `git ls-files -s scripts/*.sh` shows mode `100755` for every shim.
- [ ] `check.py` exits 0 (the runbook documents `test-scan`).

## Verify

```bash
python tests/scan.py                        # expected: 6/6 passed
python scripts/check.py                     # expected: exit 0
git ls-files -s scripts/*.sh scripts/adapters   # expected: 100755 on every .sh
python scripts/scan.py                      # runs; record its output in Handoff
```

## Commit

```
fix(T12): stop flagging code as a password

- Expressions are not literal secrets
- Add tests/scan.py, declared as test-scan
- Make .sh shims and adapters executable
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit: `task/T12-scan-false-positive` - the commit that carries this
Handoff (hash reported to the user; not amended in).

**What changed**

- `scripts/scan.py`: new `looks_like_expression(value)` (true on `(` or `[`),
  applied in `regex_scan` only when `rule == "password-property"`, right after
  `looks_like_placeholder`. No other rule, regex or the placeholder filter touched.
- `tests/scan.py` (new): 6 cases from the brief's table, one-line `case.py` per
  case in `<tmp>/scan-tests-<pid>/case-N/`, calls `scan.regex_scan` directly.
  A plain temp dir works - `iter_files` uses `rglob`, not git - so no git repo
  is initialised. Positives assert the expected rule is among those returned
  (and the result is non-empty); negatives assert exactly empty (per the
  escalation answer below).
- `project.yaml`: `test-scan: python tests/scan.py` under `commands:`.
- `RUNBOOK.md` *Test*: scan suite paragraph + `bash` block; "All three" ->
  "All four". *Open defects* untouched (T14).
- File modes: all 10 `scripts/*.sh` and 5 `scripts/adapters/**/*.sh` 100644 ->
  100755 via `git update-index --chmod=+x`. Blob hashes unchanged, so no content
  change.

**How it was verified**

- Before step 1: `python tests/scan.py` -> **3/6**, exit 1; the three failures
  were exactly the code-expression cases (`re.compile(`, `os.environ.get(...)`,
  `getpass()`), each returning `password-property`. After step 1: **6/6**, exit 0.
- `python scripts/check.py` -> exit 0 ("all invariants hold").
- `python tests/invariants.py` 51/51, `tests/hooks.py` 26/26,
  `tests/adopt.py` 31/31.
- `git ls-files -s scripts/*.sh scripts/adapters` -> `100755` on every `.sh`
  (`rest.py` stays 100644).
- `python scripts/scan.py` (no gitleaks here, regex fallback) -> exit 1:

  ```
  warn no gitleaks/trufflehog on PATH - scanned the WORKING TREE ONLY.
            2  password-assignment
  FAIL 2 NEW potential secret(s) since the baseline:
         tests/scan.py:35  password-assignment
         docs/plan/tasks/T12-scan-false-positive.md:57  password-assignment
  ```

  Both are the deliberate fake `hunter2xyz` fixture: one in the new suite, one in
  this brief's case table (already on `main` before this task). Zero
  `password-property` hits remain in the repo. I did **not** run `--update`:
  `.secrets-baseline` is tracked and not in *Owns* - see Follow-ups.

**Deviations** (escalations raised, and the answers)

- **ESCALATION T12** - the "quoted assignment secret" case
  (the quoted `hunter2xyz` line) returns both `password-assignment` and
  `password-property`, not only `password-assignment`; step 1 does not change
  that (no `(`/`[`). Options: 1) positives by inclusion, negatives exactly empty;
  2) exact sets, change case 2's expectation; 3) make `password-property` skip
  quoted values (outside step 1). Recommended 1.
  **Answer: option 1, approved.** Positives assert the expected rule is among
  those returned and the result is non-empty; negatives assert exactly empty; a
  one-line comment at that case in `tests/scan.py` says both rules fire today;
  the double hit goes to Follow-ups. Case count stays 6/6. Implemented as such.

**Follow-ups** (found, not fixed - file and line)

- One quoted secret yields two findings, so two baseline fingerprints
  (`scripts/scan.py:63-68`): `password-assignment` and `password-property` both
  match the quoted `hunter2xyz` line. Fix later by deduplicating per line, or by
  making `password-property` skip quoted values.
- `scripts/scan.py` on this branch exits 1 against the committed
  `.secrets-baseline`: the two fake `hunter2xyz` fixtures above
  (`tests/scan.py:35`, this brief at `:57`). The brief's line is already on
  `main`, so `main` fails the gate today too. Lead call: `python scripts/scan.py
  --update` after merge, or exclude `tests/scan.py` / `docs/plan/` from the scan.
- `scripts/scan.py:100` - `iter_files` tests `path.parts` of the **absolute**
  path against `SKIP_DIRS`, so a repo that sits anywhere under a directory
  named `build`, `target`, `vendor`, `dist`, `venv`... is skipped entirely and
  reports clean. Reproduced: `DB_PASSWORD=s3cr3tValue9` in
  `<tmp>/build/repo/a.py` -> `regex_scan` returns `[]`. Should test the parts
  relative to `root`. A silent false-clean in a security gate - worth a brief.

**Rollback**

`git revert <T12 commit>` on `main` (or `git revert -m 1 <merge>` if merged
`--no-ff`). It restores `scan.py`, removes `tests/scan.py` and the `test-scan`
command, reverts the RUNBOOK paragraph, and puts the `.sh` modes back to 100644.
No migration, no data, no baseline change to undo.
---

## Lead review

<!-- Lead only. -->
