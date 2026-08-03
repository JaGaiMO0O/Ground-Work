# Recipe: survey a legacy system (cartography)

Use when: a system has no card and will be read more than twice. Below that
threshold, ad-hoc reading is cheaper - do not survey systems the integration
barely touches.

This is the single largest token bill in the project. It is paid ONCE.

## Session rules

- A dedicated, disposable conversation. Nothing else happens in it.
- The only outputs are `map/<system>/CARD.md` and `seams.md`.
- When those are written, close the thread. Never survey the same system twice.
- Write to the files, not into chat. Chat output re-enters context every turn.

Load, in order:
1. `project.yaml` - the pinned ref, sparse paths, declared stack
2. `python scripts/new_card.py <system>` - scaffolds the card, prefilled
3. Shape only: `ls` and `rg --files` over `systems/<system>/`. Grep before read.
4. Seam candidates only: entry points, schedulers, file drops, DB grants,
   anything with a network or filesystem boundary.

If the sources are binary (.fmb, .rdf, COBOL copybooks), stop and run the
derive step first - see `docs/stacks/oracle-forms.md`. Grepping a binary
returns nothing and reads as "this system is empty".

Do NOT load: the interior of the service, test suites, generated code, vendored
dependencies, or anything already listed in `exclude_from_search`.

MCP servers: none. For data-shape questions use `scripts/query.py`, which costs
nothing until it is called.

Delegate: hand wide reading to a subagent - "survey these 40 files and report
the entry points". Take the summary back, not 40 files of raw content.

Done when:
- `python scripts/check.py` passes for the new card
- the Confidence line honestly marks what is guesswork
- `seams.md` has at least one seam with evidence behind it
- "Do not read" names the dead code AND says how you know it is dead
