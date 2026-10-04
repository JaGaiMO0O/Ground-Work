# T08 - AGENTS.md, playbook and trace-field: a card is a map, not the truth

Status: done
Wave: 3
Depends on: T05, T07
Build: build-0.1A

## Goal

The always-loaded router tells agents to use a card to find the line and then
open the line, lifts the skip list and the no-peeking rule for diagnosis, and
says how cards grow during ordinary work.

## Why

Both quality losses in the external evaluation came from this file. An agent
repeated a wrong, uncited claim from a card instead of reading the code; another
skipped live code because the card's *Do not read* list named it. The router
told it to do both:

- `AGENTS.md:6` "Read the recipe for the task, then the area card. Only then the code."
- `AGENTS.md:33-35` card before code; `:37` "Never open a file to find out
  whether it is relevant."
- `AGENTS.md:41` "A card costs a fraction of what reading the code costs. Read the card."
- `AGENTS.md:45` the **only** verification rule, and it covers `LOW` only.

T05 now enforces citations, so the router can point at them.

## Files you may change

- `AGENTS.md`
- `docs/playbook.md` - only the paragraphs named in step 2
- `.claude/agents/surveyor.md` - the binary-sources pointer only, step 4
- `.claude/skills/trace-field/SKILL.md`
- `context/recipes/trace-field.md`
- `context/tasks/T08-card-is-a-map.md` - Report section and Status line only

## Do exactly this

