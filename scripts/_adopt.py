"""Adopting a project that already exists.

Most projects that need this were started before anyone thought about it. So the
scaffold has to arrive in a repo full of code, without breaking anything and
without pretending to know things it does not.

Four rules:

  1. NEVER clobber. A file that already exists is left alone; our version lands
     beside it as `<name>.proposed` and the user is told. Nothing about adoption
     is worth losing somebody's README over.
  2. Detect, do not invent. Commands come from real manifests. Areas come from
     directories that actually exist, ranked by real churn. Anything unknown is
     left blank with a comment, because a plausible wrong answer in RUNBOOK.md is
     worse than an obvious gap.
  3. Refuse on a dirty tree unless forced, so `git diff` afterwards shows exactly
     what adoption did and nothing else.
  4. Carry TEMPLATES, never content. Anything this repo filled in about itself -
     its status, its handoffs, its decisions - stays here. Rule 2 forbids
     inventing a wrong answer; shipping a confident answer about a different
     project is the same failure with better grammar, and it lands in the tier an
     agent reads first.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Never copied into the target, and never proposed as an area.
NOISE = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", "out", "target", "bin", "obj", ".idea",
    ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next",
    ".nuxt", "coverage", "htmlcov", ".tox", ".gradle", "vendor",
    "systems", ".invariant-work", ".DS_Store",
}

# Files we bring in, but which must never overwrite an existing one. An existing
# AGENTS.md is somebody's work; ours lands beside it to be merged by hand.
NEVER_CLOBBER = {"AGENTS.md", "CLAUDE.md"}

# Written per-project by init.adopt(), never copied verbatim - so they must NOT
# appear in the copy plan or they get handled twice. STATUS.md is rendered from
# STATUS.template.md; this repo's own STATUS.md describes this repo.
GENERATED_HERE = {"project.yaml", "RUNBOOK.md", "STATUS.md", "STATUS.template.md"}

# The target has its own README. Ours describes the template, so it would be
# noise - adoption explains itself through START-HERE.md instead.
NOT_ADOPTED = {"README.md"}

# Parts of the template a project will never invoke. See ADR 0003: the scaffold
# is copied rather than installed, which is only defensible if it copies what
# gets used. Everything named here stays in the template.
#
#   tests/            test the scaffold, not the adopted project
#   init, _adopt      adoption has already happened by the time these arrive
#   .sh / .ps1        aliases for the .py files. No document that travels names
#                     them - the runbook adoption writes uses `python x.py`.
#
# scripts/adapters/** deliberately DOES travel, including the worked oracle and
# postgres ones. They are three files, docs/adapters.md leans on them as the
# examples you copy, and a doc that describes files which are not there is worse
# than three unused files that are.
SKIP_ON_ADOPT_DIRS = {"tests"}
SKIP_ON_ADOPT_FILES = {"scripts/init.py", "scripts/_adopt.py"}
SHIM_SUFFIXES = {".sh", ".ps1"}

# Directories where every file is something THIS project recorded about itself.
# Only the templates in them travel - a name starting with `_`, which is the
# convention everywhere else in the repo (map/_TEMPLATE, context/recipes).
#
# This is rule 4, and it was a real regression rather than a hypothetical: an
# adoption carried three dated handoffs and ADRs 0001-0003 into somebody else's
# repository, where AGENTS.md routes to "the newest handoff" for what happened
# last session. The first thing an agent read there described Ground Work.
SELF_DESCRIBING_DIRS = {"context/handoffs", "docs/decisions"}


def travels(rel: Path) -> bool:
    """Is this template file worth carrying into an adopted project?"""
    parts = rel.parts
    if parts[0] in SKIP_ON_ADOPT_DIRS:
        return False
    if rel.as_posix() in SKIP_ON_ADOPT_FILES:
        return False
    if len(parts) == 2 and parts[0] == "scripts" and rel.suffix in SHIM_SUFFIXES:
        return False
    parent = rel.parent.as_posix()
    if parent in SELF_DESCRIBING_DIRS and not rel.name.startswith("_"):
        return False
    return True


CODE_SUFFIXES = {
    ".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".java",
    ".kt", ".go", ".rs", ".rb", ".php", ".cs", ".c", ".h", ".cpp", ".hpp",
    ".swift", ".scala", ".ex", ".sql", ".sh", ".ps1", ".m", ".dart",
}


@dataclass
class Detected:
    stack: dict = field(default_factory=dict)
    commands: dict = field(default_factory=dict)
    sources: "list[str]" = field(default_factory=list)


# ---------------------------------------------------------------------------
# detection
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect(target: Path) -> Detected:
    found = Detected()

    pkg = target / "package.json"
    if pkg.is_file():
        found.stack["language"] = "javascript/typescript"
        found.sources.append("package.json")
        try:
            data = json.loads(_read(pkg) or "{}")
            scripts = data.get("scripts") or {}
            runner = "npm run "
            if (target / "pnpm-lock.yaml").is_file():
                runner = "pnpm "
            elif (target / "yarn.lock").is_file():
                runner = "yarn "
            found.commands["install"] = (
                "pnpm install" if runner == "pnpm " else
                "yarn install" if runner == "yarn " else "npm ci"
            )
            for ours, theirs in (
                ("test", "test"), ("build", "build"), ("lint", "lint"),
                ("run", "dev"),
            ):
                if theirs in scripts:
                    found.commands[ours] = f"{runner}{theirs}".replace(
                        "npm run test", "npm test"
                    )
            if (target / "tsconfig.json").is_file():
                found.stack["typed"] = "typescript"
        except json.JSONDecodeError:
            pass

    pyproject = target / "pyproject.toml"
    if pyproject.is_file():
        found.stack["language"] = "python"
        found.sources.append("pyproject.toml")
        text = _read(pyproject)
        found.commands.setdefault("install", "pip install -e .")
        if "pytest" in text:
            found.commands.setdefault("test", "pytest")
        if "ruff" in text:
            found.commands.setdefault("lint", "ruff check .")
        elif "flake8" in text:
            found.commands.setdefault("lint", "flake8")
        if "poetry" in text:
            found.commands["install"] = "poetry install"
    elif (target / "requirements.txt").is_file():
        found.stack["language"] = "python"
        found.sources.append("requirements.txt")
        found.commands.setdefault("install", "pip install -r requirements.txt")
        if (target / "pytest.ini").is_file() or (target / "tests").is_dir():
            found.commands.setdefault("test", "pytest")

    makefile = next((p for p in (target / "Makefile", target / "makefile")
                     if p.is_file()), None)
    if makefile:
        found.sources.append(makefile.name)
        targets = set(re.findall(r"^([a-zA-Z][\w-]*):", _read(makefile), re.M))
        for name in ("install", "test", "build", "lint", "run"):
            if name in targets:
                found.commands.setdefault(name, f"make {name}")

    if (target / "pom.xml").is_file():
        found.stack["language"] = "java"
        found.stack["build"] = "maven"
        found.sources.append("pom.xml")
        found.commands.setdefault("test", "mvn test")
        found.commands.setdefault("build", "mvn -DskipTests package")
    elif list(target.glob("build.gradle*")):
        found.stack["language"] = "java/kotlin"
        found.stack["build"] = "gradle"
        found.sources.append("build.gradle")
        found.commands.setdefault("test", "gradle test")
        found.commands.setdefault("build", "gradle build")

    if (target / "Cargo.toml").is_file():
        found.stack["language"] = "rust"
        found.sources.append("Cargo.toml")
        found.commands.setdefault("test", "cargo test")
        found.commands.setdefault("build", "cargo build --release")

    if (target / "go.mod").is_file():
        found.stack["language"] = "go"
        found.sources.append("go.mod")
        found.commands.setdefault("test", "go test ./...")
        found.commands.setdefault("build", "go build ./...")

    if list(target.glob("*.csproj")) or list(target.glob("*.sln")):
        found.stack["language"] = "c#"
        found.sources.append("csproj/sln")
        found.commands.setdefault("test", "dotnet test")
        found.commands.setdefault("build", "dotnet build")

    if (target / "Dockerfile").is_file():
        found.stack["container"] = "docker"

    return found


def churn(target: Path) -> dict:
    """Commits touching each top-level directory. Best-effort."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "-n", "400"],
            cwd=str(target), capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0:
        return {}
    counts: dict = {}
    for line in result.stdout.splitlines():
        line = line.strip().replace("\\", "/")
        if not line or "/" not in line:
            continue
        head = line.split("/", 1)[0]
        counts[head] = counts.get(head, 0) + 1
    return counts


