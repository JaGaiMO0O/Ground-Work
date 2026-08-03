# Profile: general

The default, and the right answer for almost every project: one repository, work
divided into local areas, a card per area.

```yaml
# project.yaml
profile: general
```

## What it adds

Nothing. That is the point.

The general profile is the core with no additions - no extra card sections, no
extra validation, no extra directories. If you are working in a single
repository and you want context that does not have to be rebuilt every session,
this is all you need.

## What you get from the core

| Artifact | Answers |
|---|---|
| `AGENTS.md` | where everything is (loaded every turn, kept small on purpose) |
| `map/<area>/CARD.md` | what a part of the project is, and what will bite you |
| `context/recipes/` | how to do a recurring task without rediscovering the load order |
| `context/handoffs/` | what happened, session by session |
| `STATUS.md` | where the project stands right now |
| `RUNBOOK.md` | how to build, test and run it |
| `docs/decisions/` | why a choice was made |
| `interfaces/mcp/servers.yaml` | which tools are enabled, and what they cost per turn |

## When to use something else

Switch to `legacy-modernization` when the work involves **systems you do not
own** - several repositories, business logic living in a database with no repo,
binary sources, or a system you are replacing incrementally and must prove
equivalent. That profile adds seam analysis, strangler sequencing and traffic
capture, none of which are useful on a codebase you control.

If you are unsure, stay here. Adding a profile later is a one-line change to
`project.yaml`; unpicking artifacts you never needed is not.
