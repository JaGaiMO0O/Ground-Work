# T14 - Prepare the build-0.1A release

Wave: 9
Depends on: T13, T19, T20
Lane: Release
Estimate: S (~30 min)
Build: build-0.1A

## Goal

Testers can be handed 0.1A: TESTING.md tells them how to produce the one piece of
evidence the project lacks, the runbook and STATUS are current, and a handoff
records the release. The tag is created only when the user says so.

## Why

Two of the three blockers in STATUS.md - *the premise is unmeasured* and *never
used by a real newcomer* - cannot be closed by code. Only a rollout closes them,
and only if it produces a before-and-after measurement. TESTING.md's Track D
currently asks testers whether `usage.py` numbers "match their experience" - an
opinion, not a measurement. The last tester never reported back, so the evidence
has to be cheap to produce: two command runs, no writing.

## Owns

- `TESTING.md`
- `RUNBOOK.md` - the *Open defects* list and *Known rough edges* only
- `STATUS.md` - human zone, and the generated zone by running `scripts/status.py`
- `context/handoffs/<today>-build-0-1a-release.md` - new, via `scripts/handoff.py`
- `docs/plan/tasks/T14-release-0.1A.md` - Handoff only

## Do exactly this

1. **TESTING.md, Track D** becomes the measurement:
   - On the day you adopt, before working, run
     `python scripts/usage.py --path <your project> > usage-before.txt`.
   - Work normally on that project for two weeks.
   - Run it again into `usage-after.txt`, and post both in the Teams thread.
   - Use `--path`, **not** `--all`: `--all` lists every project on your machine,
     with file paths. Tell testers to read both files before posting.
   - Say plainly why: this is the evidence the project does not yet have, and a
     missing "after" file leaves the question open.
2. **RUNBOOK.md, Open defects**: remove the test-command detection entry and the
   `scan.py` false-positive entry **only if** T10 and T12 are `Merged` in
   `docs/plan/ROADMAP.md`. Add to *Known rough edges*: cards written under
   `build-0A` carry no citations and now fail `check.py`; add citations or mark
   claims `(unverified)`; there is no `--update` yet.
   **TESTING.md, before Track A** (not inside Tracks A-C): one tester note -
   on Windows, clone into a short path, or run
   `git config --global core.longpaths true` first; a deep folder (OneDrive,
   nested project dirs) fails with `Filename too long` (T13 F5).
3. **STATUS.md**, human zone: **Now** - `build-0.1A ready for a small rollout.`
   **Next** - the original tester re-runs tasks 1 and 4; rollout testers send
   before/after `usage.py` files. Set `reviewed:` to today. Leave **Done means**
   and the blockers' text unchanged. Run `python scripts/status.py`.
4. **Handoff**: `python scripts/handoff.py "build 0.1A release"`, then fill it in:
   - *Goal*: release 0.1A.
   - *Done*: one line per task T00-T20 with its commit hash (from `git log`);
     T13's summary line.
   - *Open*: T13's follow-ups F3-F6 (F1 and F2 are fixed by T19); the deferred list -
     `--update`; `.ps1` adapters on macOS; `CLAUDE_CONFIG_DIR`; nested `.csproj`;
     the dead `tests/invariants.py` allow entry in adopted `settings.json`;
     promoting cards from `usage.py` counts; an ADR correcting 0003's weight
     claim; on Windows, if `python` is missing but the Microsoft Store
     `python3` stub is on PATH, the hooks run the stub and fail visibly
     without blocking (found by T02).
   - *Gotcha*: copy the most important line from T13's Handoff.
   - *Next*: rollout with at least one Mac and one Java/Maven project; the
     original tester's re-test; the directory rename.
5. **Do not create the tag.** You are in a worktree; a tag made here would mark
   your branch, not `main`. Write the exact command in Handoff -
   `git tag -a build-0.1A -m "Build 0.1A - version 0.1, alpha"` - and the lead
   creates it on `main` after merging this task, only on the user's go-ahead.

## Do not

- Push anything, or create a tag.
- Change Tracks A-C of TESTING.md.
- Remove an Open defects entry whose fixing task is not `Merged` in the roadmap.

## Acceptance criteria

- [ ] Track D asks for two `usage.py --path` files and explains why.
- [ ] `check.py` exits 0; `status.py --check` up to date.
- [ ] The handoff lists every task with its commit.
- [ ] No tag created by this task; the tag command is in Handoff.

## Verify

