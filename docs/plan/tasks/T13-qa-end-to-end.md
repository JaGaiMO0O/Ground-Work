# T13 - QA: verify build 0.1A end to end, and report

Wave: 5
Depends on: T00, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T15, T16
Lane: QA
Estimate: L (~2 h)
Build: build-0.1A

## Goal

A written record of what 0.1A was verified to do, by running it the way a tester
will - and an equally plain record of what could not be verified.

## Why

Every defect found in three trials was found by **running** something, not by
reading it: the undo, the hooks, `usage.py` paths, the test detection. The suites
prove each rule in isolation; this proves the pieces work together on real
projects before anyone outside sees them.

## Owns

- `docs/plan/tasks/T13-qa-end-to-end.md` - Handoff only

**Nothing else in this repository.** Work only in copies under your system temp
directory. Do not modify `Desktop/JLGC - Copy` or any other real project - copy
it first. If you find a defect, **do not fix it**: record it under *Found, not
fixed* with exact reproduction steps. The lead turns it into a task.

## Do exactly this

Record every step's command and result in Handoff, as a table:
**check · result · evidence**.

1. **Regression.** In this repo: `python scripts/check.py`, then
   `tests/invariants.py` (expect 51), `tests/hooks.py` (26), `tests/adopt.py`
   (32), `tests/scan.py` (6).
2. **Transcript discovery.** Run the real-data check from T03's *Verify*.
   Expect every folder to match.
3. **Older Python.** `py -0`. If any Python below 3.12 is installed, run all four
   suites under the oldest one. If none is, say so - do not install one.
4. **Fresh project from a clone.** `git clone` this repo (the local path) into a
   temp directory - a clone, so tags come with it. Run
   `python scripts/init.py --project qa --profile general --purpose "verify 0.1A" --done "report written"`.
   Confirm: `check.py` exits 0; `docs/plan/`, `LICENSE` and `TESTING.md` are
   gone; README's first line is `# qa` and contains no clone URL.
5. **Second-generation adoption.** From that initialised clone, run
   `scripts/init.py --adopt <fresh small git repo> --purpose "second gen" --done "own goal"`.
   Confirm the target's AGENTS.md says `# Project:` with the target's name and
   `Purpose: second gen`, and does not contain `verify 0.1A`.
6. **Adopt and undo on JLGC.** Copy `C:\Users\myaghmour\Desktop\JLGC - Copy` to
   temp; `git status` must be clean there (commit in the copy if not). Hash every
   file (path + bytes, including empty directories). Run `--adopt --dry-run`,
   then `--adopt`. Record the detected test command - JLGC's tests are in
   `backend/tests` behind a `-r backend/requirements.txt` indirection, which T10
   should now detect. Run `check.py` in the target. Run `--undo`. Hash again.
   **Pass: the after-undo set equals the before set exactly.**
7. **The interview, live.** On a **second** fresh copy of JLGC, adopt, then follow
   the survey-area skill for one area. When the skill reaches *Ask before you
   write*, **ask the user the questions** - this is the one step in this task that
   needs the human - and record the answers as the skill says. Write the card.
   Confirm `check.py` passes with every claim cited or `(unverified)`, and paste
   the card into Handoff.
8. **Scan.** Run `python scripts/scan.py` in the JLGC copy from step 6 before
   undo. Confirm `_NUMERIC_TOKEN = re.compile(` is no longer reported.
9. **usage.py.** `python scripts/usage.py --all` runs and reports sessions.
10. **Could not verify.** List plainly: macOS, Linux, a real Java/Maven project
    (none on this machine), any Python version you could not run, and anything
    else you could not reach.

## Do not

- Fix anything. Handoff it.
- Edit any file in this repo except your Handoff.
- Use the real `JLGC - Copy` directory instead of a copy.

## Acceptance criteria

- [ ] Every step 1-10 has a row in the Handoff table with evidence.
- [ ] The JLGC undo hash comparison is shown, pass or fail.
- [ ] The interviewed card is pasted in full.
- [ ] *Found, not fixed* lists every defect with reproduction steps, or says none.

## Verify

The steps above are the verification. Summarise at the top of Handoff:
`N passed, M failed, K could not verify`.

## Commit

```
docs(T13): record 0.1A QA results
```

Stage only this task file. No `Co-Authored-By` trailer. Never push.

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
