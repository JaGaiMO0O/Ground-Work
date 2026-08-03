# Seams: orders-forms-legacy

## S1 - ORD01.PKG_ORDER_API

| | |
|---|---|
| Kind | PL/SQL package (the de facto service layer) |
| Quality | WORKABLE |
| Cut cost | M |
| Business value | High - every order passes through it |
| Blast radius | All order entry. Branches cannot take orders if this breaks. |
| Evidence | `ALL_DEPENDENCIES` shows 11 callers; DB audit shows 6 procedures called in the last 90 days, 5 never |

**How to intercept.** A package boundary is interceptable even without an HTTP
seam: create a wrapper package with the same signature, have the Forms client
call the wrapper, and route procedure by procedure. The 5 never-called
procedures do not need reimplementing at all - that is the scope reduction the
capture pass would have given you, obtained from the audit trail instead.

**Do not start here if.** The `derive:` step has not been run. You cannot see
what the Forms triggers call until the .fmb files are XML, and the credit check
in `WHEN-VALIDATE-ITEM` calls this package in a way no .sql file records.

---

## S2 - ORD_PICK.rdf and the other Reports

| | |
|---|---|
| Kind | read-only report |
| Quality | CLEAN |
| Cut cost | S |
| Business value | Medium - branch staff use it daily and complain about it |
| Blast radius | Printing only. A failure is visible and non-destructive. |
| Evidence | Reports are SELECT-only; verified in the converted XML |

**How to intercept.** Nothing to intercept. Reports read the schema and emit
paper. Reimplement against the same schema and diff the output. This is the
best possible first cut: real user-visible value, no write path, and a trivially
provable equivalence test.

**Do not start here if.** Nothing blocks it. Start here.

---

## S3 - The Forms UI

| | |
|---|---|
| Kind | screen |
| Quality | **ENTANGLED** |
| Cut cost | L |
| Business value | High - it is what users see |
| Blast radius | Every branch, every order |
| Evidence | Credit-check logic found in `WHEN-VALIDATE-ITEM` inside `ORDERS.fmb`; commit-on-navigation confirmed in the converted XML |

**How to intercept.** Not directly. The screen and the business rules are the
same artifact - that is what makes it entangled. The sequence:

1. Run the derive step and read the trigger code.
2. Move each rule found there into `PKG_ORDER_API`, unchanged in behaviour.
   The Forms screen keeps working; it now calls out instead of computing.
3. Once the screen is a thin client over S1, replacing the UI is a UI project
   rather than a business-logic archaeology project.

**Do not start here if.** Always. Rewriting the screens first means
reimplementing rules you have not read yet, from binaries you cannot grep, and
discovering the credit check at user-acceptance testing.

<!--
Note what the evidence column does here. There is no traffic capture on this
system - no HTTP boundary exists - so every claim is sourced from the database
instead: ALL_DEPENDENCIES, the audit trail, and the converted XML. That is the
no-boundary fallback working as intended, and it produced a scope reduction (5
dead procedures) just as a capture pass would have.
-->
