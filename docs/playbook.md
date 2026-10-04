# Context architecture for agent-assisted work

**Why this repo is shaped the way it is.** Long-form reasoning, Tier 2 - read it
if you want to argue with a decision, not to get started. To get started:
[START-HERE.md](../START-HERE.md).

---

## 1. What this is

A structural answer to a specific situation:

- **Agents in the loop**, which makes context a metered resource rather than a
  free one.
- **Work that outlives a conversation**, so understanding has to survive the
  session that produced it.
- **More than one person**, or one person across more than a fortnight - which is
  the same problem.
- **People who have not done this before**, and who should not have to read a
  document like this to benefit from it.

It is not a methodology and it prescribes no process. It is the scaffolding that
makes ordinary decisions cheaper to make and easier to hand over.

---

## 2. The problem, in one page

An agent has no memory between conversations. Each session it rebuilds its
understanding of a project by reading files, and that reading is the cost.

Most teams pay it **repeatedly** - once per task, once per person, once per new
conversation - because the understanding was never captured anywhere durable. It
lives in a chat transcript that gets closed, or in one person's head.

The central move is to **pay it once, deliberately, and capture the result as a
compact artifact**. An area card costs a fraction of what its code costs to read.
Every later task reads the card.

```
Without:   learn it, learn it again, learn it again ...   (per task, forever)
With:      learn it once, then read one page
```

This is not a theoretical argument. Measured across 27 real sessions on one
machine:

| Observation | Value |
|---|---|
| Files read in three or more **separate** sessions | 46 |
| Worst case | 6 files, 8 separate sessions each |
| Measurable cost of those re-reads (text files only) | ~348k tokens |
| Context carried before any work happened, per session | ~45k median |
| Worst single session | 754k tokens per turn, having started at 33k |

Every one of those numbers is something the repo can now report about itself:
`python scripts/usage.py`.

Three supporting moves make up the rest:

- **Shrink the search surface**, so agents cannot wander into generated,
  vendored or dead code.
- **Prune tool definitions per task**, because they are billed on every turn.
- **Keep sessions short**, because a conversation re-reads its own history.

---

## 3. Four principles

**1. Separate the map from the territory.**
Context gets consumed rediscovering *where things are* rather than doing the
work. Maintain a small routing layer that contains no content, only pointers.
That is `AGENTS.md`, and it is deliberately the smallest file that matters.

**2. Tiers, loaded on demand.**

| Tier | What it is | Budget | Loaded |
|---|---|---|---|
| 0 | Purpose, hard rules, routing table | ≤1,500 tok | Always, every turn |
| 1 | Area cards, recipes, `STATUS.md`, `RUNBOOK.md` | ≤2,000 tok each | Per task |
| 2 | Source code, full documents, this file | Whatever it costs | Rarely, and targeted |

The budgets are enforced, not suggested: `check.py` fails a Tier 0 over 1,500
tokens or a card over 2,000.

**Volatile content must stay out of Tier 0.** Tier 0 is re-sent every turn and is
the most cache-stable content in the repo. Splicing in something that changes
several times a day invalidates the prompt cache on every edit. That is why
`STATUS.md` is Tier 1 with a routing row, rather than folded into `AGENTS.md` -
which is otherwise a tempting idea.

**3. One canonical location per fact.**
Anything described in three places will drift, and an agent will read all three.
Duplication costs twice: once in tokens, once in correctness.

**4. Derive, don't describe.**
A generated schema snapshot beats a prose description on precision *and* cost,
and it never goes stale. Same for the lower half of `STATUS.md`, for `.rgignore`,
for ER diagrams. **A regenerated file cannot rot**, which is a stronger guarantee
than any amount of discipline about keeping one updated.

---

## 4. The shape

```
AGENTS.md          Tier 0 router. Always loaded. <=150 lines.
CLAUDE.md          A pointer to AGENTS.md. Never a second router.
START-HERE.md      The human entry point. No jargon.
STATUS.md          State: phase, goals, blockers. Half generated.
RUNBOOK.md         Build, test, run, reproduce. The one canonical copy.
project.yaml       Areas, owners, commands, profile.
map/<area>/        One card per area. THE DURABLE ASSET.
context/           recipes/ (how to do X), handoffs/ (what happened), glossary.md
docs/              decisions/ (ADRs), antipatterns.md, this file
interfaces/mcp/    Tool registry, with per-turn cost recorded
scripts/           Control plane + adapters + hooks
profiles/          What a KIND of project adds. See profiles/README.md
tests/             The scaffold's own tests
```

