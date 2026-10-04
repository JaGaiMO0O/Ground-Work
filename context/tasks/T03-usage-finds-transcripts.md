# T03 - Make usage.py find a project's transcripts from any path

Status: ready
Wave: 2
Depends on: T00, T02
Build: build-0.1A

## Goal

`usage.py` (and `status.py`'s budget line) finds the Claude Code transcripts for
a project whatever characters its path contains, on Windows, macOS and Linux.

## Why

`usage.py` is the instrument that will measure the rollout - the only thing that
can close the "premise unmeasured" blocker. If it misses transcripts it reports
"no telemetry" or an understated number, which reads as good news. That is the
`native_path` failure class again.

- `scripts/_transcripts.py:73-78` `_slug()` replaces only `: \ / space .`.
  Claude Code replaces **every** non-alphanumeric character. Observed on this
  machine: `Desktop/RedKeys/Name_Screening` is stored as
  `C--Users-myaghmour-Desktop-RedKeys-Name-Screening`. Any path with `_ ( ) @ + ~`
  misses the exact match.
- `_slug()` calls `path.resolve()`, which follows symlinks. Claude Code records the
  logical working directory. On macOS `/tmp` resolves to `/private/tmp`, and
  iCloud-synced Desktops resolve elsewhere, so the slug never matches.
- The fallback in `project_dirs_for` (`:161-185`) compares against
  `cwd.resolve()` too, and `break`s after the **first** `.jsonl` in each folder.

## Files you may change

- `scripts/_transcripts.py` - `_slug()` and `project_dirs_for()` only
- `tests/hooks.py`
- `context/tasks/T03-usage-finds-transcripts.md` - Report section and Status line only

## Do exactly this

1. `_slug(path)`: return `re.sub(r"[^A-Za-z0-9]", "-", str(path))` on the path
   **as given** - no `resolve()` inside it. Update its docstring to say this is
   the observed Claude Code rule, and cite the `Name_Screening` example.
2. `project_dirs_for(cwd)`:
   - Build the candidate list: `cwd.absolute()`, then `cwd.resolve()` if it
     differs.
   - Try the exact slug of each candidate, in that order; return the first that
     exists as a directory.
   - In the fallback, compare each recorded `cwd` - passed through the existing
     `native_path()` - against **every** candidate, case-insensitively, with
     `\` and `/` treated as equal.
   - Look at up to **5** `.jsonl` files per folder, stopping at the first one
     that yields a recorded `cwd`, instead of only the first file.
3. `tests/hooks.py`: add a `SLUG_CASES` list of `(input, expected)` pairs, run
   after the existing hook cases, one printed line per case in the same format,
   counted in the final `N/M passed` total:
   - `C:\Users\me\Desktop\RedKeys\Name_Screening` -> `C--Users-me-Desktop-RedKeys-Name-Screening`
   - `C:\Users\me\Desktop\Legacy Modernization` -> `C--Users-me-Desktop-Legacy-Modernization`
   - `/home/me/my_proj (copy)` -> `-home-me-my-proj--copy-`
4. Run the **real-data check** below and paste its output into Report.

## Do not

- Change anything else in `_transcripts.py` - not the schema touch points, not
  `native_path()`, not `read_dirs()`.
- Change `usage.py` or `status.py`.
- Add `CLAUDE_CONFIG_DIR` support (deferred).

## Acceptance criteria

- [ ] `_slug()` maps every non-alphanumeric character to `-` and never resolves.
- [ ] The real-data check reports every transcript folder on this machine
      matching, or lists each mismatch with its recorded `cwd`.
- [ ] hooks suite: **26/26** (23 after T02, plus 3).
- [ ] `python scripts/usage.py --all` still runs and reports the same session
      count as before your change.

## Verify

```bash
python tests/hooks.py               # expected: 26/26 passed
python scripts/usage.py --all | head -6   # note the session count before AND after

# Real-data check - every folder's own recorded cwd must slug to its own name:
python - <<'EOF'
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
import _transcripts as tx
ok = bad = 0
for d in sorted(tx.PROJECTS_DIR.iterdir()):
    if not d.is_dir():
        continue
    cwd = next((c for j in list(d.glob("*.jsonl"))[:5] if (c := tx._peek_cwd(j))), None)
    if cwd is None:
        print("no cwd  ", d.name); continue
    got = tx._slug(tx.native_path(cwd))
    if got == d.name: ok += 1
    else: bad += 1; print("MISMATCH", d.name, "<-", cwd, "->", got)
print(f"{ok} match, {bad} mismatch")
EOF
```

## Commit

```
fix(T03): find transcripts on any path
- Slug every non-alphanumeric, as Claude Code does
- Try the logical path before the resolved one
- Fallback checks up to 5 transcripts per folder
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit:

**What changed**

**Verify output** (include the real-data check output in full)

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
