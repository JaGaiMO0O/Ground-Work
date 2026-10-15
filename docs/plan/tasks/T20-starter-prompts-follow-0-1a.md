# T20 - The starter prompts follow 0.1A's card rules

Wave: 8
Lane: Workflow
Depends on: T11, T18
Estimate: S (~30 min)
Build: build-0.1A

## Goal

The two prompts in `docs/starter-prompt.md` teach what the scaffold now
enforces: cards grow from tasks, every claim cites its source or is marked
`(unverified)`, a full survey waits for an area's third task and asks a human
first, and the card budget is 2,500.

## Why

The user asked, 2026-10-15. `docs/starter-prompt.md` was in no lane in waves
4-7, so T11 and T18 never reached it. It is linked from `START-HERE.md:140` and
`docs/playbook.md:364`, and travels with adoption. Its own footer says to keep it
in step with `docs/playbook.md`. As of `main` at `cedc750`:

- **Prompt 1** tells the agent to create `map/<area>/CARD.md` "one card per part
  of the codebase" at setup. ADR 0004 (`docs/playbook.md:163-167`) says no cards
  up front: they grow from tasks, with a full survey at the third task.
- No citations. `docs/playbook.md:154-161` makes them the drift management.
- No interview before a survey, and no *Open questions*.
- The *what not to read* entries carry no reason, and nothing says the list never
  applies to diagnosis (`docs/playbook.md:150-152`).
- The budget is "2000 per card". T05 made it 2,500.
- **Prompt 2** (global habits) is mostly sound, but it has no citation habit.
  Without one, the agent writes plausible, unchecked claims everywhere.

## Owns

- `docs/starter-prompt.md` - Prompt 1 and Prompt 2 code blocks only
- `docs/plan/tasks/T20-starter-prompts-follow-0-1a.md` - Handoff only

## Scope - do exactly this

Keep each prompt's voice, imperative and addressed to the agent, with lines at
the existing width (~80 columns).

**Prompt 1:**

1. Replace the `map/<area>/CARD.md` bullet with:
   ```
   - map/<area>/CARD.md - none at setup. Cards grow from work: when a task
     teaches you a landmine, add it to that area's card, starting a partial
     card if there is none. When an area is worked in its third task, survey
     it fully - but first ask me, in one message, the questions only a human
     can answer, and wait. A card holds: what the area owns, its interfaces,
     its landmines, what not to read and why, and open questions.
   ```
2. In *Hold to these*, add after the "Derive rather than describe" bullet:
   ```
   - Every claim on a card cites the line that proves it (path:line), or my
     answer (per NAME, DATE), or is marked (unverified). A card says where to
     look, not what is true: open the cited line before stating it as fact.
   - Each "what not to read" entry says how you know it is dead, and the list
     never applies when diagnosing a bug or a slowdown.
   ```
3. In the budget bullet, change `2000 per card` to `2500 per card`.
4. In *Do not*, change `card a file nobody will read twice` to
   `survey an area before its third task`.

**Prompt 2**, in the `## Working with agents` block:

5. Add after "Say what you could not determine...":
   ```
   - When you write down how something works, cite the file and line it came
     from, or mark it unverified. Ask a person for what the code cannot tell
     you.
   ```

## Do not

- Change any text outside the two code blocks: the intro, *Why three of those
  lines*, the manual, the pocket version, or the footer.
- Change the playbook, ADR 0004, `START-HERE.md`, or any script.
- Add a test. The prompts are prose for a human to paste.

## Acceptance criteria

- [ ] `grep -n "2000 per card\|one card per part\|card a file nobody" docs/starter-prompt.md`
      finds nothing.
- [ ] `grep -n "third task\|(unverified)\|2500 per card" docs/starter-prompt.md`
      finds each one inside the Prompt 1 block, and "cite the file and line"
      inside the Prompt 2 block.
- [ ] `check.py` exits 0; invariants 51/51.
- [ ] The diff touches only lines inside the two `text` code blocks.

## Verify

```bash
grep -n "2000 per card\|one card per part\|card a file nobody" docs/starter-prompt.md   # expected: nothing
grep -n "third task\|(unverified)\|2500 per card\|cite the file and line" docs/starter-prompt.md
python scripts/check.py        # expected: exit 0
python tests/invariants.py     # expected: 51/51 passed
```

## Commit

```
docs(T20): align starter prompts with 0.1A

- Prompt 1: cards grow from tasks; cite or mark
- Prompt 1: survey at third task, ask first; 2500
- Prompt 2: add the citation habit
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
