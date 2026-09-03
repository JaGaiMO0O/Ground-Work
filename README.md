# Ground Work

Structure for working on a project with AI agents: cheaply, reproducibly, and in
a way somebody else can pick up.

> **You are an agent?** Your entry point is [AGENTS.md](AGENTS.md).

---

<!-- TEMPLATE ONLY - init.py deletes from here to the END marker. These
     are instructions for obtaining the template, which stop being true
     the moment you are the project rather than a copy of it. -->

## Get it

You need **Python 3.8+** and **git**. That is the whole requirement - no install
step, no dependencies, no virtualenv.

**Starting something new?** Take a copy and make it yours:

```bash
git clone https://gitlab.optimizasolutions.com/myaghmour/ground-works.git my-project
cd my-project
rm -rf .git && git init
python scripts/init.py
```

That third line matters: without it your project's history is *this* repo's
history and your `origin` points here, so a push would land on somebody else's
repository. On PowerShell it is `Remove-Item -Recurse -Force .git; git init`.

`init.py` asks two questions - what the project is for, and how you will know it
is finished - then fills in the placeholders and deletes the parts you are not
using. **Then read [START-HERE.md](START-HERE.md).** Five minutes, four commands,
and it is the whole onboarding.

**Already have a project?** Bring the scaffold into it instead:

```bash
git clone https://gitlab.optimizasolutions.com/myaghmour/ground-works.git
cd ground-works
python scripts/init.py --adopt /path/to/your/project --dry-run
```

Drop `--dry-run` once the plan looks right. Your project has to be a git
repository with a clean tree; adoption refuses otherwise, because it writes
around fifty files and that is only a reasonable thing to do to somebody's
repository if they can take it back. Taking it back:

```bash
python scripts/init.py --undo /path/to/your/project
```

That removes exactly what adoption wrote, from a manifest it recorded at the
time, and keeps anything you have edited since.

<!-- END TEMPLATE ONLY -->

> **New here?** [START-HERE.md](START-HERE.md) - five minutes, four commands.

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
| `STATUS.md` | state: phase, goals, blockers, known issues | where are we now? |
| `STATUS.template.md` | the pristine copy of the above | what does a new project start from? |
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

## License

Proprietary. Copyright (c) 2026 Optimiza Solutions, all rights reserved -
see [LICENSE](LICENSE). Authorised testers may run it and adopt it into their
own repositories; redistribution and disclosure outside Optimiza are not
permitted.

A project you scaffold with `init.py` is yours. The licence covers this
scaffold and its tooling, not your work.
