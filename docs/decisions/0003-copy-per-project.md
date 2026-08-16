# ADR 0003 - The scaffold is copied into each project, not installed once

Status: accepted
Date: 2026-08-16
Extends: [0002](0002-general-core-with-profiles.md)

## Context

The first real adoption trial turned a 20-file project into 115 files. The
scaffold was 95 of them - 4.75x the thing it described. Pruning the unused
profiles brought that to 83, and `scripts/` is 44 of those.

That raised a question the design had never actually been asked: should each
project get its own copy of the tooling at all?

**The alternative** is a shared install - `pip install groundwork`, or one clone
on the machine - with each project carrying only what is genuinely its own:
`project.yaml`, `AGENTS.md`, `STATUS.md`, `RUNBOOK.md`, `map/`, `context/`.
About fifteen files. It also removes the divergence problem: today a fix made
inside an adopted project never reaches this repo or any other project, so every
adoption is a fork.

Both complaints are real. Neither is decisive on its own.

## Decision

**Copy per project. But copy only what that project will run.**

Three reasons, in the order they mattered.

**1. The audience makes self-containment worth more than tidiness.** The users
this exists for are the ones who struggle with exactly the failure a shared
install introduces: an install step, a PATH, and the question of which Python.
A cloned project either works or it does not, with no third state.

**2. A guardrail that fails silently is worse than none.** `.claude/settings.json`
points hooks at `scripts/hooks/guard.py` inside the project. Under a shared
install that path has to resolve to wherever the package landed, on whatever
Python Claude Code happens to invoke. When it does not resolve, the hooks simply
stop firing - no error, no output, protection quietly gone. That exact bug has
already happened here once, when `guard.py` derived its root from a payload
field that could be absent. Reintroducing the same failure mode as an
architectural feature is not a trade worth making.

**3. Divergence is version pinning wearing a disguise.** A project whose
`check.py` silently upgrades under it is not reproducible, and reproducibility is
one of the four things this repo exists for. The tooling belongs to the project
the same way a lockfile does. The genuine problem inside that complaint is not
that copies exist - it is that there is no way to tell how old one is, and no way
to refresh it. That is answered by a version stamp and an update path, not by
deleting the copies.

**What adoption therefore stops copying** - things the project will never invoke:

| Dropped | Files | Why |
|---|---|---|
| `tests/**` | 3 | They test the scaffold, not your code |
| `scripts/init.py`, `scripts/_adopt.py` | 2 | Adoption has already happened |
| `scripts/*.sh`, `scripts/*.ps1` | 20 | Aliases for the `.py` files; no document that travels names them |
| unused `profiles/<other>/**` | 13 | A project uses one profile |

`scripts/adapters/**` was on that list and was taken off it. The worked `oracle`
and `postgres` references are three files, and `docs/adapters.md` - which does
travel - leans on them as the things you copy. A document describing files that
are not there costs more than three unused files that are.

Measured on the same shape of project the trial used: 95 files to 59, with
`scripts/` down from 44 to 22. `--adopt --keep-profiles` restores the profiles
for anyone who wants to switch later.

## Consequences

**Good.** Nothing to install; clone and run. Hook paths stay inside the project,
so they resolve or fail loudly. The tooling is pinned with the work, so a result
reproduced next year is reproduced against the code that produced it.

**Costs.** Copies still diverge, and this ADR does not fix that - it argues the
divergence should be *visible and deliberate* rather than eliminated. Until the
version stamp and update path exist, an adopted project has no way to say how old
its scaffold is. That is the open item this decision creates, and it is recorded
as such rather than pretended away.

**Still too heavy for a very small project.** 59 files against a 6-file project
is better than 95 and is not obviously right. If that stays uncomfortable after
more real use, the next move is a smaller adoption tier - cards, status and
`check.py` only - not a shared install. The reasoning above rules out the install;
it does not rule out copying less still.

<!--
ADRs here are immutable. If this changes, add 0004 superseding it. Do not edit the
reasoning above - the record of why something was once right is the point.
-->
