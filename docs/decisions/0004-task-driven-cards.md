# ADR 0004 - Cards grow from tasks, not from an up-front survey

Status: accepted
Date: 2026-10-04
Extends: [0002](0002-general-core-with-profiles.md)

## Context

The workflow this repo taught was: adopt, pick the busiest area, survey it in a
dedicated session, then work against the card. The external evaluation of
27 Sep 2026 put a number on that bet.

**One up-front card cost about 1,047k cost units to write. It saved about 27k
per task that used it. That is 39 tasks to pay back** - in one area, and only
if the card stays accurate for all of them.

The cost was mostly not reading code. It was the survey session re-reading its
own growing context on every turn. The survey paid, in full and in advance, the
very orientation tax a card exists to remove.

The card it produced also lost quality in two ways a later reader would trust:

- an **uncited claim** was repeated as fact and was wrong - in the same card
  where every cited claim was correct;
- **live code sat in the *Do not read* list**, so a reader told to skip it
  would have skipped code that runs.

And the repo contradicted itself. Its own threshold said a card is worth writing
when an area is read **more than twice**, while the adopt output, the playbook's
rollout section, the onboard skill and `new_card.py` all pushed a survey first.

## Decision

**Cards grow from the work. A full survey is earned, not assumed.**

**1. Cards grow from tasks.** A landmine learned during a task goes onto that
area's card, with the line that proves it. If the area has no card yet, it gets
a partial one: a source line and that one section, with `survey: false`
(contract C3).

**2. A full survey at the third task, or on request.** When an area has been
worked in three or more tasks, or someone asks, it is surveyed with the
survey-area skill. After that, `survey: true` means the card is complete and
maintained, not merely started.

**3. A human is asked first.** Before a card is written or promoted, a person is
asked what the code cannot say - who owns it, what calls it from outside, what
is dead in production (contract C4). Answers are cited `(per NAME, YYYY-MM-DD)`;
unanswered questions stay on the card as open.

**4. Every claim cites or says it is a guess.** A claim carries `path:N`,
`schema:OBJECT` or a `per NAME` citation, or is marked `(unverified)`
(contract C1). `check.py` enforces it.

## Consequences

**Good.** The cost of a card spreads across work that was happening anyway, in
sessions that already had the context loaded. Nobody bets 39 tasks on an area
before knowing it will see them. What only people know is captured, with a name
and a date, instead of being reconstructed from code that cannot say it.

**Costs.** An area's first sessions have no card - by design, and they pay the
orientation tax a card would have saved. Partial cards are uneven: one may hold
a single landmine and nothing else. The three-task threshold is a judgement, not
a measurement; the rollout should test it, and move it if the numbers say so.
Promotion is manual: nothing derives "worked in three tasks" from `usage.py`
yet, so it relies on someone noticing.

<!--
ADRs here are immutable. If this changes, add 0005 superseding it. Do not edit the
reasoning above - the record of why something was once right is the point.
-->
