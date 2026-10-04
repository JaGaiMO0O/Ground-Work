---
name: onboard
description: Walk a newcomer through setting this project up for agent-assisted work, producing their first area card and recipe. Use when someone is new to this repo, asks how to get started, says they do not know how to use it, or wants help setting it up on an existing codebase.
---

# Onboard someone

Your job is to get one real card and one real recipe written, in about fifteen
minutes, by **doing it with them** rather than explaining it. Do not lecture, and
do not send them off to read `docs/playbook.md`.

The person you are helping may not know what a token is, and does not need to.
Talk about time and money, not context windows.

## Rules for this session

- **Show, then explain.** Run the command, look at the output together, then say
  what it meant. Never the other way round.
- **One thing at a time.** They should be able to stop after any step and still
  be better off than before.
- **Their project, their words.** Names and descriptions in the card come from
  them. If you write it all yourself they will not trust it or maintain it.
- **Never read silently.** If you disappear for twenty tool calls they learn
  nothing. Narrate briefly.

## Step 1 - show them what it is costing them now

```bash
python scripts/usage.py
```

Read the output with them and pick **one** finding - the biggest one. Usually
either re-read files or a session that grew enormous. Say what it means in plain
terms: "these files have been re-learned eight separate times", "this session was
paying ten times over by the end".

If there is no telemetry yet, say so plainly and move on. Do not invent numbers.

This step matters because everything after it is now their problem rather than
advice from a README.

## Step 2 - declare one area

Open `project.yaml`. Add **one** area - the part of the codebase they touch most.
Not all of them; one.

```yaml
areas:
  - name: api
    kind: local
    paths:
      - src/api/**
    owner: <their name or team>
    survey: false
```

Ask which paths belong to it. They know; you would be guessing.

`survey: false` is right for a first session: the card you start next is
partial. A full survey comes later, the third time someone works in the area.

## Step 3 - start the card, together

```bash
python scripts/new_card.py api
```

Then ask them three questions. Only they can answer them - this is the
interview a card starts from:

- **Owns** - what is this area the authority on?
- **Landmines** - "what has bitten you here before?" This is the question that
  produces the most valuable line in the whole repo, and only they can answer it.
- **Do not read** - "is any of this dead?"

Write each answer as a claim cited `(per NAME, YYYY-MM-DD)`, with their name and
today's date. Open only what their answers point at, and cite what you read as
`path:N`. Anything they could not answer goes under `## Open questions`, and the
claim it bears on is marked `(unverified)`.

Say it plainly: **a partial card is the expected result of a first session.** It
grows as tasks teach the next landmine, and gets a full survey the third time
someone works in this area.

Keep it to one page. `check.py` will fail a card that grows past budget, and the
reason is worth saying out loud: a card that costs as much as the code has no
reason to exist.

The citations are the safeguard: `check.py` fails a claim that neither cites
nor says `(unverified)`. A card that overstates its certainty is worse than no
card, because it gets trusted.

## Step 4 - capture the task they do most

Ask: "what do you ask an agent to do most often?" Write that as a recipe in
`context/recipes/`, using `_TEMPLATE.md`.

The three required parts are the point:

- **Load, in order** - what to read, and in what sequence
- **Do NOT load** - naming what to skip is half the value
- **Done when** - so the task has a finish line

## Step 5 - close the loop

```bash
python scripts/check.py
python scripts/handoff.py "onboarding"
```

Show them that the handoff also refreshed `STATUS.md`, and that this is the habit:
one command at the end of a session, and the next person - or the next them - starts
from something instead of nothing.

## Finish by naming the three habits

Nothing else, and in their terms:

1. **One task per conversation.** Long threads re-read themselves and get
   expensive.
2. **Write it down the first time.** If you have explained it twice, it belongs
   in a file.
3. **Never ask an agent to "read the whole codebase".** Ask for one thing; let it
   search.

Then point at `START-HERE.md` for later and stop. They now have a card, a recipe,
a handoff and a reason to keep going - which is more than a tour would have given
them.
