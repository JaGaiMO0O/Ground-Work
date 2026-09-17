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

There are two prompts below. The first builds one project's structure. The
second puts the *habits* into your global instructions, so they hold in every
project without building anything at all - see
[Making the habits permanent](#making-the-habits-permanent).

---

## Prompt 1 - one project

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

## Making the habits permanent

The prompt above is per-project: you paste it once, in one repo, and it builds
that repo's structure. The *habits* are not per-project. Those belong in your
global instructions file, which Claude loads in every session in every directory
you ever work in.

**Which means it is Tier 0 for your whole machine, and the budget rule applies
harder than anywhere else.** So what goes in it is much less than the prompt
above:

| Goes global | Stays per-project |
|---|---|
| How the agent should *work* - grep before reading, one task per conversation, say what you could not determine | The file layout: `AGENTS.md`, `STATUS.md`, `map/<area>/` |
| Judgement rules that hold regardless of language or repo | Anything naming this project's areas, commands or goals |

**Do not put the file layout in the global file.** It would have Claude create
`map/` and `context/handoffs/` in every throwaway directory you open - which is
the "scaffolding for a workflow I do not have yet" antipattern, applied to your
entire machine. The prompt above exists precisely so you can invoke the
structure deliberately, in the repos that earn it.

### Prompt 2 - every project

```text
I want a standing set of working rules that apply to every project rather than
just this one. They go in my global instructions file.

Before you change anything:

1. Read ~/.claude/CLAUDE.md if it exists, and show me what is already in it.
2. Copy it to ~/.claude/CLAUDE.md.bak. If that file cannot be written, stop.
3. If anything already in there contradicts the block below, stop and tell me
   which lines rather than picking a winner.

Then append the block below, under its own heading, at the end of the file. Do
not rewrite, reorder or reword anything already there - I put it there on
purpose. Show me the diff when you are done.

## Working with agents

Applies to every project, unless that project's own AGENTS.md or CLAUDE.md says
otherwise - the project always wins.

- One task per conversation. A session re-reads its own history on every turn,
  so a long one gets expensive at the end for no extra work. When a task is
  done, write down what was learned and start a fresh conversation.
- Write it down the first time. If something has been explained twice, it
  belongs in a file in the repo rather than in this conversation.
- Never read the whole codebase. Grep for what is needed. One thing at a time.
- Derive, do not describe. Anything git, the filesystem or a test run already
  knows should be generated rather than written out by hand.
- One canonical location per fact. Anything stated twice, one copy will rot.
- Ask the environment rather than assuming it. Check what is installed, what
  the paths actually are, what the tests actually assert.
- Say what you could not determine, rather than filling it in with something
  plausible.
- Where there is no undo, ask first.
- In a repository that is not mine, propose files rather than creating them.
```

### The manual

**Where it lives.** `~/.claude/CLAUDE.md`. On Windows that is
`%USERPROFILE%\.claude\CLAUDE.md`, usually `C:\Users\<you>\.claude\CLAUDE.md`.
The file may not exist yet, and may already have things in it - hence the
read-first, back-up-second steps in the prompt.

**When it takes effect.** Your *next* session, not the one you ran the prompt
in. Instructions are loaded at the start of a conversation.

**Checking it worked.**

```bash
cat ~/.claude/CLAUDE.md
```

That confirms the text is there. Whether it is *working* is a different
question, and an honest one: these are behavioural rules, so the evidence is
behavioural and takes a few sessions to see. The thing to watch for is an agent
reaching for grep where it used to read whole files, and offering a summary at
the end of a task rather than carrying on into a tenth topic.

**Undoing it.**

```bash
mv ~/.claude/CLAUDE.md.bak ~/.claude/CLAUDE.md
```

Which is why step 2 of the prompt is not optional.

**One project only, rather than all of them?** Put the block in that project's
own `CLAUDE.md` instead. Note that a repo built from the scaffold uses
`CLAUDE.md` as a one-line pointer to `AGENTS.md` and nothing else - so there,
the block belongs in `AGENTS.md`, inside the Tier 0 budget, or not at all.

## The pocket version

If even that is too long, three habits carry most of the value:

1. Write down what you learned before the session ends.
2. Keep the always-loaded file small and stable.
3. Generate anything git already knows.

<!--
Keep this file in step with docs/playbook.md. If a principle changes there and
not here, this becomes the second source of truth the playbook warns about.
-->
