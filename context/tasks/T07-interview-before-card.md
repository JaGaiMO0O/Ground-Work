# T07 - Survey skills interview a human before writing a card

Status: accepted
Wave: 2
Depends on: T04
Build: build-0.1A

## Goal

Every survey skill and recipe follows contract C4: before a card is written or
promoted, the agent asks the human 3-5 questions that code cannot answer, and
records the answers as cited claims. Surveys produce cards in the C1/C2 shape.

## Why

Some of what a card most needs is not in the code. The first external
evaluation's worst failure was a *Do not read* list naming live code - and
"is this still called in production?" is exactly the question a human answers in
ten seconds and an agent cannot answer at all. The playbook already says the
undocumented paths (cron jobs, direct database access, a script someone runs by
hand) are the ones that break; none of them are visible to grep.

The `surveyor` subagent cannot talk to the user, so it must hand the questions
back to the main agent.

Also, the survey-area skill contradicts itself: its trigger (`SKILL.md:3`) says
"read more than once or twice", its body (`:22-24`) says "more than twice", and
it ends "Never survey the same area twice" (`:88`), which forbids the incremental,
cited corrections the new rules require.

## Files you may change

- `.claude/skills/survey-area/SKILL.md`
- `context/recipes/survey-area.md`
- `.claude/agents/surveyor.md`
- `profiles/legacy-modernization/scaffold/.claude/skills/survey-system/SKILL.md`
- `profiles/legacy-modernization/scaffold/context/recipes/survey-system.md`
- `context/tasks/T07-interview-before-card.md` - Report section and Status line only

## Do exactly this

Read contracts C1-C4 in `context/tasks/README.md` first.

**`.claude/agents/surveyor.md`**
1. In *What to return* (`:35-46`): every claim carries `path:N`, `path:N-M` or
   `schema:OBJECT`. Where a line cannot be pinned, say so - the main agent will
   mark it `(unverified)`.
2. Add a required final section to its output, `## Questions only a human can
   answer`: 3-5 questions, each tied to something it found, none answerable by
   grep or reading. Always consider, and ask where relevant: callers from outside
   the repository; whether each *Do not read* candidate is dead **in
   production**; who owns the area and who to ask.
3. In *Hard rules*: it is a subagent and cannot ask the user - it returns the
   questions instead.

