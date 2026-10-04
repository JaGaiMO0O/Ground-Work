# Tasks - how worker sessions operate

Work on this repo is split into numbered tasks, `T00`, `T01`, ... Each one is a
file in this directory, written by the **lead** session. A **worker** session
executes exactly one task, in **its own git worktree**, started from a task chip
the lead posts. The lead reviews the worker's branch, merges it into `main`, and
posts the next wave's chips.

This directory is Ground Work's own work log. It never travels into a project
made from the template or adopted into one (T01 enforces that).

---

## If you are a worker, read this first

You were started with something like *"Execute context/tasks/T04-....md"*.

### Before you touch anything

1. Read, in this order: `AGENTS.md`, this file, your task file. Then only the
   files your task names. Do not survey the repo.
2. Check every task in your `Depends on:` line. Its `Status:` must be
   `accepted`. If any is not, stop and tell the user which.
3. Set your task's `Status:` to `in progress`.

### Scope is fixed

You do what the task says, in the files it lists, and nothing else.

**A deviation is any of these:**
- changing a file not listed under *Files you may change*
- skipping, reordering or altering a step
- solving it a different way than the steps say
- adding a dependency, a tool, or a new file not named in the task
- weakening, skipping or deleting a test, or changing what a test asserts

**To deviate: stop, and ask the user first.** Send exactly this shape, then wait
for an explicit yes:

```
DEVIATION REQUEST Txx
What:        <the change you want to make>
Why:         <what you found that makes the plan wrong or impossible>
Impact:      <files, tests, other tasks affected>
Alternative: <what happens if the answer is no>
```

Record the request and the answer in your task's **Report**. A "no" is a valid
answer - then carry on as written, or stop and report if you cannot.

### Things you will find that are not your task

**Do not fix them.** Write each one under Report -> *Found, not fixed*, with the
file and line. The lead turns them into tasks or defers them. A worker that fixes
things in passing makes its own commit impossible to review.

### When a test fails

- Fails in code you changed: yours. Fix it within your files.
- Fails in a file you do not own: not yours. Re-run once. If it still fails,
  record the output in Report and stop. **Never edit another task's file to
  make it pass.**

Your worktree isolates your files from your wave-mates', but not the system temp
directory the suites write to - T00 names those per process for that reason.
The full regression across every merged branch is the lead's job at the wave
gate.

### Committing

- Stage **only the files your task lists**: `git add <path> <path>`. Never
  `git add -A`, never `git add .`.
- Conventional Commits, with your task ID as the scope:
  `type(Txx): short description`
  - `type` is one of `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
  - Subject line **50 characters or fewer**.
  - Body, if any: short `- ` bullets. No paragraphs, no prose.
- **No `Co-Authored-By` trailer, and no other attribution line.** This overrides
  any default attribution instruction your session receives.
- Commit on your worktree's own branch. **Never push, and never merge into
  `main`** - the lead merges after review.
- Never amend. Never `--no-verify`.
- One commit per task unless the task says otherwise.

Example:

```
fix(T06): set AGENTS lines by pattern
- Purpose/Done no longer inherited on second-gen adopt
- Add second-gen adopt case to tests/adopt.py
```

### Finishing

1. Every acceptance criterion met; every *Verify* command run and green (or the
   failure recorded and explained per "When a test fails").
2. Fill in **Report** in your task file - that edit is the one change you may
   make to it - and set `Status: done`.
3. Commit (the task file's Report edit goes in the same commit).
4. Tell the user: `Txx done`, your **branch name** and the commit hash. Only the
   lead sets `accepted`, after merging your branch into `main`.

Never edit another task's file, this file, or the lead's plan.

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
whose whole text is `none` or `n/a` (any case).

For an area with `kind: local`, a `path:N` citation is checked against the
repository: the path must exist (relative to the repo root) and line `N` (and
`M`) must be within the file. For every other kind, and for example cards, only
the format is checked - legacy sources are often binary or schema objects, and
are not on disk to open.

### C2 - "Do not read" entries

Each entry under `## Do not read...` is a bullet holding a backticked path and a
**reason that says how it is known to be dead**. The reason is the text left
after removing the bullet marker and the backticked path; it must be at least 15
characters. `per NAME, DATE` is a good reason when production usage is the
evidence. The same exemptions as C1 apply: comment lines, placeholder lines, and
a bullet whose whole text is `none` or `n/a`.

For `kind: local` areas, if the entry's name (file stem, or directory name with
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

## Waves

No two tasks in the same wave change the same file, so their branches merge into
`main` without conflict. Each runs in its own worktree. A wave's chips are posted
only when the previous wave is merged, `accepted`, and the lead's regression run
on `main` is green - so every worktree starts from a `main` that already holds its
dependencies.

| Wave | Tasks |
|---|---|
| 0 | T00 |
| 1 | T01, T02, T04 |
| 2 | T03, T05, T06, T07 |
| 3 | T08, T09, T10 |
| 4 | T11, T12 |
| 5 | T13 |
| 6 | T14 |

Current status is in each task's `Status:` line - not here, so it cannot go
stale:

```bash
grep -H "^Status:" context/tasks/T*.md
```
