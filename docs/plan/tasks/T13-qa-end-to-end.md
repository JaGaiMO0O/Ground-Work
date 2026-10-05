# T13 - QA: verify build 0.1A end to end, and report

Wave: 6
Depends on: T00, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T15, T16, T17, T18
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
   (32), `tests/scan.py` (8), and
   `python scripts/scan.py` itself (expect exit 0).
2. **Transcript discovery.** Run the real-data check from T03's *Verify*.
   Expect every folder to match.
3. **Older Python.** `py -0`. If any Python below 3.12 is installed, run all five
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
   Then the T17 check: make `<temp>/build/repo/`, a fresh `git init` with one
   file `a.py` holding `DB_PASSWORD=s3cr3tValue9`, copy `scripts/` into it, and
   run `python scripts/scan.py` there. **Pass: it reports 1 `password-property`.**
   With no baseline yet, the first run records it and exits 0 - expected. A
   report of no findings is a security failure - say so at the top.
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

Branch / commit: `task/T13-qa-end-to-end` - this commit, `docs(T13): record 0.1A QA results`, on `c67889d`.

**Summary: 7 passed, 1 failed, 2 could not verify.**

- **The failure is step 6.** After undo, the tree is not byte-identical to before. It has one extra file, `.secrets-baseline`. The step-8 `scan.py` run (which the brief orders before undo) wrote it, and undo leaves it in place without saying so.
- **A control round trip passed.** Adopt, then `check.py`, then undo, with no scan, gives a byte-identical working tree.
- **No security failure.** The T17 check reports its secret.

**What changed**

Only this Handoff. Everything ran in copies under `%TEMP%\t13`. Nothing in this repo, in `Desktop\JLGC`, or in any other real project was modified.

**How it was verified**

Machine: Windows 11, Python 3.12.10 (`python`). All work was under `%TEMP%\t13` = `C:\Users\myaghmour\AppData\Local\Temp\t13`.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | `python scripts/check.py` | pass | exit 0, `ok all invariants hold` |
| 1 | `tests/invariants.py` (51) | pass | `51/51 passed in 114s` |
| 1 | `tests/hooks.py` (26) | pass | `26/26 passed` |
| 1 | `tests/adopt.py` (32) | pass | `32/32 passed in 89s` |
| 1 | `tests/scan.py` (8) | pass | `8/8 passed`, including `repo under a build folder  password-property` |
| 1 | `python scripts/scan.py` | pass | exit 0, `ok no new findings (2 known, regex-fallback, history=False)` |
| 2 | T03 real-data transcript check | pass | `51 match, 0 mismatch`. One `no cwd` folder, `C--Users-myaghmour-Downloads-OptimizaIPsHub`, holds only `memory/` and no `.jsonl`, so there is nothing to match. |
| 3 | `py -0`, suites under Python < 3.12 | **could not verify** | Installed: 3.14.3 and 3.12. Nothing below 3.12, and none was installed. |
| 4 | Fresh project from a clone | pass | `git clone <worktree> %TEMP%\t13\clone`, which brought tag `build-0A`. `init.py --project qa ...` exit 0. `check.py` exit 0. `docs/plan`, `LICENSE` and `TESTING.md` are gone. README line 1 is `# qa`, and grep finds no `git clone`, `http`, `gitlab` or `github`. |
| 5 | Second-gen adoption | pass | Fresh `git init` repo `smallrepo` with `app.py`. `clone/scripts/init.py --adopt ... --purpose "second gen" --done "own goal"` exit 0. AGENTS.md: `# Project: smallrepo` / `Purpose: second gen` / `Done = own goal`. `verify 0.1A` and `report written` appear nowhere in the target. Manifest `template_version: build-0A-37-gc67889d`. |
| 6 | JLGC adopt -> undo round trip | **FAIL** (strict) | Hashes are below. Before: 270 entries. After undo: 271. The only difference is `+ .secrets-baseline`, written by step 8's `scan.py`. Dry-run left the tree byte-identical. Detected test command: `test: pytest` (from `requirements.txt` via `-r backend/requirements.txt`), as T10 specifies, but see F3. `check.py` in the target: `0 errors, 2 warning(s)`, exit 2 (warnings: `.secrets-baseline` missing, `.env.example` not tracked). Control round trip (adopt, check, undo, no scan): working tree byte-identical. |
| 7 | Interview, live | pass | Second clone `jlgc7`. Adopted, `new_card.py backend`, surveyor subagent, 5 questions asked in one message, and answered by myaghmour on 2026-10-05. Card written and `survey: true` set. `check.py`: `0 errors, 3 warning(s)` (1 card warning, see F4; 2 safety warnings as in step 6). Negative control: removing one citation gave `FAIL ...CARD.md:45: claim has no citation`, then restored. Card is about 1.2k tokens of the 2,500 budget. Full card below. |
| 8 | `scan.py` in the JLGC copy, before undo | pass | exit 0, `ok no findings (regex-fallback, history=False)`. `_NUMERIC_TOKEN = re.compile(` (`backend/extractors.py:32`) is not reported. |
| 8 | T17: repo under `build/` | pass | `%TEMP%\t13\build\repo`: `git init`, `a.py` = `DB_PASSWORD=s3cr3tValue9`, `scripts/` copied in. First run reported `1  password-property` and recorded it in the baseline (`a.py:1`), exit 0. Second run: `no new findings (1 known)`, exit 0. |
| 9 | `python scripts/usage.py --all` | pass | exit 0, `146 session(s) across 51 project(s) [147 transcript file(s) read]` |
| 10 | Could not verify | **could not verify** | See the list below. |

