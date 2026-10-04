# Recipe: survey a legacy system (cartography)

Use when: a system has been worked on in **three or more tasks** and its card
is missing or partial, or when someone asks for a survey. Below that threshold,
do not survey: landmines go onto a partial card as they are met - a source
field plus only the sections you have, which are all `check.py` validates.

This is the single largest token bill in the project. It is paid ONCE. Do not
re-survey a system from scratch: later corrections are edits to the card, each
with a citation opened in that session.

## Session rules

- A dedicated, disposable conversation. Nothing else happens in it.
- The only outputs are `map/<system>/CARD.md` and `seams.md` - and, once the
  card is complete, that system's `survey:` line in `project.yaml`.
- When those are written, close the thread.
- Write to the files, not into chat. Chat output re-enters context every turn.

Load, in order:
1. `project.yaml` - the pinned ref, sparse paths, declared stack
2. `python scripts/new_card.py <system>` - scaffolds the card, prefilled
3. Shape only: `ls` and `rg --files` over `systems/<system>/`. Grep before read.
4. Seam candidates only: entry points, schedulers, file drops, DB grants,
   anything with a network or filesystem boundary.

If the sources are binary (.fmb, .rdf, COBOL copybooks), stop and run the
derive step first - see `profiles/legacy-modernization/docs/stacks/oracle-forms.md`. Grepping a binary
returns nothing and reads as "this system is empty".

Do NOT load: the interior of the service, test suites, generated code, vendored
dependencies, or anything already listed in `exclude_from_search`.

MCP servers: none. For data-shape questions use `scripts/query.py`, which costs
nothing until it is called.

Delegate: hand wide reading to a subagent - "survey these 40 files and report
the entry points". Take the summary back, not 40 files of raw content. Ask it
for citations the card can use as-is - `path:N` or `path:N-M`, or
`schema:OBJECT` for database logic - and for its closing
`## Questions only a human can answer`. The `surveyor` agent does both by
default.

## Ask before you write

Some of what the card most needs is not in the code: who owns the system, what
calls it from outside the repository - other systems, scheduler jobs, direct
database access, a script someone runs by hand - and whether "unused" code is
dead **in production**. Only a person can answer those, and a subagent cannot
ask one.

1. Take the surveyor's *Questions only a human can answer*.
2. Add your own if the reading raised any.
3. Keep it to **3-5**, each tied to something found. No fixed questionnaire.
4. Ask them **in one message**, and wait for the answers before writing.

Note who answered and the date - each answer goes onto the card with both.

## Filling the card

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

Done when:
- `python scripts/check.py` passes for the new card
- the Confidence line honestly marks what is guesswork
- every claim is cited or marked `(unverified)`
- every unanswered question is recorded under `## Open questions`
- `seams.md` has at least one seam with evidence behind it
- "Do not read" names the dead code AND says how you know it is dead
- the card is within 2,500 tokens
