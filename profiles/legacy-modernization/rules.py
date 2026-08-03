"""Validation rules for the legacy-modernization profile.

check.py loads this when project.yaml says `profile: legacy-modernization`.
Two hooks:

    EXTRA_CARD_SECTIONS   sections this profile requires on every area card
    register(ctx)         everything else

`ctx` carries `.project`, `.root`, and `.error/.warn/.note`, plus `.read/.rel`
helpers. Core rules have already run; anything added here is additive.
"""

from __future__ import annotations

from pathlib import Path

# Modernization is boundary work. A card without seams cannot inform what to
# cut first, which is the decision this whole profile exists to support.
EXTRA_CARD_SECTIONS = ["Seams"]

GROUP = "legacy"

# Extensions that mean "source belonging to a system we do not own". In a
# general project a .java file is simply your code; here, a copy of legacy
# source inside the control repo breaks the structural rule the profile rests
# on - legacy stays in its own repo, read-only and pinned.
FOREIGN_SOURCE_EXT = {
    ".java", ".jsp", ".jspx", ".class", ".jar", ".war", ".ear",
    ".rb", ".erb", ".php", ".asp", ".aspx", ".cs", ".vb",
    ".cbl", ".cob", ".cpy", ".jcl",
    ".fmb", ".fmx", ".pll", ".plx", ".rdf", ".rep", ".mmb", ".mmx",
    ".pks", ".pkb", ".prc", ".fnc", ".trg",
    ".pas", ".dpr", ".dfm",
}
# systems/ is gitignored; examples/ is illustrative; **/derived/** is generated
# text, which is exactly what we DO want committed.
EXEMPT_PREFIXES = ("systems/", "examples/", "profiles/")
EXEMPT_PART = "/derived/"


def _check_foreign_source(ctx) -> None:
    import _lib as lib

    if not lib.is_git_repo() or not lib.has_commits():
        return
    leaked = [
        f
        for f in lib.tracked_files()
        if Path(f).suffix.lower() in FOREIGN_SOURCE_EXT
        and not f.startswith(EXEMPT_PREFIXES)
        and EXEMPT_PART not in f"/{f}"
    ]
    if leaked:
        shown = ", ".join(leaked[:3]) + (" ..." if len(leaked) > 3 else "")
        ctx.error(
            GROUP,
            f"{len(leaked)} legacy source file(s) committed to this repo: {shown}",
            "This repo holds derived understanding only. Keep source in systems/ "
            "(gitignored) or convert it into map/<area>/derived/.",
        )


def _check_seams(ctx) -> None:
    for area in ctx.project.areas:
        if not area.survey:
            continue
        card = area.card
        if not card.exists():
            continue  # core already reported the missing card
        seams = area.card_dir / "seams.md"
        if not seams.exists():
            ctx.warn(
                GROUP,
                f"{area.name}: no seams.md",
                "Seams are the input to sequencing. A card without them cannot "
                "inform what to cut first.",
            )
            continue
        text = ctx.read(seams)
        if "Quality" not in text:
            ctx.warn(
                GROUP,
                f"{ctx.rel(seams)}: no seam Quality recorded",
                "CLEAN / WORKABLE / ENTANGLED is what makes the ordering "
                "evidence-based rather than political.",
            )
        if "Evidence" not in text:
            ctx.warn(
                GROUP,
                f"{ctx.rel(seams)}: no Evidence column",
                "A seam nobody can trace to observed behaviour is a guess.",
            )


def _check_strangler_plan(ctx) -> None:
    plan = ctx.root / "integration" / "strangler-plan.md"
    if not plan.exists():
        ctx.warn(
            GROUP,
            "integration/strangler-plan.md is missing",
            "It is where seam ordering gets decided. Without it the order is "
            "decided in meetings instead.",
        )
        return
    text = ctx.read(plan)
    surveyed = [a.name for a in ctx.project.areas if a.survey and a.card.exists()]
    unplanned = [n for n in surveyed if n not in text]
    if unplanned:
        ctx.note(
            "surveyed but absent from the strangler plan: " + ", ".join(unplanned)
        )


def _check_contracts(ctx) -> None:
    """A capture-capable area with no contract has an unfinished Phase 2."""
    import _lib as lib

    contracts = ctx.root / "integration" / "contracts"
    for area in ctx.project.areas:
        name, path = lib.resolve_adapter(area, "capture")
        if name is None or path is None:
            continue
        existing = list(contracts.glob(f"{area.name}*")) if contracts.exists() else []
        if not existing:
            ctx.note(
                f"{area.name} declares a capture adapter but has no contract in "
                f"integration/contracts/ yet"
            )


def register(ctx) -> None:
    _check_foreign_source(ctx)
    _check_seams(ctx)
    _check_strangler_plan(ctx)
    _check_contracts(ctx)
