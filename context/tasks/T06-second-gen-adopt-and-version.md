# T06 - Stop second-generation adoption leaking purpose; stamp the build label

Status: done
Wave: 2
Depends on: T01
Build: build-0.1A

## Goal

Adopting from a copy that has already been initialised gives the target **its
own** project name, purpose and done - never the source's. The adoption manifest
records the build label (`build-0.1A`), not a bare commit hash.

## Why

Verified bug, from the external review (finding 4). `personalized_agents()`
(`scripts/init.py:104-118`) fills AGENTS.md by **substituting placeholder
tokens** (`PROJECT_TOKEN`, `PURPOSE_RE`, `DONE_RE`, `:51-53`). Once a copy has run
`init.py`, those tokens are gone. Adopting from that copy then:

- leaves the source's `# Project:`, `Purpose:` and `Done =` lines in the target,
- silently drops the `--purpose` / `--done` the user gave,
- and `unfilled()` (`:121-125`) finds no placeholder, so no warning fires and
  `check.py` passes.

That is "carry templates, never content" a fourth time, in the file every
session reads first. Second-generation adoption is the **normal** path as soon as
more than one person uses this. No case in `tests/adopt.py` covers it - every
case adopts from this repo, whose AGENTS.md is still template text.

The fix has precedent in the same file: the README title and `project:` /
`profile:` lines are already set **by line**, not by token
(`init.py` README H1 handling and `project.yaml` handling).

`template_version()` (`:483-489`) records `git rev-parse --short HEAD`. A tester
can't tell `9c1e2f4` is 0.1A.

## Files you may change

- `scripts/init.py`
- `tests/adopt.py`
- `context/tasks/T06-second-gen-adopt-and-version.md` - Report section and Status line only

## Do exactly this

1. In `scripts/init.py`, define the two placeholder lines exactly as they appear in
   this repo's `AGENTS.md` today:
   `Purpose: <ONE SENTENCE - what this project is for>` and
   `Done = <ONE SENTENCE - how we know it is finished>`.
2. Rewrite `personalized_agents()` to **set lines by pattern**, each with
   `re.sub(..., count=1, flags=re.M)` and a `lambda` replacement (a project name
   or purpose may contain backslashes):
   - `^# Project:.*$` -> `# Project: {project}`
   - `^Purpose:.*$` -> `Purpose: {purpose}` if given, else the placeholder line
   - `^Done =.*$` -> `Done = {done}` if given, else the placeholder line
   Writing the placeholder back when nothing is given is the point: the target
   then fails `check.py` loudly instead of inheriting someone else's goal.
   Keep the `DB_ROLE_TOKEN` replacement as it is.
3. Leave `unfilled()` token-based - after step 2 it detects the right thing.
   If `PURPOSE_RE` / `DONE_RE` are no longer used anywhere, delete them.
4. Plain `init.py` must keep working exactly as before for a first-generation
   project. Confirm it does not delete `STATUS.template.md`; if it does, stop
   deleting it - second-generation adoption renders the target's STATUS.md from
   that file.
5. `template_version()`: return the output of `git describe --tags --always`
   run in `ROOT`, or `"unknown"` if git fails. Update its docstring.
