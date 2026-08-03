# The five expensive habits

Each one is easy to fall into, costs real money, and has a cheap fix. For each:
what it is, what it costs, what to do instead, and **how to tell whether you are
doing it** - because the point is not to take this on faith.

The detection column all comes from one command:

```bash
python scripts/usage.py
```

It reads your actual session history. Nothing here is hypothetical.

---

## 1. One long conversation for everything

**The habit.** Opening a session in the morning and still being in it at
5pm - planning, coding, debugging and reviewing in one thread.

**What it costs.** A conversation carries its entire history forward on every
turn. That is not a metaphor: the whole thing is re-read each time you press
enter. A session that starts at 45k tokens per turn and grows to 500k is paying
ten times as much for the same answer by the end.

Real measurement from one machine: sessions reaching **754k tokens per turn**,
having started around 33k. A **22x** multiplier on every remaining question.

**Instead.** One task per conversation. When the task is done, or when the guard
warns you, save your place and start fresh:

```bash
python scripts/handoff.py "what you were doing"
```

The handoff costs about 200 tokens and replaces the twenty minutes of
re-explanation that a new session would otherwise need.

**How to tell.** `usage.py` reports **LONG SESSIONS**, listing any session whose
context grew more than 3x, worst first.

---

## 2. "Read the whole codebase and tell me what it does"

**The habit.** Opening a session by asking for a tour.

**What it costs.** The most expensive sentence available, and it buys the
vaguest possible answer. The agent reads dozens of files, most irrelevant, and
every one of them stays in the context for the rest of the session - so you keep
paying for the irrelevant ones on every subsequent turn.

**Instead.** Ask one question at a time, and let the agent search rather than
read. `rg` finds the three relevant files in one call. Then read those three.

If you genuinely need an overview, that is what a card is for - write it once:

```bash
python scripts/new_card.py <area>
```

**How to tell.** `usage.py` reports **ORIENTATION SHARE**: the fraction of tool
calls spent working out where things are rather than changing anything. Under
about 20% is healthy. Well above that means the map is missing and the agent is
rediscovering the project instead of working on it.

---

## 3. Re-reading the same files every session

**The habit.** Not a decision anybody makes - it just happens. Each new session
re-reads the same handful of core files, because nothing wrote down what they do.

**What it costs.** Everything, quietly, forever. This is the single largest
avoidable cost in agent-assisted work.

Real measurement from one machine: **46 files read across three or more separate
sessions**, six of them in **eight separate sessions each**. The text files alone
accounted for roughly **348k tokens** that one card would have replaced.

**Instead.** The first time you work out what a file or an area does, write it
into `map/<area>/CARD.md`. Every later session reads the card.

The rule of thumb: **a card is worth writing when something will be read more
than twice.** Below that, reading it ad hoc is genuinely cheaper - do not
over-document.

**How to tell.** `usage.py` reports **RE-READS**, listing exactly which files you
have re-learned and how many separate sessions each cost you.

---

## 4. Leaving every tool enabled all the time

**The habit.** Connecting MCP servers - a database, a ticket tracker, a docs
site - and leaving them on permanently.

**What it costs.** Tool definitions are re-sent to the model on **every turn of
every conversation**, whether or not you use them. A 22-tool server is a standing
tax on every question you ask, including the ones that have nothing to do with it.

Real measurement from one machine: sessions starting at **45k tokens before any
work happened at all**. That is the floor: instructions plus tool definitions,
paid on every turn.

**Instead.** Enable per task, not per project. Record what each server costs in
`interfaces/mcp/servers.yaml`, so it is a decision rather than a default - and
prefer a script where one will do, because a script costs nothing until it runs.

**How to tell.** `usage.py` reports **STARTING CONTEXT**: the median context each
session carries before you ask for anything.

---

## 5. Never writing anything down

**The habit.** The work happens in the conversation, the conversation closes, and
the understanding goes with it.

**What it costs.** Everything above, compounded. It is also what makes work
impossible to hand over: the next person - or the next you, in a fortnight - starts
from nothing, and cannot tell what was decided deliberately from what was an
accident.

**Instead.** Four files, each answering one question:

| Write | When | Answers |
|---|---|---|
| `map/<area>/CARD.md` | you work out what something is | what is this? |
| `context/recipes/<task>.md` | you do a task a second time | how do I do this? |
| `context/handoffs/<date>-<topic>.md` | you stop for the day | what was I doing? |
| `docs/decisions/000N-*.md` | you make a choice with trade-offs | why is it like this? |

**How to tell.** `python scripts/check.py`. It knows what should exist and does
not, and it tells you the command that creates it.

---

## The one rule underneath all five

**If you have explained something twice, it belongs in a file.**

The second explanation is the signal. Not the third, not "when I have time" -
the second. That single habit removes most of the cost described on this page,
and it is the only one worth being strict about.
