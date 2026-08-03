# Recipe: survey an area and write its card

Use when: an area has no card and will be read more than twice. Below that
threshold, ad-hoc reading is cheaper - do not survey parts of the project the
work barely touches.

This is the most expensive single task in the project, and it is paid **once**.
Everything after it reads the card instead of the code.

## Session rules

- A dedicated conversation. Nothing else happens in it.
- The only output is `map/<area>/CARD.md`.
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
guesses belong in the `Confidence:` line where they are labelled as such. A card
that overstates its certainty is worse than no card, because it gets trusted.

Done when:
- `python scripts/check.py` passes
- the `Confidence:` line honestly marks what is guesswork
- "Do not read" names the dead code AND says how you know it is dead
- the card is under budget - if it is not, you are describing the code rather
  than mapping it
