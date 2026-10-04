# Start here

You are about to work on this project with an AI agent. This page is the whole
onboarding. Five minutes.

---

## What this repo does for you

An agent has no memory between conversations. Every new session, it learns your
project from scratch by reading files - and you pay for that reading, every time.

This repo is the project's memory. You write things down **once**, in places the
agent knows to look, and it stops re-learning.

Three things follow from that:

- **Your subscription lasts longer**, because nothing is learned twice.
- **The work is easier to hand over**, because what someone needs to know is in
  a file rather than in a closed chat window.
- **Every project looks the same**, so knowing one means knowing all of them.

---

## The four commands

You do not need to understand the whole repo. You need these.
On macOS and Linux the command is often `python3` - use that wherever these
docs say `python`.

**See where your budget actually went.** Run this first. It reads your real
session history and tells you what you have been paying for.

```bash
python scripts/usage.py
```

On a project you have not used an agent in yet, it will say *no readable session
telemetry* - correct, and not a failure. Ask it about every project on your
machine instead, which is where the interesting numbers are anyway:

```bash
python scripts/usage.py --all
```

**Check the project is in good shape.** Run before you finish anything. It says
what is wrong and how to fix it.

```bash
python scripts/check.py
```

**Write down what a part of the project is**, so nobody has to work it out again.

```bash
python scripts/new_card.py <area>
```

**Save your place before you stop.** Two minutes now, twenty minutes saved next
session.

```bash
python scripts/handoff.py "what you were doing"
```

---

## The three habits that matter

Everything else in this repo supports these.

### 1. One task per conversation

A conversation carries everything said in it, forward, on every single turn. A
long session re-reads its own history constantly - by the end, one question can
cost more than the whole task should have.

When you finish a task, or when the guard warns you the session is getting heavy:
write a handoff and start a new conversation.

### 2. Write it down the first time you learn it

If you find out how something works, put it in `map/<area>/CARD.md`. If you
discover the trick to a recurring task, put it in `context/recipes/`.

The test is simple: **if you have explained something twice, it belongs in a
file.** The second explanation is the signal.

### 3. Never say "read the whole codebase"

It is the most expensive sentence you can type, and it produces the vaguest
answer. Ask for one thing at a time, and let the agent grep rather than read.

Full list of what to avoid, and what it costs: [docs/antipatterns.md](docs/antipatterns.md).

---

## What is in here

You will meet these as you need them. No need to read them now.

| File | Answers |
|---|---|
| `STATUS.md` | Where is this project right now? |
| `RUNBOOK.md` | How do I build, test and run it? |
| `map/<area>/CARD.md` | What is this part of the code, and what will bite me? |
| `context/recipes/` | How do I do a task I have done before? |
| `context/handoffs/` | What happened last session? |
| `docs/decisions/` | Why was it done this way? |
| `AGENTS.md` | The agent's map of all of the above. |

---

## If something warns you

The repo will occasionally tell you a file is large, a session is getting heavy,
or something is missing. Those are not errors. Each one names the cheaper
alternative - it is a suggestion, not a wall.

It will **stop** you in only a few cases: reading a secrets file, writing to
external code the project does not own, and hand-editing a file that a script
regenerates. In each of those the change would have been lost or harmful anyway.

If something looks like a genuine bug, check [RUNBOOK.md](RUNBOOK.md) before
reporting it - anything already known is listed there, so your time goes on the
things that are not.

---

## Next

```bash
python scripts/usage.py --all
```

Start with your own numbers. Then read
[docs/antipatterns.md](docs/antipatterns.md) - it is the shortest useful thing
here.

Too much scaffolding for what you are doing? [docs/starter-prompt.md](docs/starter-prompt.md)
is one prompt that lays out the same structure by hand, in any project, with
none of this installed. You lose the enforcement; you keep the habits.
