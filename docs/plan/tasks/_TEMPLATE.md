# Txx - <short imperative title>

Wave: <n>
Depends on: <Txx, Txx | none>
Lane: <lane>
Estimate: <S | M | L, with a time>
Build: build-0.1A

## Goal

<One or two sentences. What is true when this is done.>

## Why

<1-3 lines, with the evidence: a file and line, a review finding, a measurement.>

## Owns

<Exhaustive. Anything not listed here is a deviation - see docs/plan/PROTOCOL.md.>

- `<path>`
- `docs/plan/tasks/Txx-<slug>.md` - Handoff only

## Do exactly this

1. <step>
2. <step>

## Do not

- <the tempting adjacent change that belongs to another task>

## Acceptance criteria

- [ ] <checkable statement>

## Verify

```bash
<exact command>    # expected: <result>
```

## Commit

```
<type>(Txx): <description, <= 50 chars>

- <bullet>
```

No `Co-Authored-By` trailer. Stage only the files you own. Never push.

---

## Handoff

<!-- Task session fills this in. Status lives in docs/plan/ROADMAP.md, lead-only. -->

Branch / commit:

**What changed**

**How it was verified**

**Deviations** (escalations raised, and the answers)

**Follow-ups** (found, not fixed - file and line)

**Rollback**
---

## Lead review

<!-- Lead only. -->
