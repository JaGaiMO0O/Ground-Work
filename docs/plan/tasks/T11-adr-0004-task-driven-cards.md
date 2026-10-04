# T11 - ADR 0004: cards grow from tasks; stop telling people to survey up front

Wave: 4
Depends on: T05, T07, T08
Lane: Workflow
Estimate: M (~1 h)
Build: build-0.1A

## Goal

The decision to grow cards from real tasks - with a full survey only at an
area's third task, and a human asked first - is recorded as ADR 0004, and every
instruction that pushes an up-front survey is replaced.

## Why

The external evaluation (27 Sep 2026) measured one up-front card at about
1,047k cost units against about 27k saved per task: **39 tasks to pay back**. Most
of the survey's cost was the session re-reading its own context - the survey paid
the very orientation tax a card exists to remove. Recording what a task teaches,
as it is learned, spreads that cost over work that was happening anyway.

The repo currently contradicts itself. Its threshold says a card is worth writing
when an area is read more than twice (`docs/playbook.md:162-164`), yet five
places push a survey first:

- `scripts/init.py` adopt output: "Then pick the busiest area and write its card."
- `docs/playbook.md:313-314` and `:362-366`: "card the busiest area"
- `.claude/skills/onboard/SKILL.md:54`: sets `survey: true` in session one
- `scripts/new_card.py:84-86,88-91`: warns unless `survey: true`, then sends you to
  "a dedicated session, output only the card"

Rolling out with those instructions would have testers pay for the expensive
workflow the review just measured, and measure the wrong thing.

## Owns

- `docs/decisions/0004-task-driven-cards.md` - new
- `scripts/init.py` - the adopt "Next" message string only
- `scripts/new_card.py` - the post-write messages only (`:84-91`)
- `docs/playbook.md` - only the paragraphs named in step 3
- `.claude/skills/onboard/SKILL.md`
- `docs/plan/tasks/T11-adr-0004-task-driven-cards.md` - Handoff only

## Do exactly this

1. **ADR 0004**, in the format of `docs/decisions/0003-copy-per-project.md`:
   `Status: accepted`, today's date, `Extends: [0002](0002-general-core-with-profiles.md)`.
   - *Context*: the 39-task payback and how it was measured; the survey paying
     the orientation tax it removes; the two quality losses (uncited claim
     repeated; live code in a skip list); the repo contradicting its own threshold.
   - *Decision*, four points: cards grow from tasks - a landmine learned during a
     task goes onto the area's card with its citation, a partial card on
     `survey: false` if need be; a full survey when an area has been worked in
     three or more tasks, or on request, after which `survey: true` means
     complete and maintained; before a card is written or promoted, a human is
     asked what the code cannot say (contract C4); every claim cites or is marked
     `(unverified)`, and `check.py` enforces it.
   - *Consequences*: good - the cost spreads across real work, no 39-task bet,
     human knowledge captured with attribution. Costs - an area's first sessions
     have no card, by design; partial cards are uneven; the three-task threshold
     is a judgement, not a measurement, and the rollout should test it;
     promotion is manual - nothing derives it from `usage.py` yet.
   - End with the immutability comment the other ADRs carry.
2. **`scripts/init.py`**: in the adopt "Next" message, replace "Then pick the
   busiest area and write its card." with: "As you work, add each landmine you
   hit to its area's card, with the line that proves it. Run a full survey the
   third time you work in an area."
3. **`docs/playbook.md`**, only these:
   - *When a card is worth writing* (`:162-164`): cards grow from tasks; full
     survey at the third task, starting with the human questions; cite ADR 0004.
     Keep the point that over-documenting is its own waste.
   - The `LOW`-card promotion bullet (`:303-304`): a partial card in an area
     worked three or more times should be promoted - surveyed, the human asked,
     `survey: true` set.
   - Adoption (`:313-314`): replace "write the card for the busiest one" with
     working normally and letting cards grow from tasks.
   - *Either way, in order* (`:362-366`): secret scan -> declare areas -> work,
     adding landmines to cards as you meet them -> full survey of an area at its
     third task -> recipes for recurring tasks -> the handoff habit. Align the
     "Resist surveying" sentence after it with the three-task threshold.
   - `docs/playbook.md:249` "Never survey the same area twice" (found by T07's
     worker): match the survey-area skill - do not re-survey an area from
     scratch; later corrections are edits, each with a citation opened in that
     session.
   - One changelog line at the foot for ADR 0004.
4. **`scripts/new_card.py`**: when the area has `survey: false`, do **not** warn.
   Print instead that this is a partial card - fill only what you know, with
   citations, and add landmines as tasks teach them; a full survey is for the
   area's third task. Replace the "dedicated session, output only the card" line
   with: a full survey follows `context/recipes/survey-area.md` and starts by
   asking a human.
5. **Onboard skill**:
   - Step 2: the example area has `survey: false`.
   - Step 3 becomes *Start the card, together*. Keep the three questions it
     already asks the newcomer (Owns, Landmines, Do not read) - they are the C4
     interview. Record each answer as a claim cited `(per NAME, YYYY-MM-DD)`; cite
     what you read as `path:N`; anything they could not answer goes under
     `## Open questions` with its claim `(unverified)`. Say plainly that a partial
     card is the expected result of a first session.
   - Remove the advice to be honest in `Confidence:` as the main safeguard;
     citations are now the safeguard. Keep the sentence "A card that overstates
     its certainty is worse than no card, because it gets trusted."

## Do not

- Touch the playbook paragraphs T08 changed.
- Change `check.py`, the templates, or the survey-area skill.
- Change `init.py` beyond that one message string.

## Acceptance criteria