*Step 6: JLGC undo hash comparison.*

The listing has one line per file (`sha256 path`) plus `DIR-EMPTY path/` per empty directory. That covers the whole clone, `.git/` included, sorted by path. The hasher is `%TEMP%\t13\hashtree.py`.

| Set | Entries | sha256 of listing | Working tree only (`.git/` excluded) |
|---|---|---|---|
| Before (clean clone, af69375) | 270 (5 empty dirs) | `31e7ef094bf631171168259fb7461a5235807bc12631ecda5e850af1c9fac160` | `c0f51f9343ce86afef348c9dc4799b27cb5be6208f2360bbe6db5ef02e7340da` |
| After undo (adopt, check, scan, undo) | 271 | `91bc948aa1f1d4b5f66fb13ed6306061f692cb623916ec6488e5a97439845b3f` | `5b24862bee9fd9fa6dd72434c21273b15e24d371e07665cfaf595e3fc1835004` |
| Same set, `.secrets-baseline` removed | 270 | - | `c0f51f93...` = **equal** to before |
| Control: start (baseline deleted) | 270 | `cmp` equal to before | equal |
| Control: after undo (adopt, check, undo) | 270 | `18d4e747a68a665f07b1c298746c46aa2a3963c6de81bd0163062abd94c931bb` | `c0f51f93...` = **equal** to before |

- `diff before after`: `> a4291ce6... .secrets-baseline`, and nothing else.
- `diff before after_control`: `.git/index` only. That is git's stat cache, rewritten because undo restores `.gitignore` with a new mtime. `git diff --cached --quiet` (entries equal HEAD), `git diff --quiet`, and `git status --short --ignored` are all empty.
- Undo output both times: `removed 52 file(s) and 25 directory(ies)` / `restored .gitignore to the bytes it had before adoption`.

*Step 7: the interviewed card* - **redacted by the lead** (the user's call, 2026-10-05).
JLGC is a separate project, so its card and the interview answers stay out of this
repo. The card stays in the temp clone at `%TEMP%\t13\jlgc7\map\backend\CARD.md`.

| Measure | Value |
|---|---|
| sha256 | `91352759a01b7f969c66dfcb0b02db984a70537ff2e6851e8528f78647cf3a5c` |
| Size | 58 lines, 583 words, about 1.2k of the 2,500-token budget |
| Claims under Owns / Interfaces / Landmines | 25, every one with a `path:N` citation |
| Claims carrying an interview answer `(per myaghmour, 2026-10-05)` | 9 |
| Claims marked `(unverified)` | 2 |
| `## Open questions` | 2: one question answered "unknown", one answered in part |
| Do not read | 1 entry, with a reason (it raised the F4 warning) |
| Interview | 5 questions, asked in one message and answered by myaghmour |

*Step 10: could not verify*
- macOS, and therefore the `.ps1` -> `pwsh` path (a known issue). None on this machine.
- Linux. None on this machine.
- A real Java/Maven project, including `mvnw.cmd`. None on this machine.
- Python below 3.12. None installed; the harness's < 3.12 branch is still unexercised.
- Git history scanning: no gitleaks or trufflehog on PATH, so every scan was the working-tree regex fallback.
- Running JLGC's tests. pytest is not installed, and installing it was out of scope. So `pytest` from the root versus from `backend/` (F3) was not run; it rests on the owner's answer and static reading.
- The live `Desktop\JLGC` working tree, by the lead's instruction. Its uncommitted, untracked and ignored files were not exercised.

**Deviations** (escalations raised, and the answers)

- **ESCALATION T13 (step 6).**
  - Found: `C:\Users\myaghmour\Desktop\JLGC - Copy` does not exist. Only the live `Desktop\JLGC` does, with 5 modified and 2 untracked files.
  - Options: 1) copy the live JLGC and commit a snapshot in the copy; 2) recreate "JLGC - Copy"; 3) mark steps 6-8a as could not verify.
  - Answer: option 1, modified. The source is the live `Desktop\JLGC`, read through git only. Each copy was made with `git clone --no-hardlinks "C:\Users\myaghmour\Desktop\JLGC" "%TEMP%\t13\<name>"` followed by `git remote remove origin`, giving HEAD `af69375`. There was no snapshot commit. Clone `jlgc6` served steps 6 and 8; clone `jlgc7` served step 7. The lead called the wrong path a lead error in the brief.
  - Before that answer, one read-only `ls` and `git status` of the live folder had already been run to write the escalation. Nothing was written there.