**`.claude/skills/survey-area/SKILL.md`** and **`context/recipes/survey-area.md`**
4. Trigger (`SKILL.md:3`) and threshold (`:22-24`, and the recipe's `:3-5`):
   a full survey runs when an area has been worked on in **three or more tasks**
   and its card is missing or partial, or when someone asks for one. Below that,
   landmines go onto a partial card as they are met (contract C3). Use those
   words; make the trigger and the body agree.
5. Add a step between reading and writing, headed `## Ask before you write`:
   take the surveyor's *Questions only a human can answer*, add your own if the
   reading raised any, keep it to 3-5, ask them **in one message**, and wait.
6. In the section that fills the card: every claim cited per C1; each answer
   becomes a claim cited `(per NAME, YYYY-MM-DD)`; each unanswered question goes
   under `## Open questions` and the claim it bears on is marked `(unverified)`;
   *Do not read* entries per C2, and the reminder that the list never applies to
   bug or performance investigation.
7. Add an instruction to the skill and recipe (you do not edit `project.yaml`
   yourself): when the card is complete, set that area's `survey: true` in
   `project.yaml` - which now means "complete and maintained" (C3).
8. Replace "Never survey the same area twice" (`SKILL.md:88`, and the playbook
   echo is **not** yours - leave `docs/playbook.md` alone) with: do not re-survey
   an area from scratch; later corrections are edits, each with a citation opened
   in that session.
9. *Done when*: add every claim cited or `(unverified)`, open questions recorded,
   card within 2,500 tokens, `check.py` passes.

**Legacy `survey-system` skill and recipe**
10. Apply steps 4-9 with the legacy wording kept: cite Forms and binaries by
    their `derived/` file, database logic as `schema:OBJECT`, and `kind: repo`
    paths relative to that repository's root. Leave the Seams instructions as
    they are.

## Do not

- Remove or rename the `Do NOT load` section of either recipe - `check.py`
  requires it, and an invariant case proves it.
- Touch `AGENTS.md`, `docs/playbook.md`, the onboard skill or the trace-field
  skill - T08 and T11 own them.
- Add a fixed questionnaire. The questions come from what was found.

## Acceptance criteria

- [ ] `surveyor.md` requires `## Questions only a human can answer`.
- [ ] Both skills and both recipes have the interview step, C1/C2/C4 recording
      rules, and the three-task trigger, with trigger and body agreeing.
- [ ] "Never survey the same area twice" appears nowhere in your files.
- [ ] `python scripts/check.py` exits 0.

## Verify

```bash
python scripts/check.py      # expected: exit 0
grep -rn "Questions only a human can answer" .claude/agents/surveyor.md .claude/skills/survey-area context/recipes/survey-area.md profiles/legacy-modernization/scaffold
grep -rn "survey the same area twice" .claude context/recipes profiles   # expected: nothing
grep -n "Do NOT load" context/recipes/survey-area.md profiles/legacy-modernization/scaffold/context/recipes/survey-system.md   # expected: still present
python tests/invariants.py --only recipe     # expected: passes
```

## Commit

```
docs(T07): interview before writing a card
- Surveyor returns questions only a human can answer
- Answers cited per NAME, DATE; gaps go to Open questions
- Full survey after three tasks; edits not re-surveys
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: the single `docs(T07): interview before writing a card` commit on
branch `T07-interview-before-card` (hash given to the user; a commit cannot
hold its own hash).

**What changed**

- `.claude/agents/surveyor.md` - steps 1-3. *What to return* now requires
  `path:N`, `path:N-M` or `schema:OBJECT` on every finding, and
  `[no line: <grep>]` where a line cannot be pinned (the main agent marks those
  `(unverified)`). New required final section
  `## Questions only a human can answer`: 3-5 questions tied to findings, none
  answerable by grep; always considers outside callers, *Do not read*
  candidates dead in production, and owner/who to ask. No fixed questionnaire.
  New *Hard rules* bullet: it is a subagent, cannot ask the user, and returns
  the questions instead.
- `.claude/skills/survey-area/SKILL.md` and `context/recipes/survey-area.md` -
  steps 4-9. Trigger (`description:`) and body/`Use when:` both say: full
  survey when the area has been worked on in three or more tasks and its card
  is missing or partial, or when someone asks; below that, landmines go onto a
  partial card as they are met. New `## Ask before you write` section between
  the reading and *Filling the card*. *Filling the card* gains the recording
  rules (C1 citations, `(per NAME, YYYY-MM-DD)` answers, `## Open questions` +
  `(unverified)`, C2 *Do not read* reasons, list never applies to bug or
  slowdown work) and the instruction to set `survey: true` in `project.yaml`
  when the card is complete. *Done when* gains: every claim cited or
  `(unverified)`, open questions recorded, card within 2,500 tokens.
  "Never survey the same area twice" replaced with: do not re-survey from
  scratch; corrections are edits, each with a citation opened in that session.
- `profiles/legacy-modernization/scaffold/.claude/skills/survey-system/SKILL.md`
  and `.../context/recipes/survey-system.md` - step 10: the same, with legacy
  wording (system, scheduler jobs, other systems) and the citation rules for
  Forms/binaries by their `derived/` file, database logic as `schema:OBJECT`,
  `kind: repo` paths relative to that repository's root. Seams instructions
  untouched. The recipe had no *Filling the card* heading; one was added before
  *Done when* to hold the recording rules. `Do NOT load` kept in both recipes.

Notes on wording choices, all inside the listed files:
- The shipped skills and recipes state the contract rules inline rather than
  citing "C1"-"C4": those labels live in `context/tasks/README.md`, which never
  travels into a project (T01), so a label would dangle there.
- Step 7 adds a `project.yaml` write, so each file's "only output(s)" session
  rule now also names the area's/system's `survey:` line - otherwise the two
  instructions contradict each other.
- The edits-not-re-surveys line (step 8) is also in both recipes, since each
  skill says its recipe is canonical and wins on disagreement.

**Verify output**

```
$ python scripts/check.py
ok   all invariants hold                       -> exit 0
$ grep -rn "Questions only a human can answer" <the five files>
.claude/agents/surveyor.md:28, :59, :69
.claude/skills/survey-area/SKILL.md:63, :72
context/recipes/survey-area.md:47, :56
.../scaffold/.claude/skills/survey-system/SKILL.md:62, :72
.../scaffold/context/recipes/survey-system.md:41, :52
$ grep -rn "survey the same area twice" .claude context/recipes profiles
(nothing, exit 1)   - also nothing for "survey the same system twice"
$ grep -n "Do NOT load" <both recipes>
context/recipes/survey-area.md:30
.../scaffold/context/recipes/survey-system.md:31
$ python tests/invariants.py --only recipe
recipe lacks 'Do NOT load'   1  1  ok      1/1 passed
```

**Deviation requests**

None. One environment note: the worktree was created from `1a79a04`, eight
commits behind `main` (no `context/tasks/` at all, so T04's status could not be
checked). The branch was a strict ancestor of `main`, so it was fast-forwarded
to `main` (`d0c3f9f`) before any edit - no file of this task changed by it,
and `main` itself was not touched. T04 shows `Status: accepted` there.

**Found, not fixed**

- `docs/playbook.md:249` still says "Never survey the same area twice" (step 8
  says leave it; T08/T11 own the playbook).
- `.claude/agents/surveyor.md:21-25` (binary rule) points to
  `docs/stacks/oracle-forms.md`, which does not exist in the general template
  (`docs/stacks/` is absent at the repo root); `project.yaml:133-137` has the
  `derive:` block only as a comment. A general-profile project following that
  pointer finds nothing.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Cherry-picked into `main` as `befa2f5`. Branch `T07-interview-before-card`, built on `main`
(`d0c3f9f`) after the worker's own fast-forward.

- Live in the lead session the moment it merged: the survey-area skill's
  listing now carries the three-task trigger.
- *Found, not fixed*: `docs/playbook.md:249` -> T11; the dangling
  `docs/stacks/oracle-forms.md` pointer in `surveyor.md` -> T08 step 4.
