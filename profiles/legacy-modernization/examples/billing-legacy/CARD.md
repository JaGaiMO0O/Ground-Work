# System Card: billing-legacy
Repo: acme/billing-legacy @ release/2024.3  |  Surveyed: 2026-07-27
Confidence: HIGH on inbound API - MED on batch jobs - LOW on cron scripts

Stack: Java 8, Spring 3.2, Oracle 11g, on-prem WebLogic
Health: ~9 yrs old. No tests on the invoice path. Builds via scripts/build-legacy.sh
        on a Jenkins agent nobody has patched since 2022.

## Owns (authoritative data - nothing else may write these)

- `invoice`, `invoice_line`, `tax_adjustment`
- `customer.billing_address` - **only this column**. The customer identity
  itself is owned by crm-legacy, and crm-legacy must never write the address.
  This split is the single most likely source of a double-write bug here.

## Interfaces

### In

| Caller | Mechanism | Entry point | Notes |
|--------|-----------|-------------|-------|
| portal-web | SOAP `/InvoiceService` | `src/main/java/com/acme/billing/invoice/InvoiceEndpoint.java` | 4 operations, **2 never called** in 7 days of capture |
| finance-batch | JMS queue `BILL.IN` | `.../InboundListener.java` | nightly, ~4k messages |
| ops team | direct SQL against BILL01 | - | UNDOCUMENTED. Found in `v$sql`, not in any doc. Confirmed with the DBA. |

### Out

- crm-legacy: nightly CSV drop to `/mnt/exch/crm/*.csv` at 02:15 Europe/Amsterdam
- Oracle `BILL01` -> `map/billing-legacy/schema.sql`
- SMTP relay for invoice PDFs (fire-and-forget; failures are logged, not retried)

## Seams

S1  `InvoiceEndpoint` - CLEAN. One call site, one contract. Wrap-and-replace.
S2  nightly CSV drop - CLEAN. Trivial to shim; the format is stable since 2019.
S3  tax calculation - ENTANGLED with DB triggers. **Do NOT start here.**

## Landmines

- **Rounding happens in a database trigger, not in code.** Amounts are
  `NUMBER(12,0)` cents and `BILL01.TRG_INV_ROUND` adjusts the last line to make
  the total reconcile. A faithful Java reimplementation of the *code* produces
  different totals on 3 of the 40 golden-master fixtures.
- **Timezone-naive `DATE` columns.** The batch assumes server local time is
  Europe/Amsterdam. It has produced duplicate invoice numbers on the October
  DST boundary twice, in 2021 and 2023.
- `invoice.status = 'X'` means **voided**, not cancelled. `'C'` is closed.
  Getting these the wrong way round silently un-voids invoices.
- `invoice_line.qty` is nullable and NULL means 1, not 0.

## Do not read unless specifically needed

- `src/legacy/report/**` - 12k lines, dead since 2019. Evidence: zero hits
  across 12 months of WebLogic access logs, confirmed against the load balancer.
- `src/main/generated/**` - JAXB stubs, regenerated at build time.
- `src/test/resources/fixtures/**` - 40MB of XML, superseded by
  `integration/fixtures/billing-legacy/`.

<!--
WHY THIS CARD IS SHAPED LIKE THIS - read once, then delete this block.

* Every claim that could be wrong cites evidence. "2 never called" is backed by
  a capture window; "dead since 2019" is backed by access logs. Compare with
  "looks unused", which belongs in the Confidence line instead.

* The Confidence line is honest about the cron scripts. That LOW is not a
  failure - it tells the next reader exactly where to verify before trusting,
  which is the whole mechanism for keeping cards cheap to maintain.

* The Owns section calls out a single shared column. That is the kind of detail
  that costs an afternoon to find now and a production incident to find later.

* The Landmines are all things you cannot learn from reading the Java. Two of
  them live in the database. This is why "read the service" is the expensive
  and unreliable path.
-->
