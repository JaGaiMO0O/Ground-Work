# T18 - Remove the last "survey first" messages

Wave: 5
Lane: Workflow
Depends on: T11, T16
Estimate: S (~30 min)
Build: build-0.1A

## Goal

No message the tools print, and no generated file, tells a user to survey an area
up front. Everything says what ADR 0004 says: cards grow from tasks, and a full
survey happens at an area's third task, after asking a human.

## Why

T11 removed five survey-first instructions; its worker found four more outside
T11's lane:

- `scripts/init.py:807` - fresh-init "Next": `4. python scripts/new_card.py <area>   - then survey it`
- `scripts/_adopt.py:418` - generated `project.yaml` header: "`survey: true` on one
  when you are ready to write its card." (implies one area gets surveyed right after adoption)
- `.claude/README.md:29` - `survey-area` row: "dedicated session ... output only the
  card" - silent on the third-task trigger and the human questions
- `scripts/usage.py:265` - re-read advice: "Survey the areas they belong to:
  python scripts/new_card.py <area>"

## Owns

- `scripts/init.py` - the fresh-init "Next" message string only
- `scripts/_adopt.py` - the `project.yaml` header comment lines only
- `.claude/README.md` - the `survey-area` row only
- `scripts/usage.py` - that one advice string only
- `docs/plan/tasks/T18-last-survey-first-messages.md` - Handoff only

## Scope - do exactly this

Use this wording. Keep each string's existing layout (indentation, `\n`, width).

1. `init.py:807`: `4. python scripts/new_card.py <area>   - start a partial card; full survey at the area's third task`
2. `_adopt.py:418` (and the line before it if the sentence spans two): the header
   says `survey: true` marks a card complete and maintained, set after a full
   survey, which happens at an area's third task (ADR 0004).
3. `.claude/README.md:29`: `Full survey of one area, at its third task: asks a human first, delegates the wide reading, outputs only the card`
4. `usage.py:265`: point at promoting the card -
   `. Promote those areas' cards with a full survey (ADR 0004): python scripts/new_card.py <area>`

## Do not

- Change any other string, logic, or file.
- Add tests - these are messages, not behaviour. If an existing test asserts on any
  of these exact strings, stop and escalate.

## Acceptance criteria

- [ ] `grep -rn "then survey it\|ready to write its card\|Survey the areas" scripts .claude`
      finds nothing.
- [ ] `check.py` exits 0; adopt suite and invariants still pass in full.

## Verify

```bash
grep -rn "then survey it\|ready to write its card\|Survey the areas" scripts .claude   # expected: nothing
python scripts/check.py        # expected: exit 0
python tests/adopt.py          # expected: 32/32 passed
python tests/invariants.py     # expected: 51/51 passed
python scripts/usage.py --all | head -40   # the advice line renders sensibly
```

## Commit

```
docs(T18): drop the last survey-first messages

- init, adopt header, .claude README, usage advice
- All now say: grow cards; survey at the third task
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit:

**What changed**

**How it was verified**

**Deviations** (escalations raised, and the answers)

**Follow-ups** (found, not fixed - file and line)

**Rollback**

---

## Lead review

<!-- Lead only. -->
