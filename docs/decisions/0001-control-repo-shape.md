# ADR 0001 - The control repo shape

Status: **superseded by [0002](0002-general-core-with-profiles.md)**
Date: 2026-07-27
Supersedes: none

> Superseded, not wrong. Everything below still describes how the
> `legacy-modernization` profile works. 0002 generalizes the core and moves this
> material into that profile. Kept verbatim: the record of why something was once
> right is the point.

## Context

The estate is several repositories of 5-10 year old systems with unreliable or
absent documentation, and the work is integration and modernization rather than
greenfield building. Agents are in the loop, which makes context a metered
resource rather than a free one.

The obvious moves are both wrong:

- **Monorepo everything.** Vendoring legacy source into one repository makes
  every search slower, every clone heavier, and quietly invites edits to
  systems nobody is authorised to change.
- **Work directly in each legacy repo.** Understanding then accumulates
  nowhere. It is rediscovered per task, per person, per conversation, at
  50k-300k tokens a time.

## Decision

One new repository - this one - is the only repo anyone opens with an agent.

1. Legacy repos stay where they are, **read-only and pinned to a ref**. Never
   vendored, never restructured.
2. This repo holds **derived understanding** (cartography) and **forward
   contracts** (integration). Never a copy of legacy source.
3. `systems/` is a gitignored working checkout, fully reproducible from
   `project.yaml`. Nothing of value lives there.
4. Anything touching a live system goes through a declared **adapter**, so the
   control plane stays stack-agnostic while the estate is Java, PL/SQL, Forms,
   and whatever else turns up.
5. `scripts/check.py` enforces the above mechanically. Rules that live only in
   prose get broken quietly.

## Consequences

**Good.** Legacy repos cannot be damaged by work done here. The expensive
understanding accumulates in one place, in a form that costs ~1.5k tokens to
load rather than 80k to rediscover. Onboarding is reading this repo.

**Costs.** A sync step exists between "clone" and "work", and it can fail on a
network or credentials problem. Cards drift from the code they describe - which
is why every card carries a confidence marker and why `check.py` compares the
surveyed ref against the pinned one.

**Accepted risk.** A card can be wrong in a way nothing detects. Confidence
markers make that survivable rather than impossible: a `LOW` marker tells the
next reader to verify, which is all that is needed and costs almost nothing to
maintain.

<!--
ADRs here are immutable. If this decision changes, add 000N superseding it and
set this one to "Status: superseded by 000N". Do not edit the reasoning above -
the record of why something was once right is the point.
-->
