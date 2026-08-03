---
name: survey-area
description: Survey an area of the project and write its card, so nobody has to read the code again to learn what it does. Use when an area has no card in map/ and will be read more than once or twice, or when asked to document/map part of a codebase.
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

Check it is worth surveying. A card earns its keep when the area will be read
**more than twice**. Below that, ad-hoc reading is cheaper - say so and stop
rather than producing a card nobody will load.

```bash
python scripts/new_card.py <area>
```

That prefills the location, stack, owner and date from `project.yaml`.

## Session discipline

- This conversation does **one** thing. Nothing else goes in it.
- The only output is `map/<area>/CARD.md`.
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
guesses belong in the `Confidence:` line where they are labelled as such. A card
that overstates its certainty is worse than no card, because it gets trusted.

## Done when

```bash
python scripts/check.py
```

passes, and:

- the `Confidence:` line honestly marks what is guesswork
- "Do not read" names the dead code AND says how you know
- the card is under budget - if it is not, you are describing the code rather
  than mapping it

Then close the thread. Never survey the same area twice.
