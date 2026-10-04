# Recipe: survey an area and write its card

Use when: an area has been worked on in **three or more tasks** and its card
is missing or partial, or when someone asks for a survey. Below that threshold,
do not survey: landmines go onto a partial card as they are met - a source
field plus only the sections you have, which are all `check.py` validates.

This is the most expensive single task in the project, and it is paid **once**.
Everything after it reads the card instead of the code. Do not re-survey an
area from scratch: later corrections are edits to the card, each with a
citation opened in that session.

## Session rules

- A dedicated conversation. Nothing else happens in it.
- The only outputs are `map/<area>/CARD.md` and, once the card is complete,
  that area's `survey:` line in `project.yaml`.
- Write to the file, not into chat. Anything you write in chat is re-sent on
  every following turn; a file is read once, when needed.
- When the card passes `check.py`, stop and close the thread.

Load, in order:
1. `project.yaml` - the declared paths, stack, owner
2. `python scripts/new_card.py <area>` - scaffolds the card, prefilled
3. Shape only: `rg --files <the area's paths>`, counts by extension. Do not open
   anything yet.
4. The boundaries only: entry points, public interfaces, scheduled jobs, config,
   anything that crosses into another area.

Do NOT load: the interior of every module, test suites, generated code,
vendored dependencies, or anything already in `exclude_from_search`.

MCP servers: none. Tool definitions are billed on every turn of the whole
session, and a survey is a long session.

**Delegate the wide reading.** Ask a subagent one question at a time - "find
every inbound entry point", "what writes to this table", "which of these files
are actually imported". Take the findings back, not the files. Forty files read
by a subagent cost you a paragraph; forty files read directly cost you forty
files, on every turn thereafter.

**If the sources are binary** - `.fmb`, `.rdf`, `.mdb`, compiled artifacts -
stop. Grep silently returns nothing on a binary, which reads exactly like an
empty area. Convert first; see the `derive:` block in `project.yaml`.

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
- **Interfaces** - how the world reaches it, including the undocumented paths.
- **Landmines** - undocumented behaviour that will bite. The highest-value
  section and the easiest to skip.
- **Do not read** - dead and generated code. A direct cost lever.

**Evidence discipline is the point.** "Dead since 2019, zero hits in 12 months
of logs" is a fact the next person can act on. "Looks unused" is a guess, and
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

Done when:
- `python scripts/check.py` passes
- the `Confidence:` line honestly marks what is guesswork
- every claim is cited or marked `(unverified)`
- every unanswered question is recorded under `## Open questions`
- "Do not read" names the dead code AND says how you know it is dead
- the card is within 2,500 tokens - if it is not, you are describing the code
  rather than mapping it
