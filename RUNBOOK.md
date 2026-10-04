# Runbook

**The one place that says how to build, test and run this project.**

This repo is a template: there is nothing to compile and nothing to deploy. "Run
it" means run its own tooling against itself, which is also how you know a change
did not break anything.

Every command in `project.yaml` under `commands:` appears here. `check.py` fails
if one is missing - that is what stops this file drifting into fiction.

---

## Setup

You need **Python 3.8+** and **git**. That is the whole hard requirement.

```bash
python --version
```

Optional, and everything degrades cleanly without them:

| Tool | Used for | Without it |
|---|---|---|
| **PyYAML** | parsing `project.yaml` | falls back to the bundled subset parser in `scripts/_minyaml.py` |
| **gitleaks** or **trufflehog** | `scan.py`, including git history | falls back to a bundled regex scan of the working tree, and says so loudly |
| **ripgrep** (`rg`) | fast search honouring `.rgignore` | use `grep`; the exclusions still apply to anything that reads `.rgignore` |
| **bash** | the `.sh` adapters and shims | use the `.py` scripts directly, or the `.ps1` shims on Windows |

```bash
pip install pyyaml
```

No virtualenv, no lockfile, no install step. That is deliberate: this has to drop
into somebody else's repo without bringing dependencies with it.

## Check

Validates every invariant. **Run this before finishing anything.**

```bash
python scripts/check.py
```

Exit `0` clean, `1` errors, `2` warnings only. On a fresh clone before `init.py`,
expect exit 2 with one warning about the `<date>` placeholder in `STATUS.md` -
that is correct; `init.py` fills it.

## Test

The invariant suite. Copies the repo to a temp directory 39 times, breaks one
rule in each copy, and asserts `check.py` notices. Takes about 45 seconds.

```bash
python tests/invariants.py
```

The guard suite. Fires every hook decision and asserts blocks block and nothing
else does. A couple of seconds.

```bash
python tests/hooks.py
```

The adoption suite. Builds a small throwaway project twenty-two times and adopts
it, asserting that nothing pre-existing is edited, that the refusals refuse, and
that the undo puts the project back byte for byte. About 40 seconds.

```bash
python tests/adopt.py
```

All three must be green before a commit. A failure in `tests/invariants.py`
usually means a rule changed without its test, or a rename missed a path.

Useful while working on one rule:

```bash
python tests/invariants.py --only legacy
```

## Usage

Reads the local Claude Code session transcripts and reports where context went.
Advisory; safe to run anywhere.

```bash
python scripts/usage.py
```

Nothing depends on it. If it reports "no readable session telemetry", that is the
expected answer on a machine with no history for this project - not a failure.

## Try it end to end

The fastest way to confirm a change is sound is to use the template as a user
would, on a copy:

```bash
cp -r . /tmp/gw-trial && cd /tmp/gw-trial && rm -rf .git && python scripts/init.py --project trial --profile general --purpose "trying it" --done "tried it"
```

Then `python scripts/check.py` in that copy should exit 0. Adoption into an
existing project is the other path worth exercising:

```bash
python scripts/init.py --adopt /path/to/some/other/repo --dry-run
```

Without `--dry-run` it writes, and records what it wrote in
`.adopt-manifest.json`. To back out:

```bash
python scripts/init.py --undo /path/to/some/other/repo
```

That removes exactly what adoption wrote and keeps anything edited since. Do
not reach for `git clean` instead - it skips whatever the target gitignores and
deletes empty directories it never created, which is how the first version of
this instruction came to be wrong.

---

## Reproducing a result

- **Pinned versions.** None to pin: stdlib Python plus git. PyYAML is optional
  and the fallback parser is tested against it for equivalence on the real
  fixtures.
- **Inputs.** `tests/invariants.py` generates everything it needs. `usage.py`
  reads `~/.claude/projects/*.jsonl`, which differs per machine - so its output
  is *not* reproducible across devices, by nature. Treat its numbers as
  observations about that machine, never as fixtures.
- **Randomness.** None. No seeds, no sampling, no network in the test suites.
- **Environment.** `GUARD_READ_BYTES` and `GUARD_CONTEXT_TOKENS` change the
  guard's thresholds. Adapter credentials live in `.env`, which is gitignored;
  `.env.example` documents the names. Never the values.

## Open defects

Found, reproduced, and not yet fixed. **Check this list before reporting
anything** - what is here is known, so your time is better spent on what is
not. Quote the build (the output of `git describe --tags`) in any report.

Both of these were found by the JLGC adoption trial on 2026-08-16; the full
write-up, including causes and the files involved, is in
`context/handoffs/2026-08-16-jlgc-adoption-trial.md` as defects 3 and 6.

- **Adoption misses the test command on some Python layouts.** The adopted
  `RUNBOOK.md` lands with `# TODO: how do you test this?` even where tests
  plainly exist. Triggers when a root `requirements.txt` only re-exports another
  file (`-r backend/requirements.txt`), or when `tests/` sits below the repo
  root rather than at it. Workaround: fill the command in by hand. It is a
  detection gap, not a wrong answer.
- **`scan.py` reports `*_TOKEN` constants as secrets.** Any identifier ending in
  `token`, `secret` or `key` assigned at the start of a line matches the
  `password-property` rule, so ordinary Python like
  `_NUMERIC_TOKEN = re.compile(` is recorded as a finding. Low volume - 1 hit in
  3,287 files on the trial - and the captured "secret" is visibly not one. Not a
  reason to distrust a real hit.

Neither risks data. Adoption's safety claims are the most-tested part of this:
three trials with 0 pre-existing files modified, and `tests/adopt.py` asserts
the undo restores the target byte for byte.

Delete an entry from this list when it is fixed, not when it is understood.

## Known rough edges

- **`tests/invariants.py` is slow** (~45s) because each case copies the whole
  repo. That is the price of testing `check.py` as a subprocess against a real
  tree, which is what makes the tests trustworthy. `--only` narrows it.
- **Work directories must live outside the repo.** They used to be in
  `.invariant-work/`; on Windows a lingering git process holds the directory and
  `rmtree` fails mid-run with WinError 32. They are in the system temp dir now.
- **Never hand-build hook payloads as JSON strings.** Windows paths contain
  backslashes, which are JSON escapes; the parse fails, the guard exits 0, and
  the test silently passes for the wrong reason. `tests/hooks.py` uses
  `json.dumps`.
- **`scan.py` without gitleaks reads the working tree only.** Git history is
  where old credentials hide. The warning says so; do not treat the fallback as
  a passed security gate.
- **The `.sh` adapters need bash.** On Windows that means git-bash. The `.ps1`
  shims cover the Python scripts, not the adapters.