6. In `tests/adopt.py`, reuse the helper T01 added that runs a given template's `init.py`
   (not only this repo's), and three cases:

   | Case | Harness argv | Assertion |
   |---|---|---|
   | second-gen keeps target purpose | `["--help"]` | see below |
   | second-gen, nothing given | `["--help"]` | see below |
   | manifest records git describe | `FILLED` | `template_version` in the target's `.adopt-manifest.json` equals `git describe --tags --always` run in this repo |

   `["--help"]` makes the harness's own run a no-op (precedent: the "undo refuses
   with no record" case). Each second-gen assertion then:
   - copies this repo's **tracked** files (`git ls-files`) into a directory under
     the harness's temp dir, and runs that copy's `init.py --project src-proj
     --profile general --purpose "SOURCE PURPOSE" --done "SOURCE DONE"`;
   - builds a fresh target with `make(...)`;
   - runs the **copy's** `init.py --adopt <target>`:
     - *keeps target purpose*: with `--purpose "TARGET PURPOSE" --done
       "TARGET DONE"`. Assert the target's AGENTS.md has `# Project:` with the
       target's name, `Purpose: TARGET PURPOSE`, `Done = TARGET DONE`, and
       contains neither `SOURCE`. Assert the target's STATUS.md does not contain
       `SOURCE PURPOSE`.
     - *nothing given*: no `--purpose` / `--done`. Assert AGENTS.md contains
       `<ONE SENTENCE` and does not contain `SOURCE`, and that the adopt exits 1.

7. Fix the message printed after plain `init.py` removes template-only paths
   (around `scripts/init.py:762-763`, "licence and testing brief are yours to
   write"). Since T01 it also removes `context/tasks/`, so the message must
   describe everything removed. Found by T01's worker.

## Do not

- Change how `--adopt` copies files, or the manifest's other fields.
- Touch the README H1 or `project.yaml` handling - they are already correct.
- Change `scripts/_adopt.py`.

## Acceptance criteria

- [ ] Both second-gen cases fail on the code as it is before your change - run
      them first and say so in Report - and pass after.
- [ ] Adopt suite: **26/26** (23 + 3).
- [ ] A first-generation `init.py` on a fresh copy still fills AGENTS.md and
      README as before (the existing cases cover this).

## Verify

```bash
python tests/adopt.py --only second-gen   # expected: 2/2 passed
python tests/adopt.py --only manifest     # expected: passes
python tests/adopt.py                     # expected: 26/26 passed
python scripts/check.py                   # expected: exit 0
git describe --tags --always              # the value the manifest must carry
```

## Commit

```
fix(T06): stop second-gen adopt leaking purpose
- Set Project/Purpose/Done lines by pattern
- No value writes the placeholder back
- Manifest records git describe, not a bare sha
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: the `fix(T06): stop second-gen adopt leaking purpose` commit on
branch `T06-second-gen-adopt-and-version` (hash given to the user; a commit
cannot carry its own hash).

**What changed**

- `scripts/init.py`
  - Added `PURPOSE_LINE` / `DONE_LINE`, the two placeholder lines exactly as in
    `AGENTS.md`. Deleted `PURPOSE_RE` / `DONE_RE`, which are no longer used.
  - `personalized_agents()` sets `# Project:`, `Purpose:` and `Done =` with
    `re.sub(..., count=1, flags=re.M)` and lambda replacements. With no purpose
    or done, it writes the placeholder line back. `DB_ROLE_TOKEN` replacement
    is unchanged. `unfilled()` is unchanged and token-based.
  - `template_version()` returns `git describe --tags --always` in `ROOT`, or
    `"unknown"`. Docstring updated.
  - Step 7: the message after removing template-only paths now names all
    three: licence, testing brief and task log.
  - Step 4: plain init does **not** delete `STATUS.template.md`. Its deletions
    are `TEMPLATE_ONLY_FILES` (`LICENSE`, `TESTING.md`), `TEMPLATE_ONLY_DIRS`,
    the examples, unused profiles and the applied scaffold. Confirmed on a
    disk copy: `second-gen-src/STATUS.template.md` is still there after the
    fixture's plain init. No change needed.
- `tests/adopt.py`: three cases, using T01's `run_template_init()`.
  - `second_gen_source()` copies `git ls-files` into
    `BASE/second-gen-src` and runs that copy's plain init with `SOURCE ...`
    values. A non-zero exit is reported as a fixture error.
  - `second-gen keeps target purpose`, `second-gen, nothing given` and
    `manifest records git describe` assert what step 6 lists. Targets come
    from `make(98)` and `make(97)`.

Before the change, run first, all three failed for the reason the task gives:
- `second-gen keeps target purpose`: "the target's name did not reach the
  router". The copy's `# Project: src-proj` survived.
- `second-gen, nothing given`: "the placeholders were not written back".
- `manifest records git describe`: `template_version is 'd0c3f9f', wanted
  'build-0A-8-gd0c3f9f'`.

**Verify output**

```
python tests/adopt.py --only second-gen   -> 2/2 passed
python tests/adopt.py --only manifest     -> 1/1 passed
python tests/adopt.py                     -> 26/26 passed in 104s
python scripts/check.py                   -> "ok   all invariants hold", exit 0
git describe --tags --always              -> build-0A-8-gd0c3f9f
```

First-generation init still works. The 23 existing cases pass, and the
second-gen fixture's own plain init exits 0 and fills `AGENTS.md`.

**Deviation requests**

None. One setup note: the app created this worktree's branch at `1a79a04`,
8 commits behind `main` and with no `context/tasks/`. I fast-forwarded it
(`git merge --ff-only main`, now at `d0c3f9f`) before reading the task. No
history was rewritten, and there were no commits of mine at that point.

**Found, not fixed**

- `tests/adopt.py`: `run_template_init()` and the harness's own
  `subprocess.run` in `main()` do not set `stdin`, so the child inherits the
  caller's. `adopt()` (`scripts/init.py:294`) prompts when `sys.stdin.isatty()`
  and purpose or done is missing. So when the suite runs from an interactive
  terminal, `unfilled Tier 0 is an error` and the new `second-gen, nothing
  given` can block on a hidden prompt, because the prompt goes into the
  captured stdout. Not seen here: the tool shell's stdin is not a TTY.
  Suggested fix: `stdin=subprocess.DEVNULL` in both calls.
- The repo's only tag is `build-0A`, so `git describe` gives
  `build-0A-8-g...`. The manifest shows `build-0.1A` only after T14 tags the
  release.

---

## Lead review

<!-- Lead only. -->
