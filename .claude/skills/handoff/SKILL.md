---
name: handoff
description: Write the session handoff note before ending a session that will be continued. Use when wrapping up, when the user says they are stopping for the day, or when context is running short and work will resume later.
---

# Write the handoff

About 200 tokens that replace twenty minutes of re-explanation next session.

```bash
python scripts/handoff.py "<short topic>"
```

That creates `context/handoffs/YYYY-MM-DD-<topic>.md` from the template. Fill
it in from what actually happened in this session - do not ask the user to
recap; you were here.

## The six lines

| Line | What belongs there |
|---|---|
| **Goal** | What this session was trying to achieve, in one sentence |
| **Done** | What is actually finished. Be precise: "3 of 5 field types covered" beats "mostly done" |
| **Open** | What is not finished, named specifically enough to pick up cold |
| **Key files** | The two or three paths the next session will need first |
| **Gotcha** | The thing that cost you an hour |
| **Next** | The single concrete next action, ideally a command |

## Gotcha is the line that earns its keep

Everything else can be reconstructed from the diff. The gotcha cannot. It is
where the surprising behaviour goes - the DST bug, the trigger that rounds, the
endpoint that returns 200 with an error body - so it costs the next person
nothing.

If nothing surprised you, write "none". Do not invent one.

## Before you finish

If anything in this session had to be explained twice, that is not a handoff
item. It is a missing line in `AGENTS.md` - add it there instead. That feedback
loop is how Tier 0 improves, and a handoff is the wrong place for it because
handoffs are read once.

Then run:

```bash
python scripts/check.py
```

so the next session starts from a clean repo rather than inheriting a failure.
