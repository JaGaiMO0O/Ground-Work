# T04 - Card templates and examples: citations, skip reasons, open questions

Wave: 1
Depends on: T00
Build: build-0.1A

## Goal

Both card templates teach contracts C1, C2 and C4 from `context/tasks/README.md`,
and both legacy example cards follow them - so every card written from 0.1A on
starts in the right shape.

## Why

The first external evaluation (27 Sep 2026): **every claim on the card that
cited a line was correct; the one claim without a line reference was wrong**, and
the agent repeated it. Separately, the card's *Do not read* list named live code,
and the second-largest cause of a slowdown was in it. Today the template
(`map/_TEMPLATE/CARD.md`) has no citation field anywhere; its only evidence
guidance is in the *Do not read* comment (`:72-73`). One `Confidence:` line
covers the whole card (`:3`).

Examples teach the habit more than guidance does, so the legacy example cards
must model it.

## Files you may change

- `map/_TEMPLATE/CARD.md`
- `profiles/legacy-modernization/scaffold/map/_TEMPLATE/CARD.md`
- `profiles/legacy-modernization/examples/billing-legacy/CARD.md`
- `profiles/legacy-modernization/examples/orders-forms-legacy/CARD.md`
- `context/tasks/T04-card-template-citations.md` - Report section and Status line only

## Do exactly this

Read contracts C1, C2, C4 in `context/tasks/README.md` first. Implement them as
written.

**In both templates:**

1. In the guidance comment block near the top, add a short paragraph (4-6 lines)
   stating C1: every claim under Owns, Interfaces and Landmines carries one of
   `` `path:N` ``, `` `schema:OBJECT` ``, `(per NAME, YYYY-MM-DD)`, or the marker
   `(unverified)`. Say why in one sentence: a card is a map that says where to
   look; an uncited claim is a guess the next reader repeats as fact.
2. Keep the single `Confidence:` header line (area level). In its guidance, add
   that doubt about an individual claim is marked `(unverified)` on that claim.
3. Change the placeholder bullets under Owns and Landmines so each shows a
   citation, e.g. `- <what this area is authoritative for> - `<path>:<line>``.
4. In the Interfaces *In* table, put the citation in the *Entry point* column
   placeholder: `` `<path>:<line>` ``.
5. In the *Do not read* section's guidance, state C2: each entry is a backticked
   path followed by why it is dead and how that is known; and that the list
   **never applies when diagnosing a bug or a slowdown**. Keep the existing
   "Say WHY it is dead and how you know" sentence.
6. Add an optional section at the end, `## Open questions`, with a comment saying
   it holds interview questions nobody could answer (C4), and that the claim each
   one bears on stays `(unverified)`.
7. Change the stated card budget from 2,000 to **2,500** tokens.
8. Keep every existing required heading (`## Owns`, `## Interfaces`,
   `## Landmines`, `## Do not read...`) and header field (`Surveyed:`,
   `Confidence:`, `Stack:`, `Health:`, and the source field) exactly as they are -
   `check.py` validates the template against them.

**Legacy template only:** in the guidance, add how to cite where code is not a
plain tree: for a `kind: repo` area cite paths relative to that repository's
root; for Forms and other binaries cite the file under `derived/`; for database
logic cite `schema:OBJECT`. Leave `## Seams` as it is - seams carry their own
*Evidence* field, enforced elsewhere.

**Both legacy example cards:** give every claim under Owns, Interfaces and
Landmines a citation in one of the C1 forms - plausible paths consistent with
what each card already says. Across the two cards, show **every** form at least
once: `path:N`, `path:N-M`, `schema:OBJECT`, `(per NAME, YYYY-MM-DD)` and
`(unverified)`. Give every *Do not read* entry a C2 reason. Add a short
`## Open questions` section to one of them with one real-sounding question.

## Do not

- Change `scripts/check.py` or `scripts/_lib.py` - T05 enforces these rules.
- Add citations to `## Seams` or `## Do not read` beyond what C2 says.
- Grow either example card by more than about a third.

## Acceptance criteria

- [ ] `python scripts/check.py` exits 0 - templates and examples still pass
      today's structural checks.
- [ ] The self-check below reports **no uncited claims** in either example card.
- [ ] The self-check reports no uncited claims in either template (placeholder
      lines are exempt by C1).
- [ ] Both templates state the 2,500 budget, C1, C2, the diagnosis exception,
      and the optional `## Open questions` section.

