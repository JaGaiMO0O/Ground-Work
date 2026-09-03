<!--
Ground Work bug report.

Before filing, check RUNBOOK.md under "Open defects" - two are already known
and do not need re-reporting. TESTING.md has the full brief.

Leave a field blank rather than guessing at it. A blank field is information;
a guessed one costs somebody an hour finding out it was wrong.
-->

### What happened

<!-- One or two sentences. The symptom, not the theory. -->

### What you expected instead

<!-- If TESTING.md or RUNBOOK.md told you what to expect, quote the line. -->

### Steps to reproduce

1.
2.
3.

### Build

<!-- Output of: git describe --tags -->

```
```

### Environment

<!-- Output of: python --version && git --version && git config core.autocrlf -->

```
```

- OS:
- Shell (PowerShell / git-bash / other):

### The subject repository, if adoption was involved

<!-- Do not name anything confidential - a shape is enough. -->

- Roughly how many source files:
- Language / framework:
- Was the git tree clean before you started:
- Does its `.gitignore` list `.claude/`:

### Output

<!--
Paste the terminal output, including the command. If a hash comparison found
a modified file, paste the diff of that file rather than the hashes - and
check `git diff --stat` first, because on Windows with core.autocrlf=true a
hash can differ from line endings alone, which is already understood.
-->

```
```

### Did anything get modified or deleted that you did not create

<!--
Yes / No / Did not check. Any "yes" is the highest-severity finding in this
build, so say so plainly even if you are unsure.
-->

### Anything else

<!--
Guesses at the cause are welcome here and nowhere above. "I did not
understand this" is a valid report - this build has never been run by someone
who did not write it.
-->

/label ~"build-0A"
