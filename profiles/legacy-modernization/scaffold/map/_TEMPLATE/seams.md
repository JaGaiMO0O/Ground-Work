# Seams: <name>

One entry per seam listed in CARD.md. This file is what makes the strangler
ordering evidence-based rather than political - when someone argues for cutting
their favourite system first, this is the document that answers them.

Copy the block below per seam.

---

## S1 - <short name>

| | |
|---|---|
| Kind | API / file drop / DB view / queue / shared table / screen / batch |
| Quality | CLEAN, WORKABLE, or ENTANGLED |
| Cut cost | S / M / L |
| Business value | why anyone would want this one cut first |
| Blast radius | who breaks if this goes wrong |
| Evidence | traffic capture, access logs, grep hits - how you KNOW |

**How to intercept.** The concrete mechanism: wrap the endpoint, shim the file
drop, add a view, dual-write, etc.

**Do not start here if.** The conditions that make this a bad first cut.

<!--
QUALITY is the honest bit. A seam is:

  CLEAN      a real boundary already exists - one call site, one contract,
             no shared state behind it. Wrap-and-replace works.
  WORKABLE   a boundary exists but leaks - shared session, implicit ordering,
             a couple of undocumented callers. Needs a shim first.
  ENTANGLED  logic is spread across code, triggers, and jobs with no single
             cut point. Say so plainly and say what would have to be untangled
             first. An ENTANGLED seam recorded honestly has saved more projects
             than a CLEAN one found early.
-->
