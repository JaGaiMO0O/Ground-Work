# <PROJECT_NAME>

Structure for working on this project with AI agents: cheaply, reproducibly, and
in a way somebody else can pick up.

> **New here?** [START-HERE.md](START-HERE.md) - five minutes, four commands.
>
> **You are an agent?** Your entry point is [AGENTS.md](AGENTS.md).

---

## The problem this solves

An agent has no memory between conversations. Every session it re-learns the
project by reading files, and that reading is what you pay for. Most teams pay it
over and over - once per task, once per person, once per new conversation -
because nothing was ever written down anywhere the agent looks.

So it gets written down. Once, in known places, in a shape small enough to be
worth loading:

```
Without this:   learn the code, learn it again, learn it again ...
With this:      learn it once, then read one page
```

That single change does most of the work. The rest of this repo protects it.

## What is here

| Path | Holds | Answers |
|---|---|---|
| `AGENTS.md` | the router, loaded every turn, deliberately small | where is everything? |
| `STATUS.md` | state: phase, goals, blockers | where are we now? |
| `RUNBOOK.md` | build, test, run, reproduce | how do I work on this? |
| `project.yaml` | areas, owners, commands, profile | what exists? |
| `map/<area>/` | one card per area | what is this, and what will bite me? |
| `context/recipes/` | task-scoped load lists | how do I do this task? |
| `context/handoffs/` | dated session log | what happened? |
| `docs/decisions/` | ADRs, immutable | why is it like this? |
| `docs/antipatterns.md` | the five expensive habits | what am I doing wrong? |
| `interfaces/mcp/` | tool registry with per-turn costs | what is switched on? |
| `profiles/` | what a *kind* of project adds | see `profiles/README.md` |

## Tooling

| Command | Does |
|---|---|
| `python scripts/init.py` | Turn this template into your project. Once. |
| `python scripts/usage.py` | **Where your context budget actually went**, from real session history |
| `python scripts/check.py` | Validate every invariant. Run before finishing. |
| `python scripts/new_card.py <area>` | Start an area card |
| `python scripts/handoff.py "<topic>"` | Write the handoff, refresh `STATUS.md` |
| `python scripts/status.py` | Regenerate the derived half of `STATUS.md` |
| `python scripts/scan.py` | Secret scan before an agent reads anything |
| `python scripts/sync.py` | Regenerate `.rgignore`; check out external areas |

Anything that touches a live external system - a database, a service - goes
through an adapter you own: [docs/adapters.md](docs/adapters.md).

## What keeps it from rotting

A folder of templates with nothing checking them becomes a folder of stale
blanks. Three things prevent that:

- **`check.py`** enforces the rules mechanically - budgets, required sections,
  generated files, secrets, drift. Rules that live only in prose get broken
  quietly. `tests/invariants.py` breaks each rule on purpose to prove the check
  still fires.
- **Derived, not described.** `STATUS.md`'s lower half, `.rgignore`, schema
  snapshots and ER diagrams are generated. A regenerated file cannot go stale.
- **Guardrails** (`.claude/`) warn about the expensive habits as they happen, and
  block only the genuinely harmful: reading secrets, writing to external code,
  hand-editing generated files. `tests/hooks.py` proves each one.

## Measuring whether it is working

```bash
python scripts/usage.py
```

The number that matters: **what fraction of a task goes on orientation rather
than work.** Under roughly 20% means the map is doing its job. If a session opens
with the agent reading four files to work out where it is, the card for that area
is missing or inadequate - and writing it is always cheaper than paying that toll
again.

## Reproducibility

`RUNBOOK.md` is the single canonical place for how to build, test, run and
reproduce a result. `project.yaml` holds the same commands machine-readably, and
`check.py` fails if the two disagree - so the runbook cannot quietly become
fiction.

Decisions with trade-offs go in `docs/decisions/` as ADRs, which are immutable
and superseded rather than edited. The record of why something was once right is
the point.
