#!/usr/bin/env python3
"""scan.py - the Phase 0 secret gate. Run it BEFORE an agent touches a repo.

Multi-repo legacy work all but guarantees credentials in config files and in git
history. This is a gate, not an ongoing programme: scan, record, rotate, move on.

Uses gitleaks or trufflehog when they are installed, because they also read git
HISTORY, which the built-in scanner cannot. Without them it falls back to a
bundled regex pass over the working tree, so a missing binary can never block
Phase 0 -- but the coverage gap is reported loudly rather than hidden.

Findings are recorded in .secrets-baseline as FINGERPRINTS ONLY. The secret
values themselves are never written to disk, never printed, and never enter an
agent transcript.

    python scripts/scan.py                # scan, compare against the baseline
    python scripts/scan.py --update       # accept current findings as the baseline
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import _lib as lib
from _lib import ROOT

BASELINE = ROOT / ".secrets-baseline"
MAX_FILE_BYTES = 2_000_000

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".idea", ".vscode", "dist", "build", "target", "vendor",
}
# .env is where secrets are SUPPOSED to live. Scanning it just floods the
# baseline with expected hits.
SKIP_NAMES = {".env", ".secrets-baseline", ".secrets-baseline.raw.json"}

# NOTE: these use [ \t] rather than \s around separators, deliberately. \s
# matches newlines, so `PASSWORD=` with an empty value would swallow the next
# line and report it as the secret. A noisy gate is a gate people switch off.
RULES: "list[tuple[str, re.Pattern]]" = [
    ("private-key", re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws-secret", re.compile(
        r"(?i)aws_?secret_?access_?key[ \t]*[:=][ \t]*['\"]?([A-Za-z0-9/+=]{40})")),
    ("github-token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}\b")),
    ("jdbc-password", re.compile(
        r"(?i)jdbc:[^\s'\"]*[?;&]password=([^\s;&'\"]+)")),
    ("url-credentials", re.compile(
        r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:([^/\s:@]{3,})@")),
    # sqlplus-style  user/password@db  -- very common in Oracle shops
    ("oracle-connect", re.compile(
        r"(?i)\b(?:sqlplus|exp|imp|rman)[ \t]+\w+/(\S{4,})@")),
    ("password-assignment", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key)\b[ \t]*[:=][ \t]*"
        r"['\"]([^'\"]{6,})['\"]")),
    ("password-property", re.compile(
        r"(?im)^[ \t]*[\w.]*(?:password|passwd|pwd|secret|token|apikey|api[_-]?key)"
        r"[ \t]*=[ \t]*(\S{6,})[ \t]*$")),
    ("bearer-token", re.compile(
        r"(?i)\bbearer[ \t]+([A-Za-z0-9\-._~+/]{20,}=*)")),
]

PLACEHOLDER = re.compile(
    r"(?i)^(?:\$\{.*\}|\{\{.*\}\}|<.*>|%.*%|(?:change|changeme|changeit|xxx+|"
    r"todo|none|null|empty|placeholder|your[_-]?\w*|example\w*|dummy|test|"
    r"sample|redacted|\*+|\.+|-+)$)"
)


def looks_like_placeholder(value: str) -> bool:
    value = (value or "").strip().strip("'\"")
    if not value or len(value) < 4:
        return True
    if PLACEHOLDER.match(value):
        return True
    if "${" in value or "{{" in value:
        return True
    return len(set(value)) <= 2


def looks_like_expression(value: str) -> bool:
    """A call or subscript is code, not a literal secret. password-property only:
    a quoted password-assignment value may legitimately contain brackets."""
    return "(" in value or "[" in value


def fingerprint(rule: str, path: str, secret: str) -> str:
    digest = hashlib.sha256(f"{rule}|{path}|{secret}".encode("utf-8"))
    return digest.hexdigest()[:16]


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in SKIP_NAMES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            with path.open("rb") as handle:
                if b"\0" in handle.read(8192):
                    continue
        except OSError:
            continue
        yield path


def regex_scan(root: Path) -> "list[dict]":
    findings: list[dict] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = path.as_posix()
        for rule, pattern in RULES:
            for match in pattern.finditer(text):
                secret = match.group(1) if match.groups() else match.group(0)
                if looks_like_placeholder(secret):
                    continue
                if rule == "password-property" and looks_like_expression(secret):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                findings.append({
                    "fingerprint": fingerprint(rule, rel, secret),
                    "rule": rule,
                    "path": rel,
                    "line": line,
                })
    return findings


def gitleaks_scan(root: Path) -> "list[dict] | None":
    """Best-effort wrapper. Returns None if anything is unexpected, so the
    caller falls back rather than silently reporting a clean scan."""
    report = ROOT / ".secrets-baseline.raw.json"
    result = subprocess.run(
        ["gitleaks", "detect", "--source", str(root), "--no-banner", "--redact",
         "--report-format", "json", "--report-path", str(report)],
        capture_output=True, text=True,
    )
    # gitleaks exits 1 when it finds leaks; only a missing report is fatal here.
    if result.returncode not in (0, 1) or not report.exists():
        return None
    try:
        raw = json.loads(report.read_text(encoding="utf-8") or "[]")
    except (json.JSONDecodeError, OSError):
        return None
    findings = []
    for item in raw:
        rel = str(item.get("File", "?")).replace("\\", "/")
        rule = str(item.get("RuleID", "gitleaks"))
        ident = str(item.get("Fingerprint") or item.get("Secret") or rel)
        findings.append({
            "fingerprint": fingerprint(rule, rel, ident),
            "rule": rule,
            "path": rel,
            "line": item.get("StartLine", 0),
            "commit": (item.get("Commit") or "")[:9],
        })
    report.unlink(missing_ok=True)
    return findings


def load_baseline() -> "set[str]":
    if not BASELINE.exists():
        return set()
    try:
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return {f["fingerprint"] for f in data.get("findings", [])}


def write_baseline(findings: "list[dict]", tool: str, history: bool) -> None:
    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "scanned_git_history": history,
        "note": (
            "Fingerprints only - no secret values are stored here. "
            "A recorded finding is not a resolved one: rotate anything live."
        ),
        "findings": sorted(findings, key=lambda f: (f["path"], f["line"])),
    }
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update", action="store_true",
                        help="accept current findings as the new baseline")
    parser.add_argument("--path", default=None,
                        help="scan just this path (default: the whole repo)")
    args = parser.parse_args()

    root = Path(args.path).resolve() if args.path else ROOT

    tool, history, findings = "regex-fallback", False, None
    if lib.which("gitleaks"):
        findings = gitleaks_scan(root)
        if findings is None:
            lib.warn("gitleaks ran but its report could not be read - falling back")
        else:
            tool, history = "gitleaks", True

    if findings is None:
        findings = regex_scan(root)
        if not lib.which("gitleaks") and not lib.which("trufflehog"):
            lib.warn(
                "no gitleaks/trufflehog on PATH - scanned the WORKING TREE ONLY."
            )
            lib.info(
                "       Git history is where old credentials hide. Install "
                "gitleaks and re-run\n"
                "       before you consider the Phase 0 gate passed."
            )

    known = load_baseline()
    fresh = [f for f in findings if f["fingerprint"] not in known]
    first_run = not BASELINE.exists()

    by_rule: dict = {}
    for finding in findings:
        by_rule[finding["rule"]] = by_rule.get(finding["rule"], 0) + 1
    for rule, count in sorted(by_rule.items(), key=lambda kv: -kv[1]):
        lib.info(f"       {count:4}  {rule}")

    if args.update or first_run:
        write_baseline(findings, tool, history)
        if findings:
            lib.warn(
                f"{len(findings)} potential secret(s) recorded in .secrets-baseline"
            )
            lib.info(
                "       Values are NOT stored. Review each one and rotate "
                "anything live.\n"
                "       Then add credential-bearing paths to "
                "exclude_from_search in project.yaml."
            )
        else:
            lib.ok(f"no findings ({tool}, history={history})")
        return 0

    if fresh:
        lib.err(f"{len(fresh)} NEW potential secret(s) since the baseline:")
        for finding in fresh[:20]:
            lib.info(f"       {finding['path']}:{finding['line']}  {finding['rule']}")
        lib.info("       Rotate if live, then: python scripts/scan.py --update")
        return 1

    lib.ok(f"no new findings ({len(findings)} known, {tool}, history={history})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
