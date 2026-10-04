# T17 - scan.py must scan a repo that sits under a "build" or "vendor" folder

Wave: 5
Lane: Scan
Depends on: T12
Estimate: S (~30 min)
Build: build-0.1A

**Security fix. Never cut to hold a date.**

## Goal

The fallback secret scan skips build and vendor directories **inside** the
project, and never skips the project itself because of where it sits on disk.

## Why

Found and reproduced by T12's worker (2026-10-04). `iter_files()` tests
`path.parts` of the **absolute** path against `SKIP_DIRS`
(`scripts/scan.py:106`). So a repository located anywhere under a folder named
`build`, `target`, `vendor`, `dist`, `venv`, ... is skipped **entirely** - and the
scan reports clean. Reproduced: `DB_PASSWORD=s3cr3tValue9` in `<tmp>/build/repo/a.py`
-> `regex_scan` returns `[]`.

A security gate that silently reports clean is worse than no gate: it is trusted.
`SKIP_DIRS` is meant for directories inside the project; the test must look only
at the path relative to the scan root.

## Owns

- `scripts/scan.py` - `iter_files()` only
- `tests/scan.py`
- `docs/plan/tasks/T17-scan-repos-under-build-dirs.md` - Handoff only

## Scope - do exactly this

1. Write the tests first (step 3) and watch the negative one fail.
2. In `iter_files(root)`, test `SKIP_DIRS` against the parts of
   `path.relative_to(root)`, not of `path`. Change nothing else in the function.
3. `tests/scan.py`, two cases:

   | Case | Setup | Expect |
   |---|---|---|
   | repo under a build folder is scanned | scan root is `<temp>/build/repo/`; it holds `a.py` with `DB_PASSWORD=s3cr3tValue9` | `password-property` returned |
   | build folder inside the repo still skipped `[+]` | scan root `<temp>/repo/`; `build/a.py` inside it holds the same line | nothing returned |

## Do not

- Change `SKIP_DIRS`, `SKIP_NAMES`, any rule, or the gitleaks path.
- Change how existing cases assert.

## Acceptance criteria

- [ ] The first case fails before step 2 and passes after - say so in the Handoff.
- [ ] Scan suite **8/8** (6 + 2).
- [ ] `python scripts/scan.py` on `main`'s tree still exits 0.

## Verify

```bash
python tests/scan.py           # expected: 8/8 passed
python scripts/scan.py         # expected: exit 0
python scripts/check.py        # expected: exit 0
```

## Commit

```
fix(T17): scan repos that sit under build dirs

- Skip list tests paths relative to the scan root
- A repo under build/ or vendor/ was reported clean
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit:

**What changed**

**How it was verified**

**Deviations** (escalations raised, and the answers)

**Follow-ups** (found, not fixed - file and line)

**Rollback**

---

## Lead review

<!-- Lead only. -->