```bash
python scripts/check.py              # expected: exit 0
python scripts/status.py --check     # expected: up to date
grep -n "usage.py --path" TESTING.md # expected: Track D
git tag -l "build-0.1A"              # expected: nothing - the lead tags main
```

## Commit

```
docs(T14): prepare build-0.1A release

- Track D measures usage before and after
- RUNBOOK, STATUS and handoff for 0.1A
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit: `task/T14-release-0.1A` - this commit, `docs(T14): prepare build-0.1A release`, on `9011466`.

**Tag - not created.** After merging, and only on the user's go-ahead, the lead runs on `main`:

```bash
git tag -a build-0.1A -m "Build 0.1A - version 0.1, alpha"
```

**What changed**

- `TESTING.md`: Track D is now the measurement. Testers run `usage.py --path <project>` into `usage-before.txt` on the day they adopt, and into `usage-after.txt` two weeks later, then post both. The section says why (the premise is unmeasured, and a missing "after" leaves it open), warns against `--all` (it lists every project, with paths), and says to read both files before posting. Before Track A: the Windows short-path / `core.longpaths` tester note (T13 F5). Tracks A-C are unchanged.
- `RUNBOOK.md`, *Open defects*: the `scan.py` `*_TOKEN` entry is removed (T12). The test-detection entry is replaced by T13 F3. T13 F4 is added. The lead-in now points at T13's Follow-ups. The "Neither risks data" evidence now includes T13's round trip and T19's undo-after-scan case. That leaves two entries.
- `RUNBOOK.md`, *Known rough edges*: `build-0A` cards fail `check.py` (add citations or mark `(unverified)`; there is no `--update` yet), and adopt prompts run together without a TTY (T13 F6).
- `STATUS.md`: Now is `build-0.1A ready for a small rollout.` Next is the original tester's re-run of tasks 1 and 4, plus the before/after `usage.py` files. `reviewed: 2026-10-27`. Done means and the blockers are unchanged. The generated zone was refreshed by `status.py`.
- `context/handoffs/2026-10-27-build-0-1a-release.md`: new, made with `handoff.py`. It lists T00-T20 with merge hashes, and covers T13's result, F3-F6, the deferred list, the Gotcha and Next.

**How it was verified**

- `python scripts/check.py`: exit 0, `all invariants hold`.
- `python scripts/status.py --check`: up to date.
- `grep -n "usage.py --path" TESTING.md`: both hits are in Track D.
- `git tag -l "build-0.1A"`: empty.
- Every hash in the handoff's Done list was checked twice: against ROADMAP's task table, and with `git log --oneline --first-parent main`. All 20 are present.
- The new RUNBOOK evidence claim (undo exact after `scan.py`) was checked against `tests/adopt.py:494` (`undo_after_scan_is_exact`).
- TESTING.md:48 ("Two defects") and :247 ("The two entries") still read true with two entries. Track B's "see the known defect first" (TESTING.md:191-192) now points at F3. README.md:71 ("two are already known") is still true and was not touched.

**Deviations** (escalations raised, and the answers)

- **ESCALATION T14 (step 2).**
  - Found: T10 and T12 are Merged, so the brief says to remove both Open defects entries. That would empty the list while TESTING.md:48 and :247 ("two"), Track B's "see the known defect first" (TESTING.md:191-192, which must not change) and README.md:71 (outside Owns) still point at it. T13 F3 is a live defect in the very layout Track B warns about.
  - Options: 1) empty the list and fix only TESTING.md; 2) replace the entries with F3 and fix the counts.
  - Answer: **option 2, modified** (the lead, approved by the user). Remove the `*_TOKEN` entry. Replace test detection with F3. Add F4, saying that `check.py` exits 2 on warnings. Point the lead-in at T13's Follow-ups F3 and F4, and drop the 2026-08-16 handoff pointer. Update the "Neither risks data" evidence (T13 round trip; T19 undo after `scan.py`). Two entries remain, so TESTING.md:48 and :247 stay as written, and README is not touched (no follow-up for it). Also add F6 as one line under Known rough edges.
- The handoff's Gotcha uses T13's step-6 failure line, with "(fixed by T19)" added so a reader does not take it for an open defect.

**Follow-ups** (found, not fixed - file and line)

- None.

**Rollback**

Revert this commit (`git revert <hash>`). It touches only docs: `TESTING.md`, `RUNBOOK.md`, `STATUS.md`, the new handoff and this Handoff. No code or tests change. If the tag was created first, delete it with `git tag -d build-0.1A` before reverting (and from any remote it was pushed to).
---

## Lead review

<!-- Lead only. -->
