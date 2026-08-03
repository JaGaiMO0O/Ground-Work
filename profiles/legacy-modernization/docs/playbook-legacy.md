# Legacy modernization: the parts that only apply here

Read [`docs/playbook.md`](../../../docs/playbook.md) first. It carries the
reasoning that applies to any project: the tiers, the cards, the token economics,
the measurement. This document adds only what is specific to replacing or
integrating **systems you do not own**.

Everything here was written for a particular situation:

- **Several repositories**, not one.
- **Systems roughly 5-10 years old**, with unreliable or absent documentation.
- **Integration and replacement** as the work, rather than building something new.
- **Hostile terrain**: code you cannot change, cannot break, and often cannot
  build.

---

## 1. Why external code stays external

Legacy repositories stay in their own repositories, **read-only and pinned to a
ref**. They are never vendored here and never restructured. This project holds
*derived understanding* and *forward contracts* - never a copy of legacy source.

The reason is ownership. A legacy repo is terrain you do not control and should
not modify; this project is terrain you fully control, and it is where all the
leverage accumulates. Mixing them loses that distinction, and with it the
guarantee that nothing you do here can damage anything there.

`rules.py` enforces it mechanically: the build fails if a `.java`, `.fmb`, `.pkb`
or similar is ever committed outside `systems/` (gitignored) or
`map/<area>/derived/` (generated text, which is exactly what we do want).

In a project you own, that rule would be nonsense - a `.java` file is simply your
code. That is why it lives in this profile and not in the core.

## 2. Pinned refs, and why a moving branch is a lie

```yaml
areas:
  - name: billing-legacy
    kind: repo
    url: git@github.com:acme/billing-legacy.git
    ref: release/2024.3      # a tag or SHA, never a branch
    sparse: [src/main/java/com/acme/billing/**]
```

A card describes a specific commit. If the ref moves, the card silently becomes
fiction and nothing tells you. `check.py` warns on a branch-shaped ref, and warns
again when a card's surveyed ref no longer matches what `project.yaml` pins.

`sparse:` matters more here than anywhere else: only the declared paths ever land
on disk, so an agent cannot wander into the 200k lines you did not ask for.

## 3. Logic with no repository

In Oracle and mainframe shops a large share of the business logic lives inside a
database: packages, triggers, scheduled jobs. There is nothing to clone and no
branch to pin, but the logic is real and it needs a card.

```yaml
  - name: core-plsql
    kind: database
    survey: true
    adapters: { db: oracle }
    schema_owners: [BILL01, CORE]
```

For these areas the schema snapshot *is* the source, and the package signature
*is* the contract. `snapshot_db.py` extracts both.

## 4. Seams

Modernization is boundary work. Every card in this profile must carry a **Seams**
section, and the detail goes in `map/<area>/seams.md`.

A seam has a **quality**, and being honest about it is the point:

| Quality | Means |
|---|---|
| `CLEAN` | a real boundary exists - one call site, one contract, no shared state. Wrap and replace. |
| `WORKABLE` | a boundary exists but leaks: shared session, implicit ordering, a couple of undocumented callers. Needs a shim first. |
| `ENTANGLED` | logic spread across code, triggers and jobs with no single cut point. Say so, and say what would have to be untangled first. |

**An `ENTANGLED` seam recorded honestly has saved more projects than a `CLEAN` one
found early.** The failure mode of these projects is cutting the seam with the
highest business value and the worst quality first - because it is the one
everybody argues for. `seams.md` is the document that answers them, which is why
`rules.py` requires both a Quality and an Evidence column.

Execution order is **seam quality x business value**, recorded in
`integration/strangler-plan.md`. That ordering is what makes sequencing
evidence-based rather than political.

## 5. Contracts from traffic, not documentation

For systems this age the documentation lies and formal specs generally do not
exist. Observing the running system is both cheaper and more trustworthy than
reading it.

```bash
python scripts/capture.py billing-legacy record --hours 24
python scripts/capture.py billing-legacy contract
python scripts/capture.py billing-legacy fixtures
```

One capture pass yields three things:

1. **A contract grounded in observed reality**, not in aspiration.
2. **A golden-master test suite** - fixtures that let you prove behavioural
   equivalence when you replace the system.
3. **Evidence of what is actually used.** This routinely shrinks scope more than
   anything else available: an operation called zero times in a week of real
   traffic does not need reimplementing.

Raw recordings are production data. Auth headers and cookies are redacted
automatically; bodies are not, because the body is the payload you needed. They
are gitignored, and agents are blocked from reading them.

## 6. When there is no boundary to observe

Capture assumes an HTTP-ish seam. Often there is not one - Oracle Forms,
green-screen terminal applications, batch-only jobs, desktop clients on
proprietary protocols. The "interface" is a database session. `capture.py` exits
3 rather than pretending.

That is a normal situation, not a failure. Fallback order, most trustworthy first:

1. **Access or audit logs** - what was actually called, and how often. The closest
   thing to observed truth, and it still yields the scope reduction.
2. **Integration tests** - somebody already encoded the expected contract.
3. **Client code** - usually more honest about the real contract than the service
   is, because it had to work against reality.
4. **The service's own source** - last, and least trustworthy.

For database-centric systems add the audit trail, `ALL_DEPENDENCIES`, and the
grants. In an Oracle Forms application the PL/SQL package boundary *is* the
contract, whether or not anyone designed it that way.

Hold the same standard as a capture: **every operation cites its evidence**, and
operations you could not find evidence for are listed explicitly as unknown
rather than quietly omitted. A named unknown is manageable; a dropped one is a
cutover incident. Procedure: `context/recipes/no-boundary-contract.md`.

## 7. Binary sources

`.fmb`, `.rdf`, `.mdb` and compiled artifacts return nothing to grep, which is
indistinguishable from an empty area - so the agent concludes there is no logic
there and writes a card saying so. In one worked example the credit check lived in
a `WHEN-VALIDATE-ITEM` trigger inside a `.fmb`, in no `.sql` file and no document.

Convert once, into `map/<area>/derived/`, and search that:

```yaml
    derive:
      - tool: Forms2XML
        from: "forms/**/*.fmb"
        to: "derived/forms-xml/"
```

Details, tools and what to grep for once it is XML:
[`docs/stacks/oracle-forms.md`](stacks/oracle-forms.md).

## 8. Sequence of work

**Phase 0 - the security gate (half a day).** Secret scan across every repo
before an agent touches one. Access tiers declared. `project.yaml` and
`.rgignore` written. This is both the security gate and a significant cost lever,
which is why it comes first.

**Phase 1 - survey (one session per system).** One dedicated, disposable session
each. This is the largest cost of the entire project. Pay it deliberately, and
only once. Order systems by how much of the planned integration touches them, and
**resist surveying systems the integration barely touches**.

**Phase 2 - contract capture.** At the boundaries actually being cut. Produces
contracts plus golden-master fixtures.

**Phase 3 - recipes and habits.** Three to five recipes for the recurring task
shapes. Establish the handoff habit. Begin the Tier 0 feedback loop.

**Phase 4 - execution.** Ordered by seam quality x business value. The `seams.md`
files make that ordering defensible.

---

## Worked examples

Two, and the second is the one people get stuck on:

- `examples/billing-legacy/` - the straightforward case: source in git, an HTTP
  boundary you can record, a database you can read.
- `examples/orders-forms-legacy/` - Oracle Forms: binary sources, logic inside the
  form triggers, no boundary to capture, and a contract that lives in PL/SQL.

Both are deleted by `init.py`. Read them first.
