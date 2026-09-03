# Handoff 2026-09-03 - build 0A tester handover

Goal: get the repo ready to hand to internal testers - documents, not code -
and tag it as build 0A.

Done: tagged `build-0A` (annotated, carries the green suite counts and the two
known defects). Added `LICENSE` (Optimiza proprietary, evaluation use) and
`TESTING.md` (four tracks; Track B is the hash-before-and-after adoption
protocol extracted from the trials). Listed JLGC defects 3 and 6 in
`RUNBOOK.md` under *Open defects* so testers stop re-finding them. Fixed
README's clone URLs, which still pointed at the old GitHub remote. `init.py`
now deletes `LICENSE`, `TESTING.md` and `.gitlab/` when scaffolding, with an
adoption test proving they never travel - without it, every scaffolded project
carried Optimiza's licence over its owner's own work.

Open: **GitLab Issues is disabled org-wide and will not be enabled** - "only
use Jira, we are not supporting GitLab Issues". So `.gitlab/issue_templates/`
is dead weight and `TESTING.md` plus `README.md` both point at a tracker that
404s. Nothing can be handed to a tester until that is repointed at Jira. The
Jira project key is not yet chosen. `build-0A` is not pushed; `main` is.

Key files: `TESTING.md` (intake section), `.gitlab/issue_templates/` (to
delete), `README.md` (Testing section), `scripts/init.py`
(`TEMPLATE_ONLY_FILES`), `tests/adopt.py` (`no_template_only_files_travel`).

Gotcha: a disabled GitLab feature returns a bare 404, and when Issues is off
above the project the per-project toggle is not rendered at all - so it reads
as a missing page rather than a policy. Half an hour went into looking for a
toggle that could not exist. Also: Jira has no repo-based issue templates, so
the field list has to live in `TESTING.md` as a block testers copy, not as a
form.

Next:

1. Get the Jira project key, then repoint `TESTING.md` and `README.md`, delete
   `.gitlab/`, and drop `.gitlab` from `init.py` and `tests/adopt.py`.
2. Re-run all three suites, move the `build-0A` tag, push `main` and the tag.
3. Then the two open JLGC defects, or hand over and stop fixing.
