# System Card: <name>
Repo: <org/repo> @ <ref>  |  Surveyed: <date>  |  Owner: <who>
Confidence: HIGH on ... - MED on ... - LOW on ...

Stack:
Health:

<!--
This REPLACES the core card template when the legacy-modernization profile is
applied. It is the core card plus a Seams section, because modernization is
boundary work and a card that does not say where the thing can be cut cannot
inform what to cut first.

BUDGET: one page. check.py fails a card past ~2500 tokens - past that it is no
longer cheaper than reading the code, which was the point.

The header line is `Repo:` for an external repository, `Schema:` for logic that
lives in a database with no repo. scripts/new_card.py fills in the right one.

CITATIONS. Every claim (bullet or table row) under Owns, Interfaces and
Landmines carries one of: `path:N` or `path:N-M`, `schema:OBJECT`,
(per NAME, YYYY-MM-DD) for something a person told you, or the marker
(unverified). A card is a map that says where to look; an uncited claim is a
guess the next reader repeats as fact.

Where the code is not a plain tree: for a `kind: repo` area, cite paths
relative to that repository's root. For Forms and other binaries, cite the
derived file under `derived/`, never the binary. For logic in the database,
cite `schema:OBJECT`. Seams carry their own Evidence field instead.

CONFIDENCE is how drift is managed cheaply. You are not expected to keep every
card perfect. You ARE expected to say which parts are guesswork. A LOW marker
tells the next reader to verify before trusting. The Confidence line is for
the whole system; doubt about one claim is marked (unverified) on that claim.
-->

## Owns (authoritative data - nothing else may write these)

<!--
The most contested question in any integration, and the most expensive to get
wrong. Name the entities this system is the source of truth for. If it owns a
single field inside an entity someone else owns, say so explicitly - that is the
case that causes silent double-writes later.
-->

- <entity this system is authoritative for> - `<path>:<line>`

## Interfaces

<!--
Who calls in, and what it calls out. Include the undocumented paths: direct SQL
from the ops team, a cron job someone wrote in 2019, a spreadsheet macro. Those
are the ones that break during a cutover, because nobody remembered them.
-->

### In

| Caller | Mechanism | Entry point | Notes |
|--------|-----------|-------------|-------|
|        |           | `<path>:<line>` |       |

### Out

<!-- Include batch jobs and file transfers, not just APIs. A nightly CSV is an
integration. -->

-

## Seams

<!--
Where this system can be cut or intercepted. This section is the input to
sequencing: execution is ordered by seam quality x business value, so be honest
about the bad ones. "Do NOT start here" is as useful as a good candidate.
One line each; the detail belongs in seams.md.
-->

S1
S2

## Landmines

<!--
Undocumented behavioural quirks. These are what make a modernization fail
acceptance months after the code looked finished: rounding done in a trigger,
timezone-naive dates, implicit ordering, magic values, a column that means
something different when NULL.
-->

- <behaviour that will bite> - `<path>:<line>`

## Do not read unless specifically needed

<!--
A direct token lever, and often the biggest one. In systems this age, dead and
generated code is frequently the majority of the lines.

Each entry is a backticked path, then why it is dead and how that is known.
Say WHY it is dead and how you know. "No hits in 12 months of access logs" is
evidence. "Looks unused" is a guess, and belongs in the Confidence line.

This list NEVER applies when diagnosing a bug or a slowdown - the cause is
often in code someone believed was dead.
-->

-

## Open questions

<!--
Optional. Interview questions nobody could answer when this card was written
or promoted to survey: true. One bullet each. The claim each one bears on stays
marked (unverified) until it is answered.
-->
