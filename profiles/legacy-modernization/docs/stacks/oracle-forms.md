# Opaque and binary legacy sources

## The failure this page prevents

"Grep before read" is the cheapest habit in the playbook. It also fails
**silently** on binary sources.

```
$ rg "credit" systems/orders-forms-legacy/forms/
$
```

Zero matches. Not "this file is binary" - just nothing. An agent reasonably
concludes the system has no credit logic, writes a card saying so, and the
credit check surfaces at user-acceptance testing six weeks later.

Oracle Forms `.fmb`, Reports `.rdf`, compiled `.fmx`/`.rep`, Access `.mdb`,
Crystal `.rpt`, and SSIS `.dtsx` all behave this way. So does any logic living
in database packages rather than in a repository.

## The fix: derive once, search the derivation

This is principle 4 - *derive, don't describe* - doing real work rather than
being a slogan. Convert the binaries to text **once**, into
`map/<system>/derived/`, and point every subsequent search there.

Declare it in `project.yaml` so it is part of the system's definition rather
than something one person did once:

```yaml
derive:
  - tool: Forms2XML
    from: "forms/**/*.fmb"
    to: "derived/forms-xml/"
  - tool: rwconverter
    from: "reports/**/*.rdf"
    to: "derived/reports-xml/"
exclude_from_search:
  - "**/*.fmx"        # compiled artifact; the .fmb is the source
  - "**/*.rep"
```

And say so in the card's **Do not read** section, pointing at the derivation.
The `orders-forms-legacy` example does both.

## Conversion tools

Versions differ between shops; treat these as the starting point, not gospel.
What matters is that the conversion happens once and the output is committed.

| Source | Tool | Notes |
|---|---|---|
| `.fmb`, `.mmb`, `.pll` | `frmf2xml` | Ships with Forms 9i+. Forms 6i modules usually need opening in a newer Forms Builder first, or converting via JDAPI. |
| `.rdf` | `rwconverter` | `DTYPE=xmlfile`. Also does `.rex` if XML is unavailable. |
| any Forms module | JDAPI (Java) | The scriptable route when you have hundreds of modules and no GUI. |
| PL/SQL in the database | `DBMS_METADATA.GET_DDL` | `scripts/snapshot_db.py` already does this via the `db` adapter. |

Typical shape, run once per module:

```bash
frmf2xml.bat ORDERS.fmb OVERWRITE=YES
```

Commit the XML. It is derived text, not legacy source, so `check.py` permits it
under `**/derived/**` - that exemption exists precisely for this.

## What to search for once it is XML

The trigger code is the point. In converted Forms XML it appears as
`<Trigger TriggerName="WHEN-VALIDATE-ITEM">` elements carrying PL/SQL bodies:

```bash
rg -o 'TriggerName="[^"]+"' map/orders-forms-legacy/derived/ | sort | uniq -c | sort -rn
rg -l 'PKG_PRICING' map/orders-forms-legacy/derived/
```

That is how you find the business rules that exist in no `.sql` file and no
document.

## Logic with no repository at all

In Oracle shops a large share of the business logic is PL/SQL packages inside
the database. There is nothing to clone and no branch to pin, but the logic is
real and it needs a card.

```yaml
- name: core-plsql
  kind: database          # sync.py skips it; snapshot_db.py extracts it
  access: read-only
  survey: true
  adapters:
    db: oracle
  schema_owners: [BILL01, CORE]
```

For these systems the schema snapshot *is* the source, and the package
signature *is* the contract.

## Contracts without an observable boundary

None of these systems have HTTP traffic to record, so `capture: none` is the
honest declaration and `capture.py` will exit 3 rather than pretend.

Use `context/recipes/no-boundary-contract.md`. The evidence hierarchy there -
audit trail, `ALL_DEPENDENCIES`, callers, then source - reaches the same two
outcomes a capture pass would: a contract grounded in observation, and evidence
of what is never called. The `orders-forms-legacy` example found five dead
package procedures that way.
