# T05 - check.py enforces the card contracts; budget 2,500

Status: ready
Wave: 2
Depends on: T04
Build: build-0.1A

## Goal

`check.py` enforces contracts C1 (citations), C2 (*Do not read* reasons and
references) and C3 (partial cards, 2,500 budget) from `context/tasks/README.md`,
each proven by a test case that fails when the rule is broken.

## Why

The repo already says evidence discipline matters (`docs/playbook.md`, the
template's *Do not read* guidance). It is prose, and `check.py` never reads a
section's body: `card_gaps` (`scripts/check.py:225-234`) matches headings by
prefix and fields by substring, so an empty `-` passes. The repo's own stated
principle is that rules which live only in prose get broken quietly - and the
first external evaluation found exactly that: the one uncited claim was wrong,
and live code sat in the skip list. Citations become a check here.

`card_gaps` also forces all four sections on every card, which makes the
task-driven partial cards of ADR 0004 impossible.

## Files you may change

- `scripts/check.py` - `card_gaps`, `check_cards`, and new helpers they call
- `scripts/_lib.py` - constants only
- `tests/invariants.py`
- `project.yaml` - the reference comment on `survey:` only (`:90`)
- `context/tasks/T05-check-enforces-card-contracts.md` - Report section and Status line only

## Do exactly this

Read contracts C1, C2, C3 in `context/tasks/README.md`. Implement them as
written; where this brief and the contract differ, stop and ask.

1. **`_lib.py`**
   - `CARD_TOKEN_BUDGET = 2500` (`:71`), comment updated.
   - Add `CODE_SUFFIXES`, a copy of the set in `scripts/_adopt.py`, with a comment
     that `_adopt.py` should import it from here (T10 does that). `check.py` must
     not import `_adopt` - `_adopt.py` does not travel into adopted projects.
2. **Claim extraction (C1).** A helper that returns `(line_number, text)` for each
   claim in a card: bullets and table data rows under `## Owns`,
   `## Interfaces` (with its `###` subsections) and `## Landmines`. Strip
   `<!-- -->` comments while preserving line numbers. A table row followed by a
   `|---|` separator row is a header, not a claim. Apply the C1 exemptions.
   The self-check in `T04` shows one working approach - you may adapt it.
3. **Citation check (C1).** A claim is cited if it matches any of:
   `` `path:N` `` / `` `path:N-M` `` (backticked, and not containing `://`),
   `` `schema:OBJECT` ``, `(per NAME, YYYY-MM-DD)`, `(unverified)`.
   Uncited -> **error**, message containing **`claim has no citation`**, with
   the file and line, and a fix hint naming the four forms.
   Apply to: every declared area's card, the template, and example cards.
4. **Local citations exist (C1).** For areas with `kind: local` only: each
   `path:N` / `path:N-M` must name a file that exists relative to the repo root,
   with `N` and `M` within its line count. Messages:
   - missing file -> **error** containing **`cites` + `does not exist`**
   - line past end -> **error** containing **`has only`** and the line count
5. **Do not read (C2).** For bullets under `## Do not read...`:
   - no backticked path, or reason under 15 characters -> **error** containing
     **`needs a reason that says how it is known to be dead`**
   - `kind: local` only: take the entry's name (file stem; or directory name with
     a trailing `/`, `/**` or `/*` removed). Skip names under 4 characters. Search
     files with a suffix in `lib.CODE_SUFFIXES`, skipping `.git/`, `systems/`,
     `map/`, `context/`, `docs/`, `node_modules/`, any file over 1 MB, and
     anything under the listed path itself. First whole-word match -> **warning**
     containing **`is listed under Do not read but referenced from`** and the
     referencing file.
6. **Partial cards (C3).** For a declared area with a card on disk:
   - `survey: true` -> today's full requirements (every section, every header
     field, a source field), plus 3-5.
   - `survey: false` -> require a source field and at least one recognised
     section; validate only the sections present, plus 3-5 and the budget. Do
     not error on missing sections or on missing `Surveyed:` / `Confidence:` /
     `Stack:` / `Health:`.
   The template and example cards keep today's full structural check.
7. **`project.yaml:90`** comment becomes: `true -> check.py requires a complete
   map/api/CARD.md; false allows a partial one`.
8. **`tests/invariants.py`**
   - Update the fixture `CARD` (`:77-102`) so every claim is cited - the `demo`
     area is `kind: repo`, so format only. Updating fixture *text* so existing
     cases stay valid is in scope. Changing any case's expected exit code or
     expected text is **not** - that is a deviation.
   - Add these cases (name, expected exit, expected text):

     | Case | Exit | Text |
     |---|---|---|
     | card claim uncited | 1 | `claim has no citation` |
     | claim marked unverified `[+]` | 0 | |
     | claim cited per person `[+]` | 0 | |
     | local citation file missing | 1 | `does not exist` |
     | local citation line past end | 1 | `has only` |
     | skip entry without reason | 1 | `needs a reason` |
     | skip entry referenced elsewhere | 2 | `referenced from` |
     | partial card, survey false `[+]` | 0 | |
     | partial card, survey true | 1 | `missing section` |
     | card at 2,400 tokens `[+]` | 0 | |

     The local cases need a `kind: local` area whose `paths:` exist, a card, and
     real files in the work copy - build them in the case's mutation function,
     following the existing `m_local_*` cases.

## Do not

- Change any message text existing cases assert on.
- Touch `AGENTS.md`, the templates, or any skill - other tasks own them.
- Add a citation check to `## Seams`.
- Import `_adopt` from `check.py`.

## Acceptance criteria

- [ ] `python scripts/check.py` exits 0 on this repo.
- [ ] Invariants **49/49** (39 + 10).
- [ ] Each new negative case fails when its rule is commented out - spot-check
      at least the citation and the reference-warning rules this way and say so
      in Report.
- [ ] `check.py` still imports nothing from `_adopt.py`.

## Verify

```bash
python scripts/check.py                       # expected: exit 0
python tests/invariants.py --only claim       # uncited / unverified / per person
python tests/invariants.py --only citation    # local citation file / line
python tests/invariants.py --only skip        # the new Do not read cases
python tests/invariants.py --only partial
python tests/invariants.py                    # expected: 49/49 passed
grep -n "_adopt" scripts/check.py             # expected: no import
```

## Commit

```
feat(T05): enforce citations on area cards
- Uncited claims and stale local citations fail
- Skip entries need a reason; live ones warn
- Partial cards allowed when survey is false
- Card budget 2,500
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit:

**What changed**

**Verify output**

**Deviation requests**

**Found, not fixed**

---

## Lead review

<!-- Lead only. -->
