# T14 - Prepare the build-0.1A release

Status: ready
Wave: 6
Depends on: T13
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

## Files you may change

- `TESTING.md`
- `RUNBOOK.md` - the *Open defects* list and *Known rough edges* only
- `STATUS.md` - human zone, and the generated zone by running `scripts/status.py`
- `context/handoffs/<today>-build-0-1a-release.md` - new, via `scripts/handoff.py`
- `context/tasks/T14-release-0.1A.md` - Report section and Status line only

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
   `scan.py` false-positive entry **only if** T10 and T12 are `accepted` - check
   their `Status:` lines. Add to *Known rough edges*: cards written under
   `build-0A` carry no citations and now fail `check.py`; add citations or mark
   claims `(unverified)`; there is no `--update` yet.
3. **STATUS.md**, human zone: **Now** - `build-0.1A ready for a small rollout.`
   **Next** - the original tester re-runs tasks 1 and 4; rollout testers send
   before/after `usage.py` files. Set `reviewed:` to today. Leave **Done means**
   and the blockers' text unchanged. Run `python scripts/status.py`.
4. **Handoff**: `python scripts/handoff.py "build 0.1A release"`, then fill it in:
   - *Goal*: release 0.1A.
   - *Done*: one line per task T00-T12 with its commit hash (from `git log`);
     T13's summary line.
   - *Open*: every item under T13's *Found, not fixed*; the deferred list -
     `--update`; `.ps1` adapters on macOS; `CLAUDE_CONFIG_DIR`; nested `.csproj`;
     the dead `tests/invariants.py` allow entry in adopted `settings.json`;
     promoting cards from `usage.py` counts; an ADR correcting 0003's weight
     claim.
   - *Gotcha*: copy the most important line from T13's Report.
   - *Next*: rollout with at least one Mac and one Java/Maven project; the
     original tester's re-test; the directory rename.
5. **Tag - only on explicit instruction.** Prepare, but do **not** run, this
   command; show it to the user and run it only if they say yes in this session:
   `git tag -a build-0.1A -m "Build 0.1A - version 0.1, alpha"`. Never push the
   tag or any branch.

## Do not

- Push anything.
- Change Tracks A-C of TESTING.md.
- Remove an Open defects entry whose fixing task is not `accepted`.

## Acceptance criteria

- [ ] Track D asks for two `usage.py --path` files and explains why.
- [ ] `check.py` exits 0; `status.py --check` up to date.
- [ ] The handoff lists every task with its commit.
- [ ] The tag exists only if the user said yes - Report records which.

## Verify

```bash
python scripts/check.py              # expected: exit 0
python scripts/status.py --check     # expected: up to date
grep -n "usage.py --path" TESTING.md # expected: Track D
git tag -l "build-0.1A"              # expected: present only if approved
```

## Commit

```
docs(T14): prepare build-0.1A release
- Track D measures usage before and after
- RUNBOOK, STATUS and handoff for 0.1A
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit:

**What changed**

**Verify output**

**Tag created?** (yes / no, and the user's words)

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
