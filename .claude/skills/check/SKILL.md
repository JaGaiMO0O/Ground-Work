---
name: check
description: Validate the control repo's invariants and fix what is broken. Use before finishing any piece of work, when check.py reports a failure, or when asked whether the repo is in good shape.
---

# Validate the repo

```bash
python scripts/check.py
```

Exit `0` clean, `1` errors, `2` warnings only. Run it before you finish
anything.

## What each failure actually means

**`Tier 0 is over budget` / `AGENTS.md is N lines`**
Tier 0 is re-sent on every turn of every conversation, so this is the most
expensive file in the repo per byte. Move detail into `context/recipes/` or
`docs/`. `AGENTS.md` is a router, not a manual.

**`survey: true but no CARD.md`**
Run `python scripts/new_card.py <system>`, then the `survey-system` skill.
Or, if the system barely matters to the integration, set `survey: false` -
a card is only worth writing when a system will be read more than twice.

**`CARD.md missing section(s)`**
The missing section is usually **Owns** or **Do not read**, and those are the
two that carry the most value. Fill them; do not delete the heading.

**`legacy source file(s) committed to the control repo`**
The structural rule of the whole repo has been broken. Legacy source belongs in
`systems/` (gitignored) or converted into `map/<sys>/derived/`. Move it
and `git rm --cached` the copy.

**`.env is tracked by git`**
Stop. `git rm --cached .env`, then **rotate every credential that was in it**.
The file being removed from HEAD does not remove it from history.

**`ref 'main' is a moving branch`**
Pin to a tag or SHA. An unpinned ref means the card describes code that may no
longer exist, and nothing will tell you when that happens.

**`card surveyed at X but project.yaml now pins Y`**
Drift. Either re-survey, or lower the `Confidence:` marker to reflect that the
card describes an older commit. Lowering confidence is a legitimate answer - it
costs nothing and it warns the next reader.

**`.rgignore is out of sync`**
`python scripts/sync.py`. It is generated; never hand-edit it.

**`no 'Do NOT load:' section`** in a recipe
Naming what to skip is half of what a recipe is for. Add it.

**`adapter 'X' declared but not found`**
Either the name in `project.yaml` is a typo, or the adapter needs writing.
See `docs/adapters.md` and copy the nearest reference.

## Warnings are not noise

Exit 2 means nothing is broken *yet*. Drift warnings and LOW-confidence notes
are the early signal that a card is becoming fiction. The notes section also
reports the metric that matters most: whether Tier 0 is still small enough to
be worth loading every turn.
