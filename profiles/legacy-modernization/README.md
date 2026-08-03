# Profile: legacy-modernization

For work on **systems you do not own**: several repositories, business logic
living in a database with no repo at all, binary sources, and a system you are
replacing incrementally while having to prove the replacement behaves the same.

```yaml
# project.yaml
profile: legacy-modernization
```

## When NOT to use this

If you control the codebase, use `general`. Seam analysis and strangler
sequencing are answers to a problem you do not have, and they cost real effort to
maintain. This profile earns its keep only when the thing you are working on is
hostile terrain: undocumented, unowned, and unsafe to change.

## What it adds

| Addition | Why |
|---|---|
| `Seams` required on every card | Modernization is boundary work. A card that does not say where the thing can be cut cannot inform what to cut first. |
| `map/<area>/seams.md` template | One entry per seam, with a Quality rating and the evidence behind it. |
| `integration/` | Forward contracts, field mappings, golden-master fixtures, the strangler plan. |
| `context/recipes/no-boundary-contract.md` | What to do when there is no observable boundary to record - the common case in Oracle Forms and batch-only systems. |
| `context/recipes/survey-system.md` | The survey recipe, extended for an external system rather than a local area. |
| `docs/stacks/oracle-forms.md` | Binary sources, database-resident logic, and the derive step that makes them greppable. |
| Extra rules in `rules.py` | Seam quality and evidence present; strangler plan exists and covers what has been surveyed; no foreign source committed into this repo. |

## The rule the whole profile rests on

**Legacy repositories stay in their own repositories, read-only and pinned to a
ref.** They are never vendored here and never restructured. This repo holds
derived understanding and forward contracts - never a copy of legacy source.

`rules.py` enforces that mechanically: it fails the build if a `.java`, `.fmb`,
`.pkb` or similar is ever committed outside `systems/` (gitignored) or
`map/<area>/derived/` (generated text, which is exactly what we want committed).

In a general project that rule would be nonsense - a `.java` file is simply your
code. That is why it lives here and not in the core.

## Declaring the estate

Each legacy system is an **area** with a `kind` saying where it lives:

```yaml
areas:
  - name: billing-legacy      # an external repo
    kind: repo
    url: git@github.com:acme/billing-legacy.git
    ref: release/2024.3       # pinned, always
    survey: true
    sparse: [src/main/java/com/acme/billing/**]
    adapters: { db: oracle, capture: rest }

  - name: core-plsql          # logic with no repo at all
    kind: database
    survey: true
    adapters: { db: oracle }
    schema_owners: [BILL01, CORE]
```

`examples/project.yaml` has all three shapes live, with the matching cards
alongside. Read those first - `examples/orders-forms-legacy/` is the hard case
and the one teams get stuck on.

## Sequence of work

0. **Secret scan** (`scripts/scan.py`) before an agent touches any repo.
1. **Survey** one system per dedicated session. Largest cost in the project, paid
   once. Order by how much of the planned work touches each system.
2. **Capture** contracts at the boundaries actually being cut - producing both a
   contract grounded in observed behaviour and golden-master fixtures.
3. **Recipes and handoffs** for the recurring task shapes.
4. **Execute**, ordered by seam quality x business value. `seams.md` is what
   makes that ordering evidence-based rather than political.

The long-form reasoning is in `docs/playbook.md` at the repo root.