- [ ] `docs/decisions/0004-task-driven-cards.md` exists with all four parts.
- [ ] `grep -rn "busiest area" scripts docs/playbook.md .claude` finds nothing
      (the ADR itself may quote it as history).
- [ ] `new_card.py` on a `survey: false` area prints no warning.
- [ ] The onboard skill never sets `survey: true`.
- [ ] `check.py` exits 0; adopt suite still passes in full.

## Verify

```bash
grep -rn "busiest area\|write its card" scripts docs/playbook.md .claude   # expected: nothing
grep -n "survey: true" .claude/skills/onboard/SKILL.md          # expected: nothing
python scripts/check.py                                         # expected: exit 0
python tests/adopt.py                                           # expected: all pass
# new_card.py on a survey:false area - in a throwaway copy, not this repo:
#   declare an area with survey: false, run python scripts/new_card.py <area>,
#   paste the output into Handoff.
```

## Commit

```
docs(T11): grow cards from tasks (ADR 0004)

- Record ADR 0004
- Remove five "survey up front" instructions
- new_card.py and onboard expect partial cards
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit: `task/T11-adr-0004-task-driven-cards` - the single `docs(T11)` commit on it

**What changed**

- `docs/decisions/0004-task-driven-cards.md` (new): Context (39-task payback,
  ~1,047k vs ~27k; survey paying the orientation tax; uncited claim wrong;
  live code in the skip list; repo contradicting its threshold), Decision
  (four points), Consequences (good and costs), immutability comment.
- `scripts/init.py`: adopt "Next" string only - "busiest area" line replaced
  with the brief's text, wrapped over two lines. `TEMPLATE_ONLY_DIRS` untouched.
- `scripts/new_card.py:84-94`: on `survey: false`, no warning; prints the
  partial-card note instead. The "dedicated session" line is replaced with
  "A full survey follows context/recipes/survey-area.md and starts by asking a
  human."
- `docs/playbook.md`: *When a card is worth writing* (cites ADR 0004, keeps the
  over-documenting line); rule 1 "Never survey the same area twice" now matches
  the survey-area skill word for word; the `LOW` promotion bullet now says a
  partial card in an area worked 3+ times; Adoption paragraph; *Either way, in
  order* and the *Resist surveying* sentence; an **ADR 0004** changelog
  paragraph at the foot, separate from T08's 0.1A paragraph (which is unedited).
- `.claude/skills/onboard/SKILL.md`: Step 2 example `survey: false`, with one
  line on why; Step 3 is *Start the card, together* - the three questions kept
  as the C4 interview, answers cited `(per NAME, YYYY-MM-DD)`, reads cited
  `path:N`, unanswered -> `## Open questions` + `(unverified)`, partial card
  stated as the expected result. The `Confidence:` advice is gone; citations
  named as the safeguard; "A card that overstates..." sentence kept. The rule
  "Never do the survey silently" became "Never read silently" (no survey in
  this session any more).

**How it was verified**

- Baseline before any change: `check.py` exit 0, `tests/adopt.py` 31/31.
- `grep -rn "busiest area" scripts docs/playbook.md .claude` -> nothing.
- `grep -n "survey: true" .claude/skills/onboard/SKILL.md` -> nothing.
- `python scripts/check.py` -> exit 0, "all invariants hold".
- `python tests/adopt.py` -> 31/31 passed.
- `new_card.py` on a `survey: false` area, in a `git archive` copy in the
  scratchpad (area `scripts`, `survey: false`):

  ```
  ok   wrote map/scripts/CARD.md

    scripts has 'survey: false', so this is a partial card. Fill only
    what you know, with citations, and add landmines as tasks teach them.
    A full survey is for the area's third task.

    A full survey follows context/recipes/survey-area.md and starts by
    asking a human.
  ```
- `init.py --adopt` into a scratch git repo; the Next block ends with:

  ```
    As you work, add each landmine you hit to its area's card, with the
    line that proves it. Run a full survey the third time you work in an area.
  ```

**Deviations** (escalations raised, and the answers)

- None escalated. One gap between the Verify block and the acceptance
  criteria: the Verify grep also matches `write its card`, which still hits
  three files outside Owns (listed under Follow-ups; one is the survey-area
  skill, which this brief forbids changing). The acceptance criterion
  ("busiest area" finds nothing) is met. I left those files alone.
- No automated test for the `new_card.py` message: `tests/` is outside Owns,
  and the brief asks for a manual run (output above).

**Follow-ups** (found, not fixed - file and line)

- `scripts/init.py:807` - the fresh-init "Next" message still says
  `python scripts/new_card.py <area>   - then survey it`. It is outside T11's
  one string, and is a survey-first instruction.
- `scripts/_adopt.py:414-415` - generated `project.yaml` header: "set
  `survey: true` on one when you are ready to write its card." It implies one
  area should be surveyed after adoption. Adoption lane.
- `.claude/README.md:29` - survey-area row still says "dedicated session ...
  output only the card". Not wrong for a full survey, but it does not mention
  the third-task trigger or the human questions.
- `scripts/usage.py:265` - advice "Survey the areas they belong to" when files
  are re-read in 3+ sessions. This roughly matches the threshold, but it could
  point at promoting a partial card instead.
- `tests/` - nothing covers `new_card.py` output. A test that `survey: false`
  prints no `warn` line would hold this change in place.

**Rollback**

`git revert <T11 commit>` on `main`. It touches docs, two message strings and
one new ADR file. There is no data or schema, and nothing else depends on the
ADR yet. If the revert lands after T16, re-check that the `init.py` hunk
reverts cleanly next to T16's `TEMPLATE_ONLY_DIRS` change (different blocks).
---

## Lead review

<!-- Lead only. -->
