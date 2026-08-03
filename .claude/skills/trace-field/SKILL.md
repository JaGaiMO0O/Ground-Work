---
name: trace-field
description: Trace a data field end to end - where it comes from, what transforms it, and which area owns it. Use when asked where a value originates, why a column holds what it holds, or how a field maps to another system.
---

# Trace a field end-to-end

Canonical text: `context/recipes/trace-field.md`. That recipe wins if this
disagrees with it.

## Load in this order. Do not skip step 1.

1. **`map/<system>/CARD.md` - read "Owns" FIRST.**
   If a different system owns the field, you are in the wrong card and
   everything after this step is wasted effort. Ownership is also the answer to
   half the questions that get asked as "where does this come from".

2. **`map/<system>/schema.sql` - grep the column, do not read the file.**
   It is a generated snapshot and it is large. `rg -n '<column>'` is the whole
   interaction.

3. **`integration/mappings/<domain>.md`** - it may already be mapped, in which
   case you are checking work rather than doing it.

4. **Only then**, grep the source for the column name.

## Do not load

Full architecture documents. Test suites. The interior of the service.
Integration work almost never needs the interior, and loading it is how a
1,500-token task becomes an 80,000-token one.

## MCP servers

None. For data-shape questions use:

```bash
python scripts/query.py <system> "SELECT ..."
```

It is read-only, it enforces a statement timeout, and it costs nothing until
called - unlike a database MCP server, whose tool definitions are re-sent on
every turn whether or not you query anything.

## Watch for

The card's **Landmines** section. Fields frequently mean something other than
their type suggests: integer cents rather than decimals, a nullable column
where NULL means 1, a status code whose letters do not map to the obvious
words. Rounding and defaulting often happen in a database trigger rather than
in application code, so the source will not tell you.

## Done when

A row exists in `integration/mappings/<domain>.md` carrying **source,
transform, and owning system**, plus the evidence the transform rule came from.
A mapping row without an owner is not finished - that gap is what produces
double-write bugs later.

If the field will not carry forward, record it in that file's "Unmapped,
deliberately" table with a reason. An unmapped field nobody decided about is a
data-loss bug; one with a reason next to it is a decision.
