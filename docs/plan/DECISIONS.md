# Decisions - build-0.1A

Numbered, dated, settled. **Task sessions never reopen these.** A decision that
turns out wrong gets a new number that supersedes it; the old entry stays.

Architecture-level decisions that outlive a release are ADRs in `docs/decisions/`.
These are the release's working calls.

---

**D-01 - 0.1A scope** *(2026-10-04)*
Fix what would hurt or mislead a rollout tester, and the card-trust flaws the
external review found. The blockers *premise unmeasured* and *never used by a
real newcomer* are closed only by a rollout; 0.1A makes them measurable and does
not claim to solve them.

**D-02 - Task-driven cards are in 0.1A** *(2026-10-04)*
ADR 0004 ships in this release (T11), with an interview step before a card is
written (contract C4). Rolling out the old "survey up front" instructions would
have had testers pay the 39-task-payback path the review measured.

**D-03 - Review verdicts** *(2026-10-04)*
Adopted: card is a map; diagnosis exception; enforced citations; skip list never
binds diagnosis; edit a card only with a citation; second-gen setup fix; budget
2,500; ADR 0004; re-test of review tasks 1 and 4.
Adapted: per-claim confidence -> the `(unverified)` marker; "reject skip entries
that say live" -> warn when a listed path is referenced elsewhere.
Rejected: filling the template's own purpose/done - it is deliberately unfilled.

**D-04 - Release label `build-0.1A`** *(2026-10-04)*
Docs never hardcode a label; they say "quote `git describe --tags`". The adoption
manifest records `git describe --tags --always`.

**D-05 - Card contracts C1-C4** *(2026-10-04, rulings added at the wave-1 gate)*
As written in `PROTOCOL.md`. Rulings: a claim includes its continuation lines; a
bare `-` is exempt; a C2 reason is what remains after removing every backticked
span, and each backticked path is reference-checked.

**D-06 - The project is what git says it is** *(2026-10-04)*
Adoption (T01) and the skip-list reference check (T15) take their file list from
git - tracked plus untracked-not-ignored - not from a disk walk. Live worktrees and
ignored local files are never part of the template. `scan.py` is the exception: a
secret scanner should read untracked files.

**D-07 - Task sessions start from app chips** *(2026-10-04)*
The app creates each session's worktree, replacing `git worktree add`. The session
fast-forwards to `main` first (the app can start from the last pushed commit),
then renames its branch to `task/Txx-<slug>`. The app's branch prefix is `task`.

**D-08 - Merging** *(2026-10-04, from wave 3)*
After the user's review: `git merge --no-ff -m "chore(Txx): merge <branch>"`,
delete the branch, remove the worktree from the main folder, push. Waves 0-2 were
fast-forwarded or cherry-picked before this standard applied; that history stands.

**D-09 - Plan location** *(2026-10-04)*
Plan artifacts live in `docs/plan/` (ROADMAP, DECISIONS, PROTOCOL, tasks/).
`CLAUDE.md` stays a one-line pointer to `AGENTS.md`: it travels into every adopted
project, so the protocol and lanes live in `PROTOCOL.md` instead. `docs/plan/`
never reaches an adopted project (T16).

**D-10 - Commit format** *(2026-10-04)*
Conventional Commits; first line 50 characters or fewer; one blank line; short
bullets; no `Co-Authored-By` trailer or other attribution.

**D-11 - Gap tests deferred to the next release** *(2026-10-04)*
The test harnesses are case tables with no expected-failure mechanism. Adding one
mid-release would touch every suite; it becomes a task in the next release.

**D-12 - How 0.1A is validated** *(2026-10-04)*
The original tester re-runs review tasks 1 and 4 on their codebase. The rollout's
evidence is `usage.py --path <project>` before and after two weeks of ordinary
work (T14, Track D) - `--path`, never `--all`, which lists every project on the
tester's machine.

**D-13 - Pushing** *(2026-10-04; superseded by D-14)*
`main` is pushed to `origin` after every merge, so the remote matches and new
worktrees start current.

**D-14 - Remotes** *(2026-10-04, user decision)*
`origin` is the internal GitLab (`gitlab.optimizasolutions.com/myaghmour/ground-works`),
for both fetch and push - the canonical remote, and what the app starts worktrees
from. `github` (`JaGaiMO0O/Ground-Work`) is the backup and the route in from
outside the company network. After every merge, `main` is pushed to **both**.
`origin` had a `pushurl` pointing at GitHub, which is why pushes never reached
GitLab and worktrees started stale; it was removed. `old-origin` duplicates
`github` and is left alone.
