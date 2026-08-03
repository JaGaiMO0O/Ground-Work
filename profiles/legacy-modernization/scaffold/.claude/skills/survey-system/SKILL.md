---
name: survey-system
description: Survey a legacy system and write its cartography card. Use when a system has no CARD.md and will be read more than twice. Runs the playbook's Phase 1 protocol - a dedicated, disposable session producing only CARD.md and seams.md.
---

# Survey a legacy system

This is the largest token bill in the project, and it is paid **once**. Treat
the session accordingly.

The canonical text is `context/recipes/survey-system.md`. If this skill and that
recipe ever disagree, the recipe is right and this file is the bug.

## Before you start

Check the system is worth surveying. A card earns its keep when the system will
be read **more than twice**. Below that, ad-hoc reading is cheaper - say so and
stop rather than producing a card nobody will load.

Then scaffold it:

```bash
python scripts/new_card.py <system>
```

That prefills the repo, pinned ref, stack and date from `project.yaml`.

## Session discipline

- This conversation does **one** thing. Nothing else goes in it.
- The only outputs are `map/<system>/CARD.md` and `seams.md`.
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
empty system. Run the derive step first: `docs/stacks/oracle-forms.md`.

**If the logic lives in the database** rather than a repo, that is a
`kind: database` system. Snapshot it with `python scripts/snapshot_db.py
<system>` and treat the package signatures as the contract.

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
of access logs" is a fact. "Looks unused" is a guess, and guesses go in the
`Confidence:` line where they are labelled as such. A card that overstates its
certainty is worse than no card, because it gets trusted.

Read `examples/billing-legacy/CARD.md` if the format is unfamiliar - and
`examples/orders-forms-legacy/CARD.md` if this system has no clean boundary.

## Done when

```bash
python scripts/check.py
```

passes, and:

- the `Confidence:` line honestly marks what is guesswork
- `seams.md` has at least one seam with evidence behind it
- "Do not read" names the dead code and says how you know it is dead

Then close the thread. Never survey the same system twice.