def propose_areas(target: Path, limit: int = 6) -> "list[tuple[str, str, int]]":
    """-> [(name, glob, file_count)] for the directories that look like code."""
    weights = churn(target)
    rows = []
    for entry in sorted(target.iterdir()):
        if not entry.is_dir() or entry.name in NOISE or entry.name.startswith("."):
            continue
        files = [
            p for p in entry.rglob("*")
            if p.is_file()
            and p.suffix.lower() in CODE_SUFFIXES
            and not any(part in NOISE for part in p.parts)
        ]
        if not files:
            continue
        rows.append((entry.name, f"{entry.name}/**", len(files),
                     weights.get(entry.name, 0)))
    # One file is enough. This used to require two, which silently dropped
    # single-file serving layers - an `app/app.py` that every session reads is
    # exactly the area that most needs a card. Nothing is lost by including
    # them: the sort below is churn-first, so a one-file directory only takes a
    # slot when there are fewer than `limit` better candidates.
    # Churn first - the directories people actually change are the ones worth a
    # card - then size as a tiebreak.
    rows.sort(key=lambda r: (r[3], r[2]), reverse=True)
    return [(n, g, c) for n, g, c, _ in rows[:limit]]


# ---------------------------------------------------------------------------
# writing
# ---------------------------------------------------------------------------


