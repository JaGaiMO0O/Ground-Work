---
name: survey-system
description: Survey a legacy system and write its cartography card. Use when a system has been worked on in three or more tasks and its card is missing or partial, or when someone asks for a survey. Below that, landmines go onto a partial card as they are met. Runs the playbook's Phase 1 protocol - a dedicated, disposable session producing only CARD.md and seams.md.
---

# Survey a legacy system

This is the largest token bill in the project, and it is paid **once**. Treat
the session accordingly.

The canonical text is `context/recipes/survey-system.md`. If this skill and that
recipe ever disagree, the recipe is right and this file is the bug.

## Before you start

Check the system is worth surveying. A full survey runs when the system has been
worked on in **three or more tasks** and its card is missing or partial, or
when someone asks for one. Below that, do not survey: landmines go onto a
partial card as they are met - a source field plus only the sections you have,
which are all `check.py` validates. Say so and stop rather than producing a
card nobody will load.

Then scaffold it:

```bash
python scripts/new_card.py <system>
```

That prefills the repo, pinned ref, stack and date from `project.yaml`.

## Session discipline

- This conversation does **one** thing. Nothing else goes in it.
- The only outputs are `map/<system>/CARD.md` and `seams.md` - and, once the
  card is complete, that system's `survey:` line in `project.yaml`.
- Write to those files. Do not draft the card in chat - chat output re-enters
  context on every subsequent turn, and a card drafted in chat gets paid for
  repeatedly.
- When both files pass `check.py`, stop and close the thread.

## Doing the survey

1. Read `project.yaml` for the declared ref, sparse paths and stack.
2. Establish shape before content: `rg --files systems/<system>/`, counts by
   extension. Do not open anything yet.
3. **Delegate the wide reading to the `surveyor` subagent.** Give it one
   question at a time - "find every inbound entry point", "find the scheduler
   definitions", "what writes to the invoice table". Take its findings back,
   not the files.
4. Follow up yourself only where a finding needs its surrounding context.

**If the sources are binary** - `.fmb`, `.rdf`, `.mdb`, compiled artifacts -
stop. Grep silently returns nothing on binaries, which reads exactly like an
empty system. Run the derive step first: `profiles/legacy-modernization/docs/stacks/oracle-forms.md`.

**If the logic lives in the database** rather than a repo, that is a
`kind: database` system. Snapshot it with `python scripts/snapshot_db.py
<system>` and treat the package signatures as the contract.

Ask the `surveyor` for citations the card can use as-is - `path:N` or
`path:N-M`, or `schema:OBJECT` for database logic - and for its closing
`## Questions only a human can answer`. It does both by default.

## Ask before you write

Some of what the card most needs is not in the code: who owns the system, what
calls it from outside the repository - other systems, scheduler jobs, direct
database access, a script someone runs by hand - and whether "unused" code is
dead **in production**. Only a person can answer those, and the surveyor
cannot ask one.

1. Take the surveyor's *Questions only a human can answer*.
2. Add your own if the reading raised any.
3. Keep it to **3-5**, each tied to something found. No fixed questionnaire.
4. Ask them **in one message**, and wait for the answers before writing.

Note who answered and the date - each answer goes onto the card with both.

## Filling the card

Four sections carry most of the value:

- **Owns.** Data ownership is the most contested question in an integration and
  the most expensive to get wrong. Name any single field owned inside another
  system's entity.
- **Seams.** The input to sequencing. Be honest about the ENTANGLED ones -
  "do not start here" is as useful as a good candidate.
- **Landmines.** Behavioural quirks that cause acceptance failures. Rounding in
  a trigger, timezone assumptions, magic status values.
- **Do not read.** A direct token lever. Say *why* it is dead and how you know.

**Evidence discipline is the point.** "Dead since 2019, zero hits in 12 months
of access logs" is a fact. "Looks unused" is a guess, and guesses are labelled
as such - in the `Confidence:` line and on the claim itself. A card that
overstates its certainty is worse than no card, because it gets trusted.

How each claim is recorded - the card template's comments say the same:

- **Every claim under Owns, Interfaces and Landmines is cited:** `path:N` or
  `path:N-M`. Cite Forms and other binaries by their `derived/` file, never the
  binary. Cite database logic as `schema:OBJECT`. For a `kind: repo` system,
  paths are relative to that repository's root. A claim you cannot pin is
  marked `(unverified)`.
- **Each interview answer becomes a claim** cited `(per NAME, YYYY-MM-DD)` -
  the person who answered and the date they did.
- **Each unanswered question goes under `## Open questions`**, and the claim it
  bears on is marked `(unverified)`.
- **Do not read entries:** each is a bullet with the backticked path and a
  reason that says how it is known to be dead - at least 15 characters once the
  backticked paths are removed. `per NAME, DATE` is a good reason when
  production usage is the evidence.
- The *Do not read* list **never applies when diagnosing a bug or a
  slowdown.** Say so on the card if it is not already there.

When the card is complete - every required section filled, interview done -
set that system's `survey: true` in `project.yaml`. That now means **complete
and maintained**, and `check.py` holds the card to every required section from
then on.

Read `examples/billing-legacy/CARD.md` if the format is unfamiliar - and
`examples/orders-forms-legacy/CARD.md` if this system has no clean boundary.

## Done when

```bash
python scripts/check.py
```

passes, and:

- the `Confidence:` line honestly marks what is guesswork
- every claim is cited or marked `(unverified)`
- every unanswered question is recorded under `## Open questions`
- `seams.md` has at least one seam with evidence behind it
- "Do not read" names the dead code and says how you know it is dead
- the card is within 2,500 tokens

Then close the thread. Do not re-survey a system from scratch: later
corrections are edits to the card, each with a citation opened in that
session.
