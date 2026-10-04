# T09 - Remove the Teams-switch drift; derive the build label in docs

Status: ready
Wave: 3
Depends on: T02, T06
Build: build-0.1A

## Goal

No document names a tracker or directory that no longer exists, and no document
hardcodes a build label - they tell the reader to quote `git describe --tags`.

## Why

Commit `1a79a04` moved tester intake to a Teams thread and deleted `.gitlab/`,
but left references behind. And `build-0A` is hardcoded in five places, so every
build would need five doc edits and one would be missed - two copies of a fact,
one of which rots.

- `STATUS.md:15` "**Build 0A** - version 0, alpha; tag `build-0A`."
- `STATUS.md:22` Now line still says intake is "blocked" on moving to Jira.
- `README.md:59` "This is **build 0A**..."; `README.md:75-77` says init deletes
  `.gitlab/`.
- `RUNBOOK.md:143` "Quote the build (`build-0A`) in any report."
- `TESTING.md:3,15` "**Build 0A.**" / `git describe` "should print `build-0A`";
  `TESTING.md:104` expects `.gitlab/` to be gone after `init.py`.

T01 made `init.py` delete `context/tasks/` instead. T06 made the adoption
manifest record `git describe`.

## Files you may change

- `README.md`
- `TESTING.md`
- `RUNBOOK.md`
- `STATUS.md` - the human zone above the generated-zone marker, and the generated
  zone only by running `scripts/status.py`
- `context/tasks/T09-docs-drift-and-build-label.md` - Report section and Status line only

## Do exactly this

1. Every hardcoded build label in the four files becomes an instruction to quote
   the output of `git describe --tags`. Where a doc says what the output should
   be, say "the build named in the Teams announcement" - not a literal label.
2. `README.md:75-77`: the list of what `init.py` deletes becomes "this licence,
   `TESTING.md` and `context/tasks/`".
3. `TESTING.md:104`: the post-init expectation names `context/tasks/` instead of
   `.gitlab/`.
4. `TESTING.md`: where it states the Python requirement, add the sentence T02
   added to README: *"On macOS and Linux the command is often `python3` - use that
   wherever these docs say `python`."*
5. `STATUS.md`, human zone only:
   - `:15` becomes: `**Current build:** whatever \`git describe --tags\` prints. Quote it in any report.`
   - The **Now** row of the goal ladder becomes: `Build 0.1A in progress - task briefs in \`context/tasks/\`. Then a small rollout, measured with \`usage.py --all\` before and after.`
   - Set `reviewed:` to today's date.
   - Leave **Next**, **Done means** and the blockers as they are.
6. Run `python scripts/status.py` to regenerate the derived half.

## Do not

- Rewrite TESTING.md's tracks - T14 changes Track D.
- Touch RUNBOOK's *Open defects* list - T12 and T14 own it.
- Change any command, path or instruction other than those listed.

## Acceptance criteria

- [ ] No hardcoded `build-0A` / `Build 0A` / `build 0A` in the four files.
- [ ] No `.gitlab` in README.md or TESTING.md.
- [ ] `STATUS.md` within its budget; `check.py` exits 0.

## Verify

```bash
grep -n "build-0A\|Build 0A\|build 0A" README.md TESTING.md RUNBOOK.md STATUS.md   # expected: nothing
grep -n "\.gitlab" README.md TESTING.md      # expected: nothing
python scripts/status.py                     # expected: regenerated
python scripts/check.py                      # expected: exit 0
python scripts/status.py --check             # expected: up to date
```

## Commit

```
docs(T09): derive build label; drop .gitlab refs
- Docs say quote git describe --tags
- init deletes context/tasks, not .gitlab
- STATUS Now line reflects 0.1A work
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