def destination_for(target: Path, rel: Path, profile: str,
                    keep_profiles: bool) -> "Path | None":
    """Where a template file lands in the target, or None if it does not travel.

    Everything is a straight copy except `profiles/`, which needs the same two
    moves plain `init.py` makes, and used not to get them:

      * only the chosen profile travels. A project uses one. Carrying the rest
        was 15 files of a 95-file adoption that nothing would ever load.
      * a profile's `scaffold/` is an overlay, not a directory to keep. It is
        copied to the project root and the source is dropped - otherwise the
        profile's own templates arrive somewhere no rule looks for them.
    """
    parts = rel.parts
    if parts[0] != "profiles" or len(parts) == 1:
        return target / rel
    if len(parts) == 2:
        return target / rel  # profiles/README.md - explains the mechanism
    if parts[1] != profile:
        return (target / rel) if keep_profiles else None
    if parts[2] == "scaffold":
        return target / Path(*parts[3:]) if len(parts) > 3 else None
    return target / rel


def scaffold_plan(template: Path, target: Path, profile: str = "general",
                  keep_profiles: bool = False) -> "list[tuple[Path, Path, str]]":
    """-> [(source, destination, action)] where action is add|proposed|skip."""
    # The template's shape. What of it actually travels is `travels()` below -
    # this list says where to look, not what to take.
    include = [
        "AGENTS.md", "CLAUDE.md", "START-HERE.md",
        "docs", "context", "map", "interfaces", "scripts", "profiles", "tests",
        ".claude", ".env.example",
    ]
    # Keyed by destination, so a scaffold file that overlays a core one appears
    # once rather than twice. `profiles` comes after `map` and `context` in the
    # include list, so the scaffold version is the one that survives - the same
    # precedence plain init.py gets by applying the scaffold last.
    plan: "dict[Path, tuple[Path, Path, str]]" = {}
    for name in include:
        if name in GENERATED_HERE or name in NOT_ADOPTED:
            continue
        source = template / name
        if not source.exists():
            continue
        sources = [source] if source.is_file() else [
            p for p in source.rglob("*") if p.is_file()
        ]
        for item in sources:
            rel = item.relative_to(template)
            if any(part in NOISE for part in rel.parts):
                continue
            if "examples" in rel.parts:
                continue
            if not travels(rel):
                continue
            destination = destination_for(target, rel, profile, keep_profiles)
            if destination is None:
                continue
            if destination.exists():
                action = "proposed" if destination.name in NEVER_CLOBBER else "skip"
            else:
                action = "add"
            plan[destination] = (item, destination, action)
    return list(plan.values())


def final_path(destination: Path, action: str) -> Path:
    """Where a planned file actually lands. Callers that need to edit a copied
    file afterwards - init.py personalizing AGENTS.md - have to agree with
    apply_plan about this, so there is one function that decides it."""
    return (
        destination.with_suffix(destination.suffix + ".proposed")
        if action == "proposed" else destination
    )


