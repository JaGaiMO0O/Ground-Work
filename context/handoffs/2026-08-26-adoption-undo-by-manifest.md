# Handoff 2026-08-26 - adoption undo by manifest

**Goal:** fix defect 1 from the JLGC trial
([2026-08-16](2026-08-16-jlgc-adoption-trial.md)) - the advertised undo was an
untrue safety claim - and stop before the other five, which are ordinary.

## Done

**Defects 1 and 2 were one defect.** 1 said the undo left files behind; 2 said it
deleted files it never wrote. So `git clean -fd` was neither complete nor
contained, and no better wording fixes that. The mechanism had to go.

**`.adopt-manifest.json`.** Adoption now records every path it wrote with a
content hash, the directories it created, the prior bytes of `.gitignore`, and
the Ground Work commit that wrote it. `python scripts/init.py --undo <dir>`
reads it.

| Old failure | Now |
|---|---|
| Ignored files survived | The manifest does not care what git thinks is disposable |
| Pre-existing empty dirs deleted | Only directories recorded as *created* are removed |
| `.gitignore` untouched | Restored from the bytes it had, not from git's opinion of them |
| Would have eaten edited files | Hash mismatch -> kept, named, and the manifest kept as the record |
| No manifest | Refuses. Deleting by pattern is how you eat somebody's own AGENTS.md |

**What survives of the git-clean advice is derived.** `git check-ignore -z` over
the paths actually written, so the message says *"this project gitignores 9 of
the files adoption just wrote"* rather than reciting our own block. That is the
fix the trial asked for.

**Verified against the trial's own pass condition** on a fixture reproducing the
JLGC shape - a gitignored `.claude/`, two pre-existing empty directories.
After-undo file hashes identical, path set identical *including the empty
directories*, `git status` clean. That condition could not be met before.

**Half of ADR 0003's open item closes on the way past.** The manifest carries
`template_version`, so an adopted copy can finally say how old its scaffold is.
There is still no `--update`, and the ADR consequence still says otherwise.

`tests/adopt.py` 18 -> 21 cases: the round trip, the edited-file case, the
refusal with no manifest. The two existing cases that asserted on the *wording*
of the old undo were rewritten - they were testing a sentence, and the sentence
was the defect. Suites: adopt 21, invariants 39, hooks 21, `check.py` clean.

## Open

Defects 3-6 from the JLGC handoff, untouched and still accurate as written:
the missed test command on a project with 84 tests (three independent causes),
the circular install hint at `check.py:533`, `jlgc---copy` on line 1 of Tier 0,
and the `scan.py` false positive. 5 is a one-line collapse of separator runs and
sits in the file every session reads - worth pulling forward.

ADR 0003's consequences still read *"59 files against a 6-file project... not
obviously right"*. Three real adoptions since have measured 0.64x, 0.91x and
~1x. That is a claim in the permanent record the evidence no longer supports,
and ADRs here are immutable, so it wants an 0004.

**Key files:** `scripts/_adopt.py` (`write_manifest`, `read_manifest`,
`dirs_that_would_be_created`, `ignored_by_target`), `scripts/init.py` (`undo`,
`read_exact`/`write_exact`, `adopt`'s `written` list), `tests/adopt.py`.

**Gotcha:** newline translation caused two more bugs *inside the fix for the bug
newline translation caused*. `write_text` restored `.gitignore` as CRLF where the
working tree had been LF; then a text-mode pipe into `git check-ignore`
translated on the way in, so git echoed back `.claude/README.md\r` and quoted it
as a path with a control character. Python translates newlines on read *and* on
write *and* on subprocess pipes, and on Windows every one of those is a silent
corruption of bytes you promised to preserve. Use `newline=""` when the bytes
matter, and `-z` with bytes for anything piped to git.

Both were found by running the thing rather than reading it - which is the same
way the original defect was found, and the reason the trial that found it was
worth more than the two before it.

That makes four instances of one rule: **anything adoption claims about a target
must be derived from that target at runtime.** A POSIX path this OS could not
resolve; a hook reading its root from a payload field that could be absent; a
test directory looked for only at the repo root; an undo naming exclusions from
our gitignore rather than the target's. Four is a pattern, so it is now in
`docs/playbook.md` §11 rather than in a handoff nobody will grep.

**Next:**

1. Defect 5, then 3. Both cheap; 5 lands in Tier 0.
2. **Then stop fixing and start using.** Three trials have each found ~6 defects
   and there will always be another repo with another awkward shape. Nothing so
   far tests whether any of this *helps* - only that it is safe. Dry bean is
   still the only subject with the session history to answer that: adopt it for
   real, card `src/`, work normally for a week, then re-measure against the
   recorded baseline of 33% orientation and 41 files re-read across 3+ sessions.
3. ADR 0004 on the weight consequence, whenever it is convenient.
