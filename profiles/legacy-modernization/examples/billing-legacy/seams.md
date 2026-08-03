# Seams: billing-legacy

## S1 - InvoiceEndpoint (SOAP)

| | |
|---|---|
| Kind | API |
| Quality | CLEAN |
| Cut cost | M |
| Business value | High - portal-web is the customer-facing path |
| Blast radius | portal-web only. No batch depends on it. |
| Evidence | 7 days of capture, 11,402 calls, 4 operations exercised of 6 declared |

**How to intercept.** Put the new service behind the same WSDL, route
`getInvoice` and `listInvoices` to it first, leave writes on the legacy path
until the golden-master suite is green.

**Do not start here if.** The tax path is in scope for the same release - S1
reads totals that S3 computes, so cutting both at once means you cannot tell
which one broke.

---

## S2 - Nightly CSV drop to crm-legacy

| | |
|---|---|
| Kind | file drop |
| Quality | CLEAN |
| Cut cost | S |
| Business value | Low on its own, but it unblocks retiring the shared mount |
| Blast radius | crm-legacy overnight load. A failure is invisible until 09:00. |
| Evidence | Format unchanged since 2019 (git log on the writer). 14 sample files under integration/fixtures/. |

**How to intercept.** Write the same CSV from the new service to the same path,
byte-identical, and diff against the legacy output for a fortnight before
switching the producer off.

**Do not start here if.** Nothing blocks this. It is the cheapest real win
available and a good first cut to build confidence.

---

## S3 - Tax calculation

| | |
|---|---|
| Kind | shared table + trigger |
| Quality | **ENTANGLED** |
| Cut cost | L |
| Business value | High, and that is the trap |
| Blast radius | Every invoice. Every downstream total. |
| Evidence | `BILL01.TRG_INV_ROUND` fires on `invoice_line` insert AND update; `PKG_TAX` is called from three schemas |

**How to intercept.** There is no clean interception point today. Untangling
sequence, if anyone insists:

1. Move rounding out of the trigger into a callable package - behaviour
   identical, location changed. Prove with the golden-master suite.
2. Only then wrap the package.
3. Only then reimplement.

**Do not start here if.** Ever, in the first two phases. This seam has the
highest business value and the worst quality, which is precisely the
combination that sinks these projects: it is the one everybody argues for and
the one that produces six months of silent total mismatches.

<!--
S3 is the reason this file exists. Ordering by business value alone puts it
first. Ordering by seam quality x business value puts S1 and S2 first, gets a
working strangler pattern and a green fixture suite in place, and reaches S3
with the tooling to prove equivalence. Write the ENTANGLED ones down honestly -
that is what makes the argument winnable.
-->