1. **`AGENTS.md`** - make exactly these changes:
   - `:6` becomes:
     `Recipes and cards tell you where to look. Open the line a card cites before you state it as fact.`
   - `:33-37` (the numbered list and the line after it) become:
     ```
     1. The matching `context/recipes/*.md`.
     2. Then the relevant `map/<area>/CARD.md` - it says where to look, not what is true.
     3. Then the code it cites - and **grep before you read**.

     Never open a file just to find out whether it is relevant. Diagnosing a bug or
     a slowdown is the exception: a card's *Do not read* list and this rule do not
     apply - read what the evidence points at.
     ```
   - `:41` becomes:
     `- A card is far cheaper than the code it describes. Use it to find the line, then open that line.`
   - `:45` becomes:
     `- A claim marked \`(unverified)\`, or a card marked \`LOW\`, is a guess. Expect it to be wrong.`
   - Add a section `## Cards`, directly before `## Conventions`, holding exactly:
     ```
     - Learned a landmine during a task? Add it to `map/<area>/CARD.md` with the
       line that proves it. No card yet? Create one with its `Path:` line and that
       one section.
     - Edit a card only with a citation you opened in this session.
     - Writing a full card? Follow the survey-area skill - it asks a human first.
     ```
2. **`docs/playbook.md`** - only these:
   - The *Confidence markers are the drift management* paragraph and the
     *Evidence discipline* paragraph that follows it (around `:151-160`): rewrite
     as one section saying citations are now the drift management - each claim
     cites the line or is marked `(unverified)`; `check.py` fails an uncited claim
     and a stale local citation; the next reader opens the line rather than
     trusting the sentence. Keep the sentence "A card that overstates its
     certainty is worse than no card, because it gets trusted." Add one sentence
     of evidence: in the first external evaluation every cited claim was correct
     and the one uncited claim was wrong.
   - The **Do not read** bullet in §5 (around `:148-149`): add that each entry
     says how it is known dead, and that the list never applies to bug or
     performance work - in that evaluation the second-largest cause of a slowdown
     sat in a skip list.
   - The **Grep before read** bullet (around `:188`): add the diagnosis exception
     in the same words as AGENTS.md.
   - Add one line to the changelog at the foot of the file for 0.1A naming these
     changes.
3. **trace-field skill and recipe**: after the step that reads the card's
   **Owns** first, add: open the line the Owns claim cites before relying on it;
   an `(unverified)` ownership claim is a lead to check, not an answer.

4. **`.claude/agents/surveyor.md`**, binary-sources rule: it points to
   `docs/stacks/oracle-forms.md`, which does not exist in a general-profile
   project (found by T07's worker). Point instead to the `derive:` reference
   block at the foot of `project.yaml`, and - in a legacy-modernization project -
   to `profiles/legacy-modernization/docs/stacks/oracle-forms.md`. Change nothing
   else in that file.

## Do not

- Touch the `## Commands` table in AGENTS.md - an invariant case patches a line
  in it by exact text.
- Touch the playbook's *When a card is worth writing* paragraph (`:162-164`), the
  `LOW` promotion bullet (`:303-304`), or the *card the busiest area* lines
  (`:313-314`, `:362-366`) - T11 owns those.
- Push AGENTS.md past the 1,500-token Tier 0 budget, or past 150 lines.

## Acceptance criteria

- [ ] AGENTS.md matches step 1 exactly; `check.py` reports Tier 0 within budget.
- [ ] The phrase "Only then the code" no longer appears in AGENTS.md.
- [ ] The playbook carries the three edits and a changelog line, and nothing else
      changed in it.
- [ ] Invariants still pass in full.

## Verify

```bash
python scripts/check.py                    # expected: exit 0; Tier 0 under 1500
grep -n "Only then the code" AGENTS.md     # expected: nothing
grep -n "## Cards" AGENTS.md               # expected: one line
python tests/invariants.py --only "Tier 0" # expected: passes
python tests/invariants.py                 # expected: all pass
git diff --stat docs/playbook.md           # sanity: a small diff
```

## Commit

```
docs(T08): treat cards as a map, not the truth
- AGENTS.md: open the cited line before stating it
- Skip list and no-peek rule lifted for diagnosis
- Cards grow from tasks; edit only with a citation
- Playbook and trace-field match
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: see `git log -1` on branch `T08-card-is-a-map` (a commit cannot name
its own hash)

**What changed**

- `AGENTS.md`: step 1 applied verbatim - `:6` line, Start-here list plus the
  diagnosis exception, the two Cost-discipline bullets, new `## Cards` section
  before `## Conventions`. `## Commands` untouched. 76 lines, Tier 0 ~852 tokens.
- `docs/playbook.md`: §5 *Do not read* bullet (how known dead; never for bug or
  performance work; evaluation evidence); the two paragraphs at `:151-160`
  merged into one "Citations are the drift management" paragraph, keeping the
  "worse than no card" sentence and adding the evaluation sentence; §6 *Grep
  before read* bullet carries the diagnosis exception in AGENTS.md's words; a
  `**0.1A.**` entry appended at the foot of the Changelog. T11's paragraphs
  untouched.
- trace-field skill and recipe: new step 2 after "Owns FIRST" (open the cited
  line; `(unverified)` ownership is a lead, not an answer); later steps
  renumbered 3-5.
- `.claude/agents/surveyor.md`: binary-sources bullet now points to the
  `derive:` block in `project.yaml` and, for legacy-modernization, to
  `profiles/legacy-modernization/docs/stacks/oracle-forms.md`; paragraph
  rewrapped. Nothing else changed.

**Verify output**

- `python scripts/check.py` - exit 0, "Tier 0 ~852 tokens of 1500 budget",
  "ok all invariants hold".
- `grep -n "Only then the code" AGENTS.md` - nothing (exit 1).
- `grep -n "## Cards" AGENTS.md` - `51:## Cards`.
- `python tests/invariants.py --only "Tier 0"` - 3/3 passed.
- `python tests/invariants.py` - 49/49 passed (run again after the last edit).
- `git diff --stat docs/playbook.md` - 20 insertions, 13 deletions.

**Deviation requests**

None.

**Found, not fixed**

- `.claude/agents/surveyor.md:20` - its own *Grep before read* bullet has no
  diagnosis exception, unlike AGENTS.md and the playbook now. Step 4 said
  change nothing else in that file.
- Profile files still point at a project-relative `docs/stacks/oracle-forms.md`:
  `profiles/legacy-modernization/scaffold/.claude/skills/survey-system/SKILL.md:54`,
  `profiles/legacy-modernization/scaffold/context/recipes/survey-system.md:28`,
  `profiles/legacy-modernization/scaffold/context/recipes/no-boundary-contract.md:34`,
  `profiles/legacy-modernization/examples/orders-forms-legacy/CARD.md:87`.
  Fine if the profile installs `docs/stacks/` into the project; not checked.

---

## Lead review

<!-- Lead only. -->
