# System Card: orders-forms-legacy
Repo: acme/orders-forms @ v6.2.1  |  Surveyed: 2026-07-27
Confidence: MED on screen inventory - MED on DB packages - LOW on what users actually use

Stack: Oracle Forms 6i, Reports 6i, Oracle 11g. Client/server, no web tier.
Health: ~14 yrs. Sources are BINARY. No build pipeline - .fmx files are compiled
        by hand on a Windows box in the ops cupboard. One person knows how.

## Owns (authoritative data - nothing else may write these)

- `sales_order`, `sales_order_line` - `schema:ORD01.SALES_ORDER`
- `order_status_history` - `schema:ORD01.ORDER_STATUS_HISTORY`
- **Not** pricing - `map/orders-forms-legacy/derived/ORDERS.xml:2214-2236`. Prices are read from
  `BILL01.PKG_PRICING` at order entry and copied onto the line. The copy is authoritative once written, which means a
  price correction in billing does NOT propagate. That is by design, and every
  reimplementation gets it wrong the first time.

## Interfaces

### In

| Caller | Mechanism | Entry point | Notes |
|--------|-----------|-------------|-------|
| ~40 branch users | Forms runtime over SQL*Net | `map/orders-forms-legacy/derived/ORDERS.xml:1` | **No HTTP. Nothing to record.** (per Henk, 2026-07-24) |
| night ops | SQL*Plus scripts | `scripts/eod/*.sql` | Undocumented; found on the fileshare, not in the repo. Who runs them is (unverified) |
| pick lists | Reports 6i | `map/orders-forms-legacy/derived/ORD_PICK.xml:15` | prints directly to branch printers |

### Out

- Writes directly into the `ORD01` schema. There is no service layer - `map/orders-forms-legacy/derived/ORDERS.xml:880-912`
- Calls `BILL01.PKG_PRICING.GET_PRICE` - a **cross-schema grant**, not an API - `schema:BILL01.PKG_PRICING`.
  Nothing versions this and nothing tests it.
- Spools nightly totals to `/mnt/exch/fin/ord_totals_YYYYMMDD.txt` (per Henk, 2026-07-24)

## Seams

S1  `ORD01.PKG_ORDER_API` - WORKABLE. The PL/SQL package boundary is the real
    contract, whether or not anyone designed it as one.
S2  `ORD_PICK.rdf` - CLEAN. Reports are read-only; reimplement independently.
S3  the Forms UI itself - ENTANGLED. Business logic lives inside the binaries.

## Landmines

- **Business logic lives in trigger code INSIDE the .fmb binaries** - `map/orders-forms-legacy/derived/ORDERS.xml:1412-1468`.
  `WHEN-VALIDATE-ITEM` on the quantity field enforces the credit check. It is
  not in any .sql file, and it is not in any document. Converting the .fmb to
  XML is the only way to read it - see "Do not read" below.
- **Forms 6i commits on navigation** - `map/orders-forms-legacy/derived/ORDERS.xml:96`. Moving between blocks issues a commit.
  There is no transaction spanning the order header and its lines, so a
  half-entered order is a real, persisted state that downstream code must
  tolerate.
- **No optimistic locking** (per Henk, 2026-07-24). Two branches editing the same order silently
  last-write-wins. Users have adapted by phoning each other. A new system that
  adds proper locking will be reported as broken.
- Order numbers come from `ORD_SEQ`, but branch 07 has a *different* sequence - `schema:ORD01.ORD_SEQ_B07`.
  It dates from a 2018 migration. Uniqueness is by (branch, number), not number.

## Do not read unless specifically needed

- `forms/**/*.fmb`, `reports/**/*.rdf` - **BINARY**. `rg` returns zero matches
  and an agent will conclude the system is empty. Read
  `map/orders-forms-legacy/derived/` instead, which is the XML produced
  by the `derive:` step in project.yaml.
- `**/*.fmx`, `**/*.rep` - compiled output, rebuilt by hand from the .fmb and
  .rdf sources; nothing in them is not also in the source.
- `forms/attic/**` - 6 screens disabled in the 2018 branch merge. Evidence:
  no menu entry references them, confirmed against `ORD01.MENU_ITEMS`.

## Open questions

- Who runs `scripts/eod/*.sql` each night, from which machine, and does the
  finance spool depend on them finishing first? Bears on the night ops row.

<!--
WHY THIS ONE IS DIFFERENT - read once, then delete this block.

This is the case the playbook's traffic-capture path does not cover, and it is
extremely common in Oracle shops.

* THERE IS NO BOUNDARY TO RECORD. No HTTP, no queue, no API. `capture: none` in
  project.yaml is the honest declaration, and context/recipes/
  no-boundary-contract.md is the route to a contract instead.

* THE SOURCES ARE BINARY. "Grep before read" silently fails: the grep returns
  nothing, and nothing looks exactly like an empty system. The derive: block in
  project.yaml converts .fmb -> XML once, into map/<sys>/derived/,
  and that is what gets searched. See profiles/legacy-modernization/docs/stacks/oracle-forms.md.

* THE REAL CONTRACT IS IN THE DATABASE. For a Forms application the PL/SQL
  package boundary is the interface, and schema.sql plus the package source are
  worth more than the screens. S1 reflects that.

* THE LOW CONFIDENCE IS ON USAGE, NOT STRUCTURE. We know what the screens are;
  we do not know which ones anyone opens. That is answerable from the DB audit
  trail, and until someone answers it the marker stays LOW.
-->
