# Strangler plan

Ordered by **seam quality x business value**. Not by politics, not by which
team is loudest, and not by which system is most annoying to work in.

Every row must point at a seam that exists in a `seams.md` file. If there is no
seam entry behind a row, the row is a wish rather than a plan - and the fix is
to go survey the seam, not to write the row more confidently.

| # | Seam | System | Quality | Cut cost | Business value | Status | Depends on |
|---|------|--------|---------|----------|----------------|--------|------------|
| 1 |      |        |         |          |                | not started | |

## Sequencing notes

<!-- Why this order and not another. Write down the constraint that forced an
awkward ordering, or the next person will "fix" it. -->

## Explicitly not doing yet

| Seam | Why not, and what would change that |
|------|-------------------------------------|
|      |                                     |

<!--
Status: not started -> shimmed -> dual-running -> cut over -> legacy retired

"Dual-running" is where these projects stall, because it is the point at which
the old system still works and the pressure comes off. Record the date a seam
entered dual-running. If a row has been sitting there for months, that is the
finding, and it belongs in front of whoever is funding the work.

Cutting an ENTANGLED seam first is the commonest way one of these projects
fails. If a row here has Quality: ENTANGLED and a low number, say out loud why.
-->
