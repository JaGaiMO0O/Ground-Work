---
name: survey-area
description: Survey an area of the project and write its card, so nobody has to read the code again to learn what it does. Use when an area has been worked on in three or more tasks and its card is missing or partial, or when someone asks for a survey or to document/map part of a codebase. Below that, landmines go onto a partial card as they are met.
---

# Survey an area and write its card

The canonical text is `context/recipes/survey-area.md`. If this skill and that
recipe ever disagree, the recipe is right and this file is the bug.

## Why this is worth a whole session

Working out what a part of a codebase does costs a lot of context. Most teams pay
that cost **again** every session, because the understanding was never written
down - it evaporates when the conversation closes.

A card costs a fraction of what the code costs to read, and it is read instead of
the code from then on. This session is where that cost gets paid, once.

## Before you start

Check it is worth surveying. A full survey runs when the area has been worked
on in **three or more tasks** and its card is missing or partial, or when
someone asks for one. Below that, do not survey: landmines go onto a partial
card as they are met - a source field plus only the sections you have, which
are all `check.py` validates. Say so and stop rather than producing a card
nobody will load.

```bash
python scripts/new_card.py <area>
```

That prefills the location, stack, owner and date from `project.yaml`.

## Session discipline

- This conversation does **one** thing. Nothing else goes in it.
- The only outputs are `map/<area>/CARD.md` and, once the card is complete,
  that area's `survey:` line in `project.yaml`.
- Write to the file, not into chat. Anything written in chat is re-sent on every
  following turn; a file is read once, when needed.
- When the card passes `check.py`, stop and close the thread.

## Doing the survey

1. Read `project.yaml` for the declared paths, stack and owner.
2. Establish **shape** before content: `rg --files <paths>`, counts by extension.
   Do not open anything yet.
3. **Delegate the wide reading to a subagent.** One question at a time - "find
   every entry point", "what writes to this table", "which of these files is
   actually imported". Take the findings back, not the files.
4. Follow up yourself only where a finding needs its surrounding context.

Step 3 is the one that saves the most. Forty files read by a subagent cost you a
paragraph. Forty files read directly cost you forty files - on this turn and
every turn after it.

**If the sources are binary** - compiled artifacts, `.fmb`, `.rdf`, `.mdb` - stop.
Grep silently returns nothing on a binary, which reads exactly like an empty
area. Convert first; see the `derive:` block in `project.yaml`.

Ask every subagent to cite each finding as `path:N`, `path:N-M` or
`schema:OBJECT`, and to end with `## Questions only a human can answer` - the
`surveyor` agent does both by default.

## Ask before you write

Some of what the card most needs is not in the code: who owns the area, what
calls it from outside the repository, whether "unused" code is dead **in
production**. Only a person can answer those, and a subagent cannot ask one.

1. Take the surveyor's *Questions only a human can answer*.
2. Add your own if the reading raised any.
3. Keep it to **3-5**, each tied to something found. No fixed questionnaire.
4. Ask them **in one message**, and wait for the answers before writing.

Note who answered and the date - each answer goes onto the card with both.

## Filling the card

Four sections carry the value:

- **Owns** - what this area is authoritative for. The most contested question in
  any project and the most expensive to get wrong.
- **Interfaces** - how the world reaches it, including the undocumented paths:
  the cron job, the direct database access, the script someone runs by hand.
- **Landmines** - undocumented behaviour that will bite. Highest-value section,
  easiest to skip.
- **Do not read** - dead and generated code, and how you know it is dead.

**Evidence discipline is the point.** "Dead since 2019, zero hits in 12 months of
logs" is a fact the next person can act on. "Looks unused" is a guess, and
guesses are labelled as such - in the `Confidence:` line and on the claim
itself. A card that overstates its certainty is worse than no card, because it
gets trusted.

How each claim is recorded - the card template's comments say the same:

- **Every claim under Owns, Interfaces and Landmines is cited:** `path:N`,
  `path:N-M`, or `schema:OBJECT` for a database object. A claim you cannot pin
  is marked `(unverified)`.
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
set that area's `survey: true` in `project.yaml`. That now means **complete and
maintained**, and `check.py` holds the card to every required section from
then on.

## Done when

```bash
python scripts/check.py
```

passes, and:

- the `Confidence:` line honestly marks what is guesswork
- every claim is cited or marked `(unverified)`
- every unanswered question is recorded under `## Open questions`
- "Do not read" names the dead code AND says how you know
- the card is within 2,500 tokens - if it is not, you are describing the code
  rather than mapping it

Then close the thread. Do not re-survey an area from scratch: later corrections
are edits to the card, each with a citation opened in that session.