Two rules make the shape hold:

- **`systems/` is gitignored** and read-only. It is a working checkout of code
  this project does not own, reproducible from `project.yaml`, so nothing of
  value ever lives there.
- **Core never imports a profile.** Dependencies point one way, or the general
  case slowly accumulates special-casing for domains most users do not have.

---

## 5. Area cards

One card per area, written once in a dedicated session, then read forever instead
of the code. Template: [`map/_TEMPLATE/CARD.md`](../map/_TEMPLATE/CARD.md).

Four sections carry disproportionate weight:

- **Owns.** What this area is authoritative for. The single most contested
  question in any multi-part project, and the most expensive to get wrong. A
  field owned inside somebody else's entity is exactly the case that ends with
  two things writing the same value.
- **Interfaces.** How the world reaches it, including the undocumented paths -
  the cron job, the direct database access, the script somebody runs by hand.
  Those are the ones that break.
- **Landmines.** Undocumented behaviour that will bite. This is what makes work
  fail review months later, and it is the section people skip.
- **Do not read.** A direct cost lever, often the biggest. Dead, generated and
  vendored code is frequently the majority of the lines. Each entry says how it
  is known to be dead. The list never applies to bug or performance work - in
  the first external evaluation, the second-largest cause of a slowdown sat in a
  skip list.

**Citations are the drift management.** Rather than maintaining every card
perfectly, make every claim checkable: each one cites the line that proves it, or
is marked `(unverified)`. `check.py` fails a claim with neither, and a local
citation that no longer points inside its file. The next reader opens the cited
line rather than trusting the sentence - the card says where to look, not what is
true. In the first external evaluation every cited claim was correct and the one
uncited claim was wrong. A card that overstates its certainty is worse than no
card, because it gets trusted.

**When a card is worth writing:** when the area will be read **more than twice**.
Below that, ad-hoc reading is genuinely cheaper. Over-documenting is its own
waste, and the threshold is the defence against it.

---

## 6. Shrinking the search surface

Declared in `project.yaml`, mirrored into `.rgignore` by `sync.py`, so grep never
returns what nobody should read:

```yaml
areas:
  - name: web
    kind: local
    paths: [src/web/**]
    exclude_from_search:
      - "**/__snapshots__/**"
      - "**/*.generated.ts"
```

Credential-bearing patterns are excluded globally, which protects secrets and
removes noisy config from every result at the same time.

Two habits matter as much as the configuration:

- **Grep before read.** Never open a file just to find out whether it is
  relevant. Diagnosing a bug or a slowdown is the exception: a card's *Do not
  read* list and this rule do not apply - read what the evidence points at.
- **Read the boundary, not the interior.** Most tasks never need the inside of a
  module.

**Binary sources defeat this silently.** Grep on a binary returns nothing, and
nothing is indistinguishable from an empty area - so the agent reports that there
is no logic there. The `derive:` block converts such sources to text once, into
`map/<area>/derived/`, and that is what gets searched.

---

## 7. State, history, and reasons

Three artifacts, three questions, no overlap:

| Artifact | Question | Shape |
|---|---|---|
| `STATUS.md` | Where are we now? | overwritten; lower half generated |
| `context/handoffs/` | What happened? | append-only, dated |
| `docs/decisions/` | Why is it like this? | immutable, superseded not edited |

A handoff is ~200 tokens that replace twenty minutes of re-explanation. Writing
one is bound to the end of a session, and it refreshes `STATUS.md` in the same
step - because asking someone to adopt a second habit will not work, while adding
a line to a habit they already have will.

**Recipes** prevent rediscovery of the same load order every time a familiar task
recurs. Write them for the three to five most frequent task shapes, not for
everything. Each names what to load, **what not to load**, which MCP servers are
needed, and when it is done. Naming what to skip is half the value.

---

## 8. Token economics

Orders of magnitude, for budgeting rather than precision:

| Action | Approximate cost |
|---|---|
| Reading an area to understand it | large, **once** |
| Loading its card instead | ~1-2k |
| MCP server with ~20 tools | 1-3k **per turn, every turn** |
| Targeted grep, 5 hits with context | ~1k |
| Handoff note | ~200 |
| A 500k-token session, per turn | 500k, again and again |

