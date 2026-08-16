# Handoff 2026-08-16 - JLGC adoption trial

**Goal:** second real adoption trial, against a larger and messier project than
the dry-bean one, and this time run the *undo* rather than reading it.

**Subject:** `Desktop/JLGC - Copy` - a FastAPI OCR/advisory pipeline. ~50 source
files under `backend/`, 84 pytest tests, a real `backend/.env`, an 8k-file
`.venv`, and a pre-existing `.claude/` and `.cursor/`. Clean git tree. A copy,
so destructive testing was safe.

**Method:** MD5-hashed all 136 pre-existing files before and after, so
"non-destructive" is measured rather than asserted.

## Done

- **0 pre-existing files modified, 0 deleted.** Only `.gitignore` changed, and
  adoption announced it. 51 files added.
- Dry run predicted `46 added, 0 proposed`; the real run matched exactly.
- **Rule 4 held.** Only `_TEMPLATE.md` travelled out of `context/handoffs/` and
  `docs/decisions/`. `STATUS.md` rendered fresh from the template.
- **The weight fix landed.** 46 scaffold files against ~50 real source files.
  Was 4.75x on the last trial; now roughly 1x.
- **`guard.py` correct on real inputs:** blocked `backend/.env` (live
  credentials), allowed `backend/.env.example` and `backend/main.py`, blocked
  `systems/` writes and `.rgignore` edits.
- **`check.py` enforcement loop verified end to end:** placeholder card -> warn;
  `survey: true` with card deleted -> FAIL exit 1; card restored -> pass.
- `status.py`, `new_card.py`, `handoff.py`, `sync.py` all ran. `usage.py`
  degraded cleanly (no transcripts for that directory). Tier 0 738/1500.
- The dirty-tree gate refuses correctly - proved by accident.

## Open - defects found, none fixed

**1. The undo is wrong, and it is a safety claim.** The target's own
`.gitignore` contains `.claude/`. `git clean -fd` never touches ignored files,
so all 8 `.claude/**` files adoption wrote survive the undo - including
`settings.json` (deny rules + hook wiring), `agents/surveyor.md`, and 5 skills.
Ran the undo verbatim to confirm. The message names only `systems/` as the
ignored exception because that list is hardcoded from *our* gitignore block
rather than asked of the target's git. Fix: `git check-ignore` over the actually
added paths, and name whatever comes back.

**2. The undo deletes pre-existing directories.** `git clean -fd` removed
`.cursor/`, `backend/scripts/` and `backend/static/`. All three predate
adoption. They were **empty**, so `git status --porcelain` reported a clean tree
- which is exactly why the "exact only because the tree was clean" precondition
could not see them. Harmless placeholders here; the claim "removes the files
adoption ADDED" is still false. Fix: write the added-file list and delete from
it, or check for untracked empty dirs in the precondition.

**3. Test command missed on a project with 84 tests.** RUNBOOK.md says
`# TODO: how do you test this?`. Three independent causes in `_adopt.detect()`:
the `requirements.txt` branch never greps for `pytest` the way the
`pyproject.toml` branch does; root `requirements.txt` is a one-line
`-r backend/requirements.txt` re-export and the indirection is not followed; and
`tests/` is only looked for at the repo root, not one level down. Not rule 2
being conservative - it was detectable three ways.

**4. Circular install hint.** `check.py:533` prints `'install' command needs
'pip', which is not on PATH - try: pip install -r requirements.txt`. When the
failing command *is* the install command, the hint is the thing that just
failed.

**5. Project name `jlgc---copy`.** `target.name.lower().replace(" ", "-")` on
`JLGC - Copy`. Lands on line 1 of AGENTS.md, read every turn. Collapse
separator runs.

**6. `scan.py` false positive.** `_NUMERIC_TOKEN = re.compile(` in
`backend/extractors.py:32` recorded as `password-property`; the captured
"secret" is the literal `re.compile(`. The rule matches any identifier ending in
token/secret/key assigned at line start. 1 hit in 3,287 files so not flooding,
but `scan.py:47` says a noisy gate gets switched off, and `*_TOKEN` constants
are ordinary Python.

**Not a defect, checked and dismissed:** `.rgignore` omits `.venv`, but ripgrep
reads `.gitignore` natively and the target ignores `.venv/`. The 8,017-file venv
is already excluded.

**Worth telling an adopter:** because this project gitignores `.claude/`, none
of the guardrails or skills adoption installs will ever be committed. Adoption
does not mention it.

**Key files:** `scripts/init.py` (`adopt()` - the undo message, ~line 326),
`scripts/_adopt.py` (`detect()` ~line 170), `scripts/check.py:533`,
`scripts/scan.py:66`.

**Gotcha:** two of the six defects are the same failure as the last trial's
`native_path` bug - a claim asserted from a static assumption instead of asked
of the environment. The undo names `systems/` from *our* gitignore, never the
target's. Anything adoption promises about the target must be derived from the
target at runtime. Also: `git status --porcelain` cannot see untracked empty
directories, so a "clean tree" precondition does not mean `git clean -fd` is
safe. And `git checkout -- .gitignore` does not byte-restore under
`core.autocrlf=true` - it came back CRLF where the working tree had been LF.

**Next:**

1. Fix 1 and 3 first - 1 is an untrue safety promise, 3 leaves the runbook
   silent about the command most worth having.
2. Then 2, 4, 5, 6.
3. Re-run this trial against `Desktop/JLGC - Copy` and re-execute the undo; the
   pass condition is that the after-undo hash set equals the before set.
