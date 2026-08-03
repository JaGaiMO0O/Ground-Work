# Mapping: <domain>

Field-level legacy -> target. One row per field.

| Legacy field | Type | Target field | Type | Transform | Owner | Evidence |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Unmapped, deliberately

Fields present in the legacy system that will NOT carry forward, and why.

| Legacy field | Why not |
|---|---|
|  |  |

<!--
A row without an Owner is not finished - "who is allowed to write this" is the
question that causes double-write bugs when it goes unanswered.

Evidence means: where the transform rule came from. A traffic capture, a
landmine in the card, a business rule someone confirmed. "Looks like cents"
is not evidence.

The second table matters more than it looks. An unmapped field that nobody
decided about is a data-loss bug; an unmapped field with a reason next to it
is a decision. Same outcome, completely different conversation at UAT.
-->
