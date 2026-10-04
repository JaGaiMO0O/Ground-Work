# Project: <PROJECT_NAME>

Purpose: <ONE SENTENCE - what this project is for>
Done = <ONE SENTENCE - how we know it is finished>

Recipes and cards tell you where to look. Open the line a card cites before you state it as fact.

## Hard rules

- Secrets live in `.env`. Never read it, never echo it. Ask instead.
- Generated files carry a `GENERATED` header. Never hand-edit - re-run the script.
- Anything under `systems/` is **READ-ONLY**: external code this project does not own.
- One task per conversation. Write outputs to files, not into chat.

## Where things are

| Need | Go to |
|---|---|
| How to do task X | `context/recipes/` <- **start here** |
| Where this project stands | `STATUS.md` |
| How to build, test and run it | `RUNBOOK.md` |
| What a part of the code is, and what will bite | `map/<area>/CARD.md` |
| What exists and who owns it | `project.yaml` |
| What happened last session | `context/handoffs/` (newest) |
| Why a choice was made | `docs/decisions/` (ADRs, newest wins) |
| Domain terms that are easy to misread | `context/glossary.md` |
| Which MCP servers exist, and their cost | `interfaces/mcp/servers.yaml` |
| The habits that waste the most | `docs/antipatterns.md` |
| The reasoning behind all of this | `docs/playbook.md` (long - only if asked) |

## Start here

1. The matching `context/recipes/*.md`.
2. Then the relevant `map/<area>/CARD.md` - it says where to look, not what is true.
3. Then the code it cites - and **grep before you read**.

Never open a file just to find out whether it is relevant. Diagnosing a bug or
a slowdown is the exception: a card's *Do not read* list and this rule do not
apply - read what the evidence points at.

## Cost discipline

- A card is far cheaper than the code it describes. Use it to find the line, then open that line.
- MCP tool definitions are re-sent **on every turn**. Enable per task, not per
  project. Check `interfaces/mcp/servers.yaml` for a cheaper script first.
- Delegate wide reading to a subagent. Take the summary back, not forty files.
- A claim marked `(unverified)`, or a card marked `LOW`, is a guess. Expect it to be wrong.
- Long conversations get expensive: every turn re-reads everything before it.
  Past ~100k of context, write a handoff and start fresh.

## Cards

- Learned a landmine during a task? Add it to `map/<area>/CARD.md` with the
  line that proves it. No card yet? Create one with its `Path:` line and that
  one section.
- Edit a card only with a citation you opened in this session.
- Writing a full card? Follow the survey-area skill - it asks a human first.

## Conventions

- Mermaid for diagrams, not images.
- ADRs are immutable. Supersede rather than edit.
- Anything you have to re-explain twice belongs in this file.

## Commands

| Command | Does |
|---|---|
| `python scripts/check.py` | Validate everything. Run before you finish. |
| `python scripts/usage.py` | Where the context budget actually went |
| `python scripts/handoff.py "<topic>"` | Write the handoff, refresh `STATUS.md` |
| `python scripts/new_card.py <area>` | Start an area card |
| `python scripts/status.py` | Refresh the generated half of `STATUS.md` |
| `python scripts/scan.py` | Secret scan |

New here? `START-HERE.md`.
