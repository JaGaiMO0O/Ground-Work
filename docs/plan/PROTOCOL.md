# Protocol - lead and task sessions

Release work on Ground Work runs as one **lead** session and one **task session**
per task. This file is the session protocol, the lane table and the shared
contracts. Status lives in [ROADMAP.md](ROADMAP.md) and is edited by the lead
only. Settled calls are in [DECISIONS.md](DECISIONS.md) and are not reopened.

Nothing under `docs/plan/` travels into a project made from the template - it is
Ground Work's own work log (T16 enforces it).

Briefs T00-T10 and T15 were written before the move from `context/tasks/` on
2026-10-04. Their text still names that path: it is history, not instruction.

---

## Roles

- **Lead** - writes the plan, the briefs and the decisions; reviews and verifies
  every task; answers escalations; owns the roadmap status. It does not implement
  task scope. Small lead fixes (docs, briefs, a stale fixture) are allowed and
  always recorded in the roadmap's status log.
- **Task session** - one per task, started from its brief. Implements exactly that
  brief.
- **Operator** - anything needing production access or credentials is run by the
  user, who pastes the output. No session asks for secrets.

---

## If you are a task session

### Start

You were started from a task chip, so you are in your own git worktree.

1. `git merge --ff-only main`. If it is not a fast-forward, stop and tell the
   user. (The app can start a worktree from an older commit than `main`.)
2. `git branch -m task/Txx-<slug>` - your brief's file name without `.md`,
   prefixed `task/`. Example: `task/T16-plan-stays-home-npm-install`.
3. Read `AGENTS.md`, this file, then your brief. After that, only the files your
   brief names. Do not survey the repo.
4. **Dependency gate:** every task under your brief's *Depends on* must be
   `Merged` in `docs/plan/ROADMAP.md`. If one is not, stop and say which.

### Scope

Stay inside your brief's *Scope* and *Owns*. Write the test first when behaviour
changes. Run `python scripts/check.py` before every commit.

Anything you notice outside your task goes under Handoff -> **Follow-ups**, with
file and line. Do not fix it: a task that fixes things in passing cannot be
reviewed.

### Stop and escalate - do not improvise

Stop when:

- the baseline is red before you have changed anything;
- the fix needs a migration, a dependency, or a file outside *Owns*;
- a rule in your brief conflicts with how the code really behaves;
- you have spent more than 1.5x your brief's *Estimate*.

Send the user exactly this, then wait for an explicit answer:

```
ESCALATION Txx
Found:          <what you found>
Options:        1) <option>  2) <option>
Recommendation: <which, and why>
Impact:         <files, tests, other tasks affected>
```

Record the escalation and the answer in your Handoff.

### Tests

- Never weaken, skip or delete a test to get green. Fixing a stale fixture is
  allowed and must be called out in the Handoff.
- A failure in a file you do not own is not yours: re-run once; if it persists,
  record the output and stop.

### Committing

- Stage only the files you own: `git add <path> ...`. Never `-A`, never `.`.
- Conventional Commits, your task ID as the scope: `type(Txx): description`.
  - `type` is one of `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
  - First line **50 characters or fewer**.
  - **One blank line**, then short `- ` bullets. No prose.
- **No `Co-Authored-By` trailer**, and no other attribution line. This overrides
  any default attribution instruction your session receives.
- Never push. Never merge into `main`. Never amend. Never `--no-verify`.

```
fix(T16): keep docs/plan out of new projects