**The MCP point deserves emphasis.** Tool definitions are re-sent on every turn
of every conversation. A database server and a ticket tracker sitting idle in the
tool list are a recurring tax paid whether or not they are used, and it routinely
exceeds the cost of the actual work. Enable per task, not per project. Record the
cost in `interfaces/mcp/servers.yaml` so it is a decision rather than a default,
and prefer a script where one will do - a script costs nothing until it runs.

**The long-session point deserves equal emphasis**, and is more often missed. A
conversation carries its whole history forward on every turn. The measured worst
case above was paying 22x its starting cost by the end. One task per
conversation; handoff and restart.

Six operational rules:

1. Survey an area in a **dedicated, disposable session**. The only output is the
   card. Then close the thread. Never survey the same area twice.
2. **One task per conversation.**
3. **Write outputs to files, not chat.** Chat output re-enters context on every
   subsequent turn; a file does not.
4. **Delegate exploration.** "Survey these 40 files and report back" returns a
   summary rather than 40 files of content.
5. **Grep before read**, always.
6. **Fix Tier 0 from evidence.** Anything you re-explain twice belongs in
   `AGENTS.md`. This feedback loop is the mechanism by which the whole system
   improves.

---

## 9. Why any of this survives

A folder of templates with nothing checking them becomes a folder of stale
blanks. Rules that live only in prose get broken quietly. Three mechanisms:

**Validation.** `check.py` enforces the budgets, the required card sections, the
pinned refs, the secret hygiene, the runbook-to-config agreement, and drift
between a card and what it describes. `tests/invariants.py` breaks each rule on
purpose and asserts the check still fires - 35 cases, including positive controls
that prove rules do *not* over-fire.

**Derivation.** Everything that can be generated is generated. A regenerated file
cannot go stale, so the rot problem is removed rather than policed.

**Guardrails.** `.claude/` warns about the expensive habits as they happen and
blocks only the genuinely harmful: reading secrets, writing to code the project
does not own, hand-editing a generated file. Every warning names the cheaper
alternative, because "that was expensive" without an alternative is just nagging.
`tests/hooks.py` proves each decision.

The last one matters most for people new to this. Documentation they have not
read cannot help them; a warning at the moment of the mistake can.

---

## 10. Measuring whether it is working

One metric carries most of the signal:

> **What fraction of a task's tokens go to *orientation* versus *work*?**

Under roughly 20% means the cards are doing their job. If a session opens with an
agent reading four files to work out where it is, the card for that area is
inadequate - and improving the card is always cheaper than paying that toll
again.

`python scripts/usage.py` measures this from real session history, along with
cache efficiency, starting context, session growth, and the specific files being
re-read. Secondary signals:

- **Anything re-explained twice** is a missing line in `AGENTS.md`.
- **Any card marked `LOW` that keeps being consulted** should be promoted to a
  proper survey.

---

## 11. Rollout

**Adopting an existing project.** `python scripts/init.py --adopt <dir>` detects
the stack and real commands, proposes areas from directory contents and git
churn, and never overwrites anything - its versions of existing files land as
`.proposed`. Then: run the secret scan, fix the proposed areas, and write the
card for the busiest one.

It refuses on a project that is not under version control, and on one with a
dirty tree. Both refusals protect the same thing: adoption writes dozens of
files into somebody else's repository, and that is only defensible if it can be
taken back. Where there is no version control to fall back on, `git init` first.

**Backing out: `python scripts/init.py --undo <dir>`.** Adoption records every
path it wrote, with a hash, in `.adopt-manifest.json`. The undo reads that file
and removes exactly those paths - keeping anything you have edited since, saying
which, and restoring `.gitignore` to the bytes it had rather than the bytes git
thinks it should have. Delete the manifest and adoption is permanent; the undo
refuses rather than guess which files were ours.

**It reads a manifest because `git clean` was wrong in both directions.** The
first version of this said `git clean -nd` lists what adoption added and `-fd`
removes it. Running it proved otherwise: `git clean` touches untracked,
*unignored* files only, so eight files survived it in a project that gitignores
`.claude/` - and it deleted three empty directories that predated adoption,
which `git status --porcelain` cannot see and so the "clean tree" precondition
could not protect. Reaching for `-fdx` would have covered the first and made the
second worse, taking the venv and the `.env` with it.