## Verify

```bash
python scripts/check.py      # expected: exit 0

# Self-check against contract C1 (T05 will build the real check into check.py):
python - map/_TEMPLATE/CARD.md profiles/legacy-modernization/scaffold/map/_TEMPLATE/CARD.md profiles/legacy-modernization/examples/*/CARD.md <<'EOF'
import re, sys
CIT = re.compile(r"`[^`\s]+:\d+(?:-\d+)?`|`schema:[^`\s]+`|\(per [^,()]+, \d{4}-\d{2}-\d{2}\)|\(unverified\)")
PH = re.compile(r"<[a-z][a-z0-9 /_-]*>")
SEP = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")
bad = 0
for f in sys.argv[1:]:
    raw = open(f, encoding="utf-8").read()
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), raw, flags=re.S)
    lines, sec = text.splitlines(), None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            sec = line[3:].strip().split()[0].lower(); continue
        if sec not in ("owns", "interfaces", "landmines"): continue
        s = line.strip()
        bullet = s.startswith(("- ", "* "))
        row = s.startswith("|") and not SEP.match(s) and not (i + 1 < len(lines) and SEP.match(lines[i + 1]))
        if not (bullet or row): continue
        if PH.search(s) or s.lstrip("-* ").strip().lower() in ("none", "n/a"): continue
        if not CIT.search(s): bad += 1; print(f"{f}:{i+1}: uncited: {s}")
print("uncited claims:", bad)
EOF
# expected: uncited claims: 0
```

## Commit

```
docs(T04): require citations on card claims
- Templates teach C1, C2, C4 and the 2,500 budget
- Legacy examples cite every claim, all forms shown
```

No `Co-Authored-By` trailer. Stage only the files listed above. Never push.

---

## Report

<!-- Worker fills this in. The header Status: line is the only status. -->

Commit: this commit on `claude/trusting-cohen-a80a36` (hash reported in chat)

**What changed**

- Both templates: C1 citation paragraph in the top comment; Confidence guidance
  says per-claim doubt is marked `(unverified)`; Owns and Landmines placeholders
  and the In-table *Entry point* placeholder show `` `<path>:<line>` ``; Do not
  read guidance states C2 and the bug/slowdown exception (WHY sentence kept);
  optional `## Open questions` section added (C4); budget 2,000 -> 2,500.
- Legacy template: how to cite `kind: repo` paths, Forms/binaries (`derived/`)
  and database logic (`schema:OBJECT`). `## Seams` untouched.
- billing-legacy: every Owns/Interfaces/Landmines claim cited (`path:N`,
  `path:N-M`, `schema:`, `per`); two Do not read reasons now say how it is known.
- orders-forms-legacy: every claim cited, Forms claims cite
  `map/orders-forms-legacy/derived/*.xml`; `(unverified)` on the night-ops row,
  tied to a new `## Open questions` entry; one Do not read reason strengthened.
- Growth: billing ~+16%, orders ~+17%.
- Required headings and header fields unchanged.

**Verify output**

- `python scripts/check.py` -> `ok   all invariants hold`, exit 0.
- Self-check over both templates and both examples -> `uncited claims: 0`.
- Extra: `check.card_gaps` on the legacy template with `['Seams']` -> no gaps.

**Deviation requests**

None.

**Found, not fixed**

- The Verify self-check only inspects the first line of a multi-line bullet, so
  citations were placed on each bullet's first line. T05 should decide whether
  continuation lines count as part of the claim.
- C2 "reason" strips *the* backticked path; two entries carry a second
  backticked path (`billing-legacy/CARD.md` fixtures entry,
  `orders-forms-legacy/CARD.md` binaries entry). T05 should strip all leading
  paths, or only the first, deliberately.
- Both templates still have bare `-` under `### Out` and `## Do not read`; the
  steps did not cover them, so no placeholder shows an Out citation or a C2 entry.

---

## Lead review

<!-- Lead only. -->

**Accepted 2026-10-04.** Cherry-picked into `main` as `70e8839`. Branch renamed from `claude/...` to
`T04-card-template-citations`.

- All three *Found, not fixed* items were contract ambiguities, ruled in
  `context/tasks/README.md` before T05 starts: a claim includes its
  continuation lines; a bare `-` is exempt; a C2 reason strips every
  backticked span and each path is reference-checked.
- Commit body has a blank line after the subject, unlike T01/T02. Fine.