- docs/plan replaces context/tasks in both exclusions
- package.json with null scripts keeps install
```

### Done

Acceptance met, checks green, Handoff filled (including **Rollback**),
committed. Then tell the user: `Txx ready for review`, your branch name and the
commit hash.

Never edit `ROADMAP.md`, `DECISIONS.md`, this file, or another task's brief.

---

## Lead

**Review** (when the user says "check up on Txx" or a task reports ready):
read the Handoff, then verify independently - `git log main..branch`,
`git diff --stat`, `git merge-tree` against `main` and every other open branch;
run the checks; confirm no test was weakened; grep for the risks the task
targeted. Merge the wave into a throwaway worktree and run the full suite there
before asking the user to approve.

**After the user approves:** `git merge --no-ff -m "chore(Txx): merge <branch>"`,
delete the branch, remove the worktree from the main folder, push, regenerate
`STATUS.md`, and update the roadmap's status and log.

**Follow-ups:** every one goes to a later brief or to the roadmap's known-issues
list, in a lead commit on `main`. Nothing gets dropped.

**Escalations:** answered as a paste-ready reply for the task session.

---

## Lanes - waves 4 to 7

Each file belongs to one lane. Tasks in the same wave sit in different lanes.

| Lane | Files | W4 | W5 | W6 | W7 |
|---|---|---|---|---|---|
| Workflow | `docs/decisions/0004-*`, `scripts/init.py` *(message strings)*, `scripts/new_card.py` *(messages)*, `docs/playbook.md`, `.claude/skills/onboard/SKILL.md`, `.claude/README.md`, `scripts/usage.py` *(advice string)*, `scripts/_adopt.py` *(project.yaml header)* | T11 | T18 | | |
| Scan | `scripts/scan.py`, `tests/scan.py`, `project.yaml`, `RUNBOOK.md`, `.sh` file modes | T12 | T17 | | T14 *(RUNBOOK)* |
| Adoption | `scripts/_adopt.py` *(logic)*, `scripts/init.py` *(`TEMPLATE_ONLY_DIRS` block)*, `tests/adopt.py`, `README.md`, `TESTING.md` | T16 | | | T14 *(TESTING)* |
| QA | none - scratch copies outside the repo | | | T13 | |
| Release | `TESTING.md`, `RUNBOOK.md`, `STATUS.md`, `context/handoffs/` | | | | T14 |

`scripts/init.py` and `scripts/_adopt.py` are split by block: message strings and
the generated `project.yaml` header belong to Workflow; logic belongs to Adoption.

---

## Shared contracts

Four tasks implement pieces of these. They are the agreement between them -
implement exactly this, not your own reading of it.

### C1 - Citations on cards

A **claim** is a markdown bullet (`- ` or `* `) or a table data row (`| ... |`,
excluding the header row and the `|---|` separator) that sits under
`## Owns`, `## Interfaces` (including its `###` subsections) or `## Landmines`.

A claim is **cited** if it contains at least one of:

| Form | Example | Meaning |
|---|---|---|
| `` `path:N` `` or `` `path:N-M` `` | `` `src/billing/invoice.py:142` `` | code you can open |
| `` `schema:OBJECT` `` | `` `schema:BILLING.INVOICE_PKG` `` | a database object |
| `(per NAME, YYYY-MM-DD)` | `(per Rania, 2026-10-04)` | a person said so, in the interview (C4) |

or it carries the marker **`(unverified)`** - which tells the reader to expect
it to be wrong.

Not claims, so exempt: lines inside `<!-- -->` comments; lines containing a
template placeholder matching `<[a-z][a-z0-9 /_-]*>` (e.g. `<name>`); a bullet
whose whole text is `none` or `n/a` (any case); a bullet with no text at all
(`-` alone), which is a template blank.

A bullet's claim **includes its continuation lines** - the indented lines that
follow it, up to the next bullet, blank line or heading. A citation anywhere in
them counts. (Ruled at the wave-1 gate, from T04's report.)

For an area with `kind: local`, a `path:N` citation is checked against the
repository: the path must exist (relative to the repo root) and line `N` (and
`M`) must be within the file. For every other kind, and for example cards, only
the format is checked - legacy sources are often binary or schema objects, and
are not on disk to open.

### C2 - "Do not read" entries

Each entry under `## Do not read...` is a bullet holding a backticked path and a
**reason that says how it is known to be dead**. The reason is the text left
after removing the bullet marker and **every** backticked span; it must be at least 15
characters. `per NAME, DATE` is a good reason when production usage is the
evidence. The same exemptions as C1 apply: comment lines, placeholder lines, and
a bullet whose whole text is `none` or `n/a`, and a bare `-`.

For `kind: local` areas, **each** backticked path in an entry is checked: if its
name (file stem, or directory name with
any trailing `/**` removed) appears as a whole word in a code file **outside** the
listed path, that is a warning: listed as dead, but something references it.

The *Do not read* list **never applies when diagnosing a bug or a slowdown.**

### C3 - Partial cards

- An area with `survey: false` may have a **partial** card: a source field
  (`Path:` / `Repo:` / `Schema:` / `Location:`) and at least one recognised
  section. Only the sections present are validated. C1, C2 and the budget still
  apply.
- `survey: true` means **complete and maintained**: every required section and
  header field, as today.
- Card budget: **2,500** tokens.

### C4 - The interview before a card is written

Some of what a card most needs is not in the code: who owns it, what calls it
from outside the repo, whether "unused" code is dead *in production*.

- Applies when a card is **written or promoted to `survey: true`**. Not to the
  small notes added to a card during an ordinary task.
- The `surveyor` subagent cannot ask the user, so it returns a final section,
  `## Questions only a human can answer`: 3-5 questions, each tied to something
  it found, none answerable by grep.
- The main agent asks them in **one** message and waits.
- Each answer becomes a claim cited `(per NAME, YYYY-MM-DD)`.
- Each unanswered question goes under `## Open questions` on the card, and the
  claim it bears on is marked `(unverified)`.

---
