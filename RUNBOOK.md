# Runbook

**The one place that says how to build, test and run this project.** If the
answer lives in someone's shell history, it lives here instead.

Every command declared in `project.yaml` under `commands:` must appear here with
an explanation. `check.py` fails if one is missing - that is what stops this file
drifting into fiction.

---

## Setup

What a person needs before anything works: language version, package manager,
services, credentials. Be specific about versions - "Node 20.11" not "recent
Node".

```bash
# install
```

## Test

```bash
# test
```

How long it takes, and what a normal failure looks like. If some tests need a
database or network, say which and how to skip them.

## Run

```bash
# run
```

Where it listens, what it needs running alongside it, and how to tell it started
correctly.

## Build

```bash
# build
```

## Lint / format

```bash
# lint
```

---

## Reproducing a result

The part people skip, and the part that matters six months later. Enough for
somebody else to get the same output you got:

- **Pinned versions.** Which lockfile is authoritative, and how to install from
  it exactly rather than approximately.
- **Inputs.** Where the data or fixtures come from, and which version of them.
- **Randomness.** Seeds, and anything else that varies between runs.
- **Environment.** Variables that change behaviour - and their safe defaults.
  Never the secret values; those live in `.env`, which is gitignored.

If a result cannot be reproduced from this section alone, it is not reproducible,
and saying so here is more useful than implying otherwise.

## Known rough edges

Things that will waste an hour if nobody warns you: the test that fails on a
clean checkout until you run something first, the build step that needs to be run
twice, the port that is usually already taken.

<!--
WHY THIS FILE EXISTS

An agent that cannot find out how to run the tests will either guess or ask. The
guess costs a wrong turn; the question costs a round trip. Both are avoidable by
writing it down once.

It is also the reproducibility contract. `project.yaml` holds the machine-
readable command list; this file holds the reasoning, the versions and the
gotchas around them. check.py checks the two agree.
-->