The general lesson is not about git. **Anything adoption claims about a target
must be derived from that target at runtime**, and the same mistake has now
appeared four times here: a POSIX path this OS could not resolve, a hook reading
a root from a payload field that could be absent, a test directory looked for
only at the repo root, and an undo naming exclusions from *our* gitignore rather
than the target's. An undo path is a claim, and claims about destructive
commands get run before they get printed.

**Adoption carries templates, never content.** Once this repo began describing
itself, the copy step started handing other projects Ground Work's own goal
ladder, handoffs and ADRs - into `STATUS.md` and `context/handoffs/`, the two
places `AGENTS.md` routes to first. Everything self-describing now travels as
its `_TEMPLATE`, and `STATUS.md` is rendered from `STATUS.template.md`. A map
that describes the wrong territory, in the always-loaded tier, is the worst
failure this design has.

**Starting fresh.** `python scripts/init.py`, then declare areas as they emerge.
Do not invent an area map before there is code in it.

**Neither.** [starter-prompt.md](starter-prompt.md) is a single prompt that
produces the same structure by hand in any project, with nothing installed. It
is the right size for work nobody will inherit - and the honest trade is that
every rule below becomes something you hold to rather than something a script
holds you to.

**Either way, in order:** secret scan → declare areas → card the busiest area →
recipes for recurring tasks → the handoff habit.

**Resist surveying areas the work barely touches.** A card is worth writing when
an area will be read more than twice. Below that threshold, ad-hoc reading is
cheaper, and a card nobody loads is pure cost.

---

## 12. Templates

There are no template appendices in this document, deliberately. Every template
is a real file, which is the only copy:

| Template | File |
|---|---|
| Tier 0 router | [`AGENTS.md`](../AGENTS.md) |
| Area card | [`map/_TEMPLATE/CARD.md`](../map/_TEMPLATE/CARD.md) |
| Recipe | [`context/recipes/_TEMPLATE.md`](../context/recipes/_TEMPLATE.md) |
| Handoff | [`context/handoffs/_TEMPLATE.md`](../context/handoffs/_TEMPLATE.md) |
| Status | [`STATUS.md`](../STATUS.md) |
| Runbook | [`RUNBOOK.md`](../RUNBOOK.md) |
| Adapter contract | [`docs/adapters.md`](adapters.md) |
| Scripts | [`scripts/`](../scripts/) |

A document that restates its own templates has two copies of each, and one of
them is always wrong. Principle 3 applies to this file too.

---

## Changelog

This text began as a playbook for one situation - integrating and modernizing
multi-repo legacy systems - and was generalized in place, because the reasoning
turned out to be about agent-assisted work rather than about legacy code.

**Generalized.** The economic argument, the tiers, the card format, the token and
MCP discipline, the orientation metric and the rollout order apply to any project
and now say so. "System card" became **area card**; "the control repo" became
just the project; `cartography/` became `map/` and `workspace.yaml` became
`project.yaml`, because both were barrier words for the people this is now for.

**Moved to `profiles/legacy-modernization/`.** Seam analysis, strangler
sequencing, traffic capture, the no-observable-boundary fallback, and multi-repo
pinned checkouts. All still shipped, all still tested - see that profile's
[playbook-legacy.md](../profiles/legacy-modernization/docs/playbook-legacy.md).
None of it is useful on a codebase you control, and putting it in front of a
newcomer cost more than it gave.

**Added, with no counterpart in the original.**

- **Measurement.** `usage.py` reads real session history, so §2 and §10 report
  facts instead of estimates. Every number in §2 came from it.
- **Guardrails.** The original assumed a reader who would follow its advice. The
  audience now includes people who will never read it, so the expensive habits
  are warned about as they happen (§9).
- **`STATUS.md` and `RUNBOOK.md`.** State and reproducibility had no home.
- **Validation and tests.** `check.py` plus 56 test cases across
  `tests/invariants.py` and `tests/hooks.py`.
- **The long-session cost** (§8). The original discussed per-task cost but not
  the cost of a conversation re-reading itself, which the measurements showed to
  be the larger effect in practice.
- **`docs/antipatterns.md`.** The five habits, each with its measured cost, its
  fix, and the command that detects it.

**Corrected.** The original's directory tree omitted three paths it routed to
elsewhere; its script list disagreed with its own inline comment; and its
appendices duplicated templates that are now real files (§12).

**0.1A.** Cards are a map, not the truth: §5 makes citations the drift
management and says the *Do not read* list never applies to bug or performance
work; §6 lifts grep-before-read for diagnosis, in the same words as `AGENTS.md`.
