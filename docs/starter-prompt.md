# Starter prompt

A one-page answer to *"I want the habits, not the scaffold."*

Adoption installs about 50 files. That is right for a project someone will
inherit; it is too much for a weekend project, and it needs a working copy of
this repo to hand. The prompt below needs neither. Paste it into a fresh session
in any project and it produces the same shape by hand.

What it does not give you: the enforcement. No `check.py` failing a bloated
Tier 0, no hooks blocking a `.env` read, no `usage.py` telling you what
orientation cost. Those are the reason the scaffold exists. This is the version
that relies on the agent, and on you, to hold the line instead.

---

## The prompt

```text
Set this project up so an agent joining it cold is cheap to bring up to speed,
and so anyone who inherits it finds the same shape.

First ask me two questions and wait: what is this project for (one sentence),
and how will we know it is finished (one sentence). Do not invent them.

Then create only these:

- AGENTS.md - the only file loaded every turn. Max 150 lines. Project name, my
  two sentences, and a routing table: for task X read file Y. Nothing volatile
  goes in here; it is re-sent every turn, so anything that changes daily
  destroys the prompt cache.
- CLAUDE.md - one line pointing at AGENTS.md. Never a second router.
- STATUS.md - where things stand now. Goal ladder (now / next / done means) and
  blockers, each with a name attached. State, not history.
- RUNBOOK.md - the one place saying how to build, test and run this. Real
  commands, versions pinned. If you detect them from a manifest, say so and
  mark them unverified.
- map/<area>/CARD.md - one card per part of the codebase, and only for parts
  that will be read more than twice. Each card: what it owns, its interfaces,
  its landmines, and what not to read.
- context/handoffs/ - a dated note at the end of any session that continues:
  goal, what got done, what is open, and the gotcha that cost an hour.
- docs/decisions/ - one file per non-obvious decision: context, decision,
  consequences. Immutable - supersede, never edit.

Hold to these:

- One canonical location per fact. Anything stated twice, one copy will rot.
- Derive rather than describe. Anything git, the filesystem, or a test run
  already knows should be generated, not typed. A regenerated file cannot go
  stale.
- Budget the always-loaded file and enforce it in a script - say 1500 tokens
  for AGENTS.md, 2000 per card. An unchecked budget is a suggestion.
- Anything a tool claims about my environment must be asked of my environment
  at runtime, never assumed when the tool was written.
- Refuse rather than warn where there is no undo.

Do not: document what you can derive, invent an area map before there is code
in it, card a file nobody will read twice, or create scaffolding for a workflow
I do not have yet.

When you are done, tell me what you could not determine rather than filling it
in with something plausible.
```

---

## Why three of those lines are there

They are not principles. They are scars, and they are the lines to resist
trimming when the prompt feels long.

**"asked of my environment at runtime, never assumed when the tool was
written."** Four separate defects in this repo, all the same shape: a POSIX
path this OS could not resolve (`native_path`); a hook deriving its root from a
payload field that could be absent; a test directory looked for only at the repo
root; an undo message naming `systems/` from *our* gitignore rather than the
target's. Each read as a platitude until it cost an afternoon.

**"An unchecked budget is a suggestion."** The `STATUS.md` token budget has now
caught a defect in the script that *generates* `STATUS.md` - twice, once by
catching its own author restating a handoff instead of pointing at it. It is the
only rule here that has failed the person who wrote it.

**"create scaffolding for a workflow I do not have yet."** This is what turned a
20-file project into 115 on the first real trial. Everything else on the list is
cheap. This one is not.

## The pocket version

If even that is too long, three habits carry most of the value:

1. Write down what you learned before the session ends.
2. Keep the always-loaded file small and stable.
3. Generate anything git already knows.

<!--
Keep this file in step with docs/playbook.md. If a principle changes there and
not here, this becomes the second source of truth the playbook warns about.
-->