def apply_plan(plan, dry_run: bool) -> dict:
    counts = {"add": 0, "proposed": 0, "skip": 0}
    for source, destination, action in plan:
        counts[action] += 1
        if dry_run or action == "skip":
            continue
        final = final_path(destination, action)
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, final)
    return counts


def project_yaml(name: str, profile: str, found: Detected, areas) -> str:
    lines = [
        "# project.yaml - what this project is made of.",
        "#",
        "# Seeded by `init.py --adopt` from what is actually in the repository.",
        "# Everything here is a starting point: correct the areas, and set",
        "# `survey: true` on one when you are ready to write its card.",
        "",
        f"project: {name}",
        f"profile: {profile}",
        "",
    ]
    if found.commands:
        lines.append("# Detected from " + ", ".join(found.sources or ["the repo"])
                     + ". Verify these actually work.")
        lines.append("commands:")
        for key in ("install", "test", "lint", "build", "run"):
            if key in found.commands:
                lines.append(f"  {key}: {found.commands[key]}")
    else:
        lines += [
            "# Nothing detected - no recognised manifest. Fill these in; check.py",
            "# verifies RUNBOOK.md documents whatever you declare.",
            "commands:",
            "  # test: ",
        ]
    lines += ["", "defaults:", "  access: read-only", "  survey: false", ""]

    if areas:
        lines.append("# Proposed from directory contents and git churn, busiest")
        lines.append("# first. Rename, merge or delete freely - these are a guess.")
        lines.append("areas:")
        for area_name, glob, count in areas:
            lines.append(f"  - name: {area_name}")
            lines.append("    kind: local")
            lines.append("    paths:")
            lines.append(f"      - {glob}")
            lines.append(f"    # {count} source file(s)")
            lines.append("    survey: false")
            lines.append("")
    else:
        lines += [
            "# No obvious source directories found. Declare areas yourself:",
            "areas: []",
            "",
        ]
    return "\n".join(lines)


def runbook(name: str, found: Detected) -> str:
    lines = [
        "# Runbook",
        "",
        "**The one place that says how to build, test and run this project.**",
        "",
        "Seeded by `init.py --adopt`. Every command declared in `project.yaml`",
        "must appear here - `check.py` fails if one is missing, which is what",
        "stops this file drifting into fiction.",
        "",
    ]
    if found.stack:
        lines += ["## Stack", "",
                  *[f"- {k}: {v}" for k, v in found.stack.items()], ""]
    order = [
        ("install", "Setup", "What is needed before anything works. Add versions - "
                             "\"Node 20.11\", not \"recent Node\"."),
        ("test", "Test", "How long it takes, and what a normal failure looks like."),
        ("run", "Run", "Where it listens, and how to tell it started correctly."),
        ("build", "Build", ""),
        ("lint", "Lint", ""),
    ]
    for key, heading, note in order:
        command = found.commands.get(key)
        lines += [f"## {heading}", "", "```bash",
                  command if command else f"# TODO: how do you {key} this?", "```", ""]
        if note:
            lines += [note, ""]
        if command:
            lines += ["<!-- DETECTED, NOT VERIFIED: this came from a manifest and "
                      "has not been run. Confirm it, then delete this note. -->", ""]

    lines += [
        "## Reproducing a result",
        "",
        "Enough for somebody else to get the same output you got:",
        "",
        "- **Pinned versions.** Which lockfile is authoritative, and how to",
        "  install from it exactly rather than approximately.",
        "- **Inputs.** Where data or fixtures come from, and which version.",
        "- **Randomness.** Seeds, and anything else that varies between runs.",
        "- **Environment.** Variables that change behaviour, and safe defaults.",
        "  Never the secret values - those live in `.env`, which is gitignored.",
        "",
        "If a result cannot be reproduced from this section alone, it is not",
        "reproducible, and saying so here is more useful than implying otherwise.",
        "",
        "## Known rough edges",
        "",
        "The things that waste an hour if nobody warns you: the test that fails on",
        "a clean checkout, the build that needs running twice, the port already in",
        "use.",
        "",
    ]
    return "\n".join(lines)
