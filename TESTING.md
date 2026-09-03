# Testing Ground Work

**Build 0A.** You are one of the first people outside its author to run this.

This page is the whole brief. It says what to exercise, what a correct result
looks like, and how to file what you find. Twenty minutes gets you through
Track A; Track B is the one that matters and takes about an hour.

> **Confirm the build before you start.** Every report needs it.
>
> ```bash
> git describe --tags
> ```
>
> That should print `build-0A`, possibly with a commit suffix if you have
> pulled since.

---

## File your findings here

**<https://gitlab.optimizasolutions.com/myaghmour/ground-works/-/issues>**

Open an issue per finding. The **Bug** template loads automatically and asks
for the seven things that make a report actionable - fill it in rather than
writing prose, because the fields are the ones that were missing from reports
that could not be reproduced.

Two rules:

1. **Check *Open defects* in [RUNBOOK.md](RUNBOOK.md) first.** Two defects are
   already known and written down. Re-reporting them costs you time and tells
   nobody anything.
2. **File as you go, not at the end.** One issue per finding beats one issue
   listing nine, because nine cannot be closed separately.

Nothing here is urgent. File it and carry on; it gets picked up when there is
time.

---

## Before you start

You need **Python 3.8+** and **git**. Nothing else, no virtualenv, no install
step.

```bash
python --version
git --version
```

**Pick a subject repository for Track B now**, because the choice shapes the
result. What makes a good one:

- A project you know well enough to notice a wrong answer about it.
- Real size - tens of source files, not three.
- Already a git repository, with a clean tree.
- **A copy.** `cp -r` it, or clone it somewhere scratch. Adoption is designed
  to be reversible and the undo is tested, but you are here to test that
  claim, not to rely on it.

---

## Track A - a project from scratch

Ten minutes. Proves the template turns into a project.

```bash
git clone https://gitlab.optimizasolutions.com/myaghmour/ground-works.git track-a
cd track-a
rm -rf .git && git init
python scripts/init.py
```

On PowerShell that third line is `Remove-Item -Recurse -Force .git; git init`.

`init.py` asks what the project is for and how you will know it is finished.
Answer as if it were real - vague answers hide the defects.

**Expected afterwards:**

| Check | Correct result |
|---|---|
| `python scripts/check.py` | exit 0, `all invariants hold` |
| Line 1 of `AGENTS.md` | your project's name, no `<PROJECT_NAME>`, no mangled punctuation |
| `README.md` | opens with your project name; the clone-and-adopt instructions are gone |
| `STATUS.md` | your two answers in the goal ladder, not Ground Work's |
| `LICENSE`, `TESTING.md`, `.gitlab/` | gone - they describe the template, not your project |
| `grep -rn "<PROJECT_NAME>\|<ONE SENTENCE>" .` | no hits outside `profiles/` |

Then read [START-HERE.md](START-HERE.md) and do what it says, **as written,
without asking anybody**. This is the part with no test coverage and the part
most likely to be wrong. Where you get stuck, that is the finding - file it
even if you worked it out, and say what you expected to happen.

---

## Track B - adoption into a project that already exists

The important track, and the one where a defect would actually cost somebody
something. The claim under test is exact:

> Adoption adds files and modifies nothing that was already there. The undo
> removes exactly what adoption wrote and keeps anything you edited since.

### Measure it, do not trust it

Hash the subject before and after. Every real defect so far was found this way
rather than by reading output.

**Keep the baseline outside the subject repository** - adoption refuses to run
on a dirty tree, and a baseline file sitting in the subject makes it dirty.

```bash
cd /path/to/subject
find . -path ./.git -prune -o -type f -print | sort | xargs md5sum > ~/before.txt
```

PowerShell:

```powershell
Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.git\\' } | Get-FileHash -Algorithm MD5 | Select-Object Hash,@{n='P';e={Resolve-Path -Relative $_.Path}} | Sort-Object P | Export-Csv ~\before.csv -NoTypeInformation
```

### Run it

```bash
cd /path/to/ground-works
python scripts/init.py --adopt /path/to/subject --dry-run
```

Read the plan. **Write down the counts it predicts**, then run it for real by
dropping `--dry-run`.

### What to check

| Check | Correct result |
|---|---|
| Dry-run vs real run | the counts match exactly |
| Re-hash and diff against your baseline | **zero modified, zero deleted.** Only additions |
| `.gitignore` | may be appended to - and adoption must say so out loud |
| `git status` in the subject | only untracked additions |
| `RUNBOOK.md` | names the subject's real build and test commands |
| `AGENTS.md` line 1 | the subject's name, cleanly slugified |
| `python scripts/check.py` in the subject | runs and explains anything it complains about |

A **modified or deleted pre-existing file is the highest-severity finding in
this build.** File it immediately and stop.

### Then undo it

```bash
python scripts/init.py --undo /path/to/subject
```

Re-hash. **The after-undo set should equal your before set**, and anything you
edited in the meantime should survive.

> **Do not file line-ending differences as a defect.** On Windows with
> `core.autocrlf=true`, git rewrites LF to CRLF on checkout, so a hash can
> differ for a file whose content never changed. Check with
> `git diff --stat` before reporting - if git sees no change, the hash
> difference is the line endings, and that is already understood.

### Worth trying deliberately

- Adopt into a repo with a **dirty tree**. It must refuse, and say why.
- Adopt into a repo that **gitignores `.claude/`**. The guardrails will never
  be committed there - does anything tell you that?
- Adopt **twice** into the same subject.
- Run the undo **without having adopted**. It must refuse, not guess.
- A subject with a **space or punctuation in its directory name**.
- A subject whose tests live **below the root** (`backend/tests/`) - see the
  known defect first.

---

## Track C - the guardrails

Fifteen minutes, in an adopted subject. These must **block**:

- Reading a real secrets file (`.env` with live-looking values).
- Writing to anything under `systems/`.
- Hand-editing a generated file - one with a `GENERATED` header.

These must **not** block, and a false block is a defect worth filing:

- Reading `.env.example`.
- Reading and writing ordinary source files.

Everything else the repo says is a **warning, not a wall**. If something warns
you and gives you no way forward, that is a finding.

---

## Track D - the numbers

```bash
python scripts/usage.py --all
```

This reads your local Claude Code session history and reports where context
went. It is advisory and reads nothing but transcripts.

Judge one thing: **do the numbers describe your actual experience?** If it
claims a project cost you very little and you remember burning an afternoon on
it, that is worth a report - a budget tool that under-reports reads as good
news, which is the worst way for it to be wrong.

`no readable session telemetry` on a project you have never used an agent in is
the correct answer, not a failure.

---

## What counts as a finding

File all of these:

- Anything modified or deleted that adoption did not create. **Highest.**
- A safety claim in the docs that is not true.
- An instruction you followed exactly that did not work.
- A place you got stuck in `START-HERE.md`, even if you got past it.
- A number you do not believe.
- A block with no way forward, or a warning you could not act on.
- Wording that read as confident about something it could not know.

Do not file:

- The two entries under *Open defects* in `RUNBOOK.md`.
- The blockers in `STATUS.md` - those are known and owned.
- `tests/invariants.py` taking about 45 seconds. It is documented and
  deliberate.

**"I did not understand this" is a valid and useful report.** This build has
never been run by someone who did not write it, so confusion is data, not
your mistake.

---

## If you want the short version

Run Track B against a copy of something real, hash it before and after, undo
it, and hash again. If those three sets do not line up the way this page says
they will, that is the finding worth having.
