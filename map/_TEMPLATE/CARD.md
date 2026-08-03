# Area Card: <name>
Path: <where this area lives>  |  Surveyed: <date>  |  Owner: <who>
Confidence: HIGH on ... - MED on ... - LOW on ...

Stack:
Health:

<!--
WHAT THIS IS. One page answering "what is this part of the project, and what do
I need to know before touching it" - so nobody has to read the code again to
find out. Written once, read many times.

BUDGET: one page. check.py fails a card past ~2000 tokens, because beyond that
it is no longer cheaper than reading the code, which was the entire point.

The header line is `Path:` for a local area, `Repo:` for an external repo,
`Schema:` for a database. scripts/new_card.py fills in the right one.

CONFIDENCE is how this stays cheap to maintain. You are not expected to keep
every card perfect. You ARE expected to say which parts are guesswork. A LOW
marker tells the next reader to verify before trusting - that costs nothing to
maintain and is most of the value.
-->

## Owns (authoritative - nothing else may write these)

<!--
What this area is the source of truth for: tables, entities, files, config, a
queue. If it owns one field inside something another area owns, say so - that is
exactly the case that ends with two things writing the same value.
-->

-

## Interfaces

<!--
How the rest of the world reaches this area, and what it reaches out to.
Include the undocumented paths: the cron job, the direct database access, the
script someone runs by hand. Those are the ones that break.
-->

### In

| Caller | Mechanism | Entry point | Notes |
|--------|-----------|-------------|-------|
|        |           |             |       |

### Out

-

## Landmines

<!--
Undocumented behaviour that will bite. This is what makes work fail review
months later: rounding done somewhere surprising, timezone assumptions, implicit
ordering, magic values, a field that means something different when empty.

Capture one the moment you find it. Highest-value part of the card, and the
easiest to forget.
-->

-

## Do not read unless specifically needed

<!--
A direct cost lever, and often the biggest one. Dead code, generated code and
vendored dependencies are frequently the majority of the lines.

Say WHY it is dead and how you know. "No hits in 12 months of logs" is evidence.
"Looks unused" is a guess, and belongs in the Confidence line instead.
-->

-
