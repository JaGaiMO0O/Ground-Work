# ADR 0002 - A general core, with profiles

Status: accepted
Date: 2026-08-03
Supersedes: [0001](0001-control-repo-shape.md)

## Context

ADR 0001 designed this repo as a *control repo* for legacy modernization. That
was right for the situation it addressed, and the machinery it produced works.

Two things then changed.

**The reasoning turned out not to be about legacy code.** The economic argument -
an agent has no memory, so understanding must be captured or re-bought every
session - applies to any project worked on with agents. Only the seams, the
strangler sequencing and the traffic capture were actually legacy-specific.

**The audience changed, and it matters more than the topic.** The primary users
are now people who have not done this before and are burning an LLM subscription
without knowing why. The 0001 material is expert-facing: it assumes you know what
a seam is and why MCP tool definitions are billed per turn. Such a person will not
read a 537-line playbook, so the structure has to enforce and measure the habits
rather than describe them.

## Decision

**A domain-agnostic core, plus profiles.**

1. The core knows nothing about any kind of work. A profile adds artifacts and
   validation rules for a *kind* of project. `general` is the default and adds
   nothing; `legacy-modernization` carries everything from 0001.
2. The profile mechanism is three optional things - a `scaffold/` directory, a
   `rules.py`, an `adapters/` directory - and no plugin registry, entry points or
   base class. Adding a profile is a directory.
3. **Core must never import a profile.** Dependencies point one way, or the
   general case accumulates special-casing for domains most users do not have.
4. De-jargoned, because the words were barriers for the new audience:
   `cartography/` → `map/`, `workspace.yaml` → `project.yaml`, *system card* →
   *area card*, *control repo* → just the project.
5. One model for what a project is made of: **areas**, whose `kind` says where
   they live (`local`, `repo`, `database`, `fileshare`). A legacy system is an
   area with `kind: repo`; a part of your own codebase is an area with
   `kind: local`. Same cards, same validation.
6. **Measure, do not assert.** `usage.py` reads real session transcripts, so the
   cost argument is made with the reader's own numbers.
7. **Guardrails over documentation.** Hooks warn about the expensive habits as
   they happen and block only what is harmful. Documentation nobody reads cannot
   help; a warning at the moment of the mistake can.

## Consequences

**Good.** Nothing built for 0001 is lost - it is a profile, still tested. A
newcomer running `init` never encounters the word "seam". The cost argument is now
evidence rather than advice. `--adopt` means projects that already exist can be
brought in, which is where most of the waste actually is.

**Costs.** One more indirection: a reader must know which profile is active to
know which rules apply. Two renames invalidated every path reference in the repo
at once. And `usage.py` couples to an undocumented transcript format - the only
dependency here that cannot be pinned.

**Accepted risk.** That format can change without notice. Mitigated by isolating
every schema touch point in `scripts/_transcripts.py`, degrading each metric
independently, and *never reporting zeros on a parse failure* - a budget tool that
silently reports "0 tokens" reads as good news, which is worse than reporting
nothing. Nothing else in the repo depends on it: `check.py`, the blocking hooks
and the scaffold all work with `usage.py` completely broken.

<!--
ADRs here are immutable. If this changes, add 0003 superseding it. Do not edit the
reasoning above - the record of why something was once right is the point.
-->
