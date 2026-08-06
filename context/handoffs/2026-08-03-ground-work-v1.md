# Handoff 2026-08-03 - Ground Work v1

**Goal:** turn a single design document into a working, general-purpose scaffold
for agent-assisted projects - one that makes work cheap, reproducible and easy to
hand over, aimed at people who have not driven an agent well before.

**Done:**

- **Phase 1** built a control repo for legacy modernization: Tier 0 router, area
  cards, templates, control-plane scripts, an adapter contract, `.claude` wiring,
  and a validator with a 17-case test suite.
- **Phase 2** generalized it. Domain-agnostic core plus `profiles/`; everything
  legacy-specific moved into `profiles/legacy-modernization/` and is still
  tested. Renames: `cartography/` to `map/`, `workspace.yaml` to `project.yaml`,
  *system card* to *area card*.
- **`usage.py`** reads real session transcripts and reports re-read hotspots,
  orientation share, cache efficiency, starting context and session growth.
- **`hooks/guard.py`** warns on the expensive habits as they happen and blocks
  six genuinely harmful actions.
- **`STATUS.md` + `status.py`**: human goal ladder above a marker, everything
  below generated from git, handoffs, `check.py` and `usage.py`.
- **`init.py --adopt`** brings the scaffold into an existing repo, detecting stack
  and commands and overwriting nothing.
- **Novice layer**: `START-HERE.md`, `docs/antipatterns.md`, `/onboard` skill.
- **Verified**: 35 invariant cases + 21 hook cases green; `check.py` clean after
  `init`; all scripts answer `--help`; ASCII-only console output; all doc links
  resolve; Tier 0 at ~706 tokens in 66 lines.

**Open:**

- The directory rename to `Ground Work` (see Blockers in `STATUS.md`).
- Nobody outside this session has used it. Untested against its actual audience.
- `db/oracle.sh` has never run against a live Oracle instance. Its own header
  says so. `db/postgres.sh` was only exercised to its exit-4 boundary.
- The gitleaks and trufflehog paths in `scan.py` are unexercised - neither binary
  is installed here. The regex fallback is fully tested.

**Key files:**

- `START-HERE.md` - the newcomer path, and the fastest way back into this
- `docs/playbook.md` - why it is shaped this way; changelog at the foot records
  what changed from the original document and why
- `docs/decisions/0002-general-core-with-profiles.md` - the Phase 2 decision;
  supersedes 0001, which still describes the legacy profile accurately
- `RUNBOOK.md` - setup, test, and the rough edges worth knowing
- `tests/invariants.py`, `tests/hooks.py` - the regression gate

**Gotcha:**

Four things cost real time and are recorded in `RUNBOOK.md` so they cost nothing
next time: test work directories must live **outside** the repo (Windows holds a
lingering git handle and `rmtree` fails mid-run); hook payloads must be built
with `json.dumps` because Windows backslashes are JSON escapes and a failed parse
makes the guard exit 0 - a test passing for the wrong reason; a blanket sed
turned `ROOT / "systems"` into `ROOT / "areas"` and quietly created a stray
directory found only in the final inventory; and `usage.py` originally costed
PDFs and images with `len(bytes)/4`, producing a headline of 1.6M wasted tokens
against an honest 348k. A fabricated headline is worse than no headline.

**Next:**

1. Rename the directory, then commit - the message is ready and git does not
   record the containing directory, so order does not matter.
2. Use it on one real project. `python scripts/init.py --adopt <repo>`.
3. Then `python scripts/usage.py` on that project a week later. If orientation
   share has not fallen, the cards are not being written or are not good enough,
   and that is the thing to fix - not more tooling.

## Picking this up on another device

```bash
git clone <your-repo-url> "Ground Work" && cd "Ground Work"
python scripts/check.py
python tests/invariants.py
python tests/hooks.py
```

`check.py` should exit 0. Both suites should be green. If they are, the clone is
sound and nothing else needs installing - Python 3.8+ and git are the only hard
requirements, and `RUNBOOK.md` lists what the optional extras buy you.

Then read, in this order: this handoff, `STATUS.md`, then `docs/playbook.md` only
if you want to argue with a decision.

**Not in the repo:** the approved Phase 2 plan lives at
`~/.claude/plans/okay-let-s-plan-out-glittery-treehouse.md` on the machine it was
written on. It is deliberately not committed - it describes work that is now done,
and the durable record is `docs/decisions/` for the *why* and this handoff for the
*state*. Copy it across if you want the archaeology; nothing depends on it.
