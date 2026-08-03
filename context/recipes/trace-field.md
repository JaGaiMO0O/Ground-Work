# Recipe: trace a field end-to-end

Use when: you need to know where a value comes from, what transforms it, and
which system is allowed to write it.

Load, in order:
1. `map/<system>/CARD.md` - check **Owns** FIRST. If another system
   owns the field, you are reading the wrong card and everything after this
   step is wasted.
2. `map/<system>/schema.sql` - grep the column name. Do not read the
   file; it is a generated snapshot and it is large.
3. `integration/mappings/<domain>.md` - it may already be mapped.
4. Only then: grep the source for the column name.

Do NOT load: full architecture documents, test suites, the interior of the
service. Integration work almost never needs the interior.

MCP servers: none. Use `scripts/query.py` for data-shape questions - a database
MCP server costs tokens on every turn whether or not you query it.

Done when: a row exists in `integration/mappings/<domain>.md` carrying source,
transform, and owning system. A mapping row without an owner is not finished.