- **Temp location.** The first step-4 clone, into the session scratchpad (a path of about 190 characters), failed with `Filename too long` (see F5). All work moved to `%TEMP%\t13`, which is still the system temp directory.
- **Step 6 `--purpose` / `--done`.** The brief gives no values for JLGC. Dry-run was run without them; stdin was not a TTY, so both were skipped. The real adopt passed `--purpose "JLGC QA copy" --done "undo verified"`, and step 7 passed `"JLGC QA interview copy"` / `"card passes check"`.
- **Step 6 control.** I added a second round trip on the same clone, after deleting `.secrets-baseline`, to separate adoption from the scan. It is evidence only; the strict result stays FAIL.
- **Step 7 `check.py` exit code** is 2 (warnings), not 0. It has 0 errors. The warnings are F4 and the two safety warnings that every fresh adoption carries. `scan.py` was not run in `jlgc7`, because the skill limits that session's outputs to the card and `project.yaml`.

**Follow-ups** (found, not fixed - file and line)

- **F1 - undo silently leaves `.secrets-baseline`.** (This is the step-6 FAIL.) `init.py --adopt`'s "Next" step 4 tells the user to run `python scripts/scan.py`, which writes `.secrets-baseline` at the target root. `--undo` does not remove it or mention it. Its output promises to keep "anything you have edited since and saying which", but a file the scaffold's own script created is neither removed nor named, so the target is left with a stray file. Reproduction:
  1. `git clone <any repo> %TEMP%\x`
  2. `python scripts/init.py --adopt %TEMP%\x --purpose p --done d`
  3. `cd %TEMP%\x && python scripts/scan.py`
  4. `python <template>/scripts/init.py --undo %TEMP%\x`
  5. `git -C %TEMP%\x status --short` shows `?? .secrets-baseline`.

  Relevant code: undo is at `scripts/init.py:509`. The lead decides whether undo should remove it, name it, or whether this belongs in the brief's step order.
- **F2 - the printed undo command only works from the target's parent directory.** `scripts/init.py:444` prints `python scripts/init.py --undo {target.name}`, a bare basename. Run as printed from the template directory, it fails. Reproduction: adopt `%TEMP%\t13\jlgc6` from the template folder, then run the printed `python scripts/init.py --undo jlgc6` there. Result: `FAIL ...\vigorous-cori-5a3050\jlgc6 is not a directory`, exit 1. It works with the full path. Step 5 printed `--undo smallrepo` in the same way.
- **F3 - the detected `test: pytest` will not work from the repo root for JLGC** (unverified by running; pytest is not installed). Detection follows T10's spec (`scripts/_adopt.py:200-215`) and writes plain `pytest` to `project.yaml` and `RUNBOOK.md:23-26`, flagged `DETECTED, NOT VERIFIED`. But JLGC's tests import top-level modules (`backend/tests/test_async_api.py:3-6`: `from main import app`), and backend has no `conftest.py`, `pytest.ini` or `__init__.py`. The owner confirms tests are run from `backend/` (per myaghmour, 2026-10-05). When the tests sit under a nested directory such as `backend/tests`, the right command is probably `cd backend && pytest`. Reproduction: adopt a JLGC clone at af69375, then `grep -A1 '^commands' project.yaml` gives `test: pytest`.
- **F4 - the C2 reference check counts the scaffold's own scripts as project code.** `scripts/check.py:432` builds `code_files()` with `scripts/` included, so a Do-not-read entry for `backend/tests/__pycache__/` warns `referenced from scripts/_lib.py`, because of `scripts/_lib.py:580` `"__pycache__/"`. The same will happen for any name the scaffold mentions, such as `build`, `dist` or `node_modules`. Reproduction: on any adopted `kind: local` area, add `` - `x/__pycache__/` - compiled bytecode, not tracked by git `` under Do not read and run `check.py`.
- **F5 - a clone into a deep directory fails on Windows.** The longest tracked path is 78 characters (`profiles/legacy-modernization/scaffold/context/recipes/no-boundary-contract.md`). `git clone` into a parent about 190 characters long fails with `Filename too long` / `Clone succeeded, but checkout failed`. `core.longpaths` is not set globally; here it is `true` only in this worktree's `config.worktree`, which a fresh clone does not inherit. Testers cloning into deep folders such as OneDrive or nested project dirs will hit it. Candidate: a README note, or shorter profile paths. Reproduction: `git clone <repo> "<a ~190-char path>\qa\clone"`.
- **F6 - cosmetic: the prompts run together when stdin is not a TTY.** `--adopt --dry-run` without `--purpose`/`--done` prints `Purpose (one sentence):   Done = (one sentence): ` on one line, with nothing after it (`scripts/init.py:664-665`). Reproduction: `python scripts/init.py --adopt <repo> --dry-run < /dev/null`.
- **Note, not a defect:** after undo restores `.gitignore` (bytes equal, mtime new), git's next command rewrites `.git/index` stat data, so a `.git/`-inclusive hash can differ while the index entries equal HEAD. If the go/no-go wants byte equality including `.git/`, the criterion should say working tree plus `git status` clean.

**Rollback**

Revert this commit (`git revert <hash>`). Only this Handoff changes. The scratch copies under `%TEMP%\t13` are disposable and can be deleted at any time.

---

## Lead review

<!-- Lead only. -->
