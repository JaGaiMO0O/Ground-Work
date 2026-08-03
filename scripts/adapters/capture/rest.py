#!/usr/bin/env python3
"""rest.py - `capture` adapter for HTTP systems. Working reference.

Verbs:  record | contract | fixtures
Reads:  CAPTURE_BASE_URL, CAPTURE_AUTH_HEADER (optional)
Contract: docs/adapters.md

  record    runs a recording reverse proxy in front of the legacy service.
            Point a client - or a slice of real traffic - at it, and it writes
            one JSON line per exchange.
  contract  reduces those recordings to an OpenAPI 3 skeleton grounded in what
            was actually called, with observation counts per operation.
  fixtures  reduces them to golden-master request/response pairs, so you can
            prove the replacement behaves the same way.

The counts are the point as much as the schema. An endpoint observed zero times
in a week of real traffic probably does not need reimplementing, and that is
usually the single largest scope reduction available.

SENSITIVE DATA. Recordings are real traffic. Auth headers and cookies are
redacted automatically; BODIES ARE NOT, because the body is the payload you
need. Raw recordings are gitignored for exactly that reason. Treat
integration/fixtures/<system>/raw/ as production data.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

REDACT_HEADERS = {
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "x-auth-token",
}
HOP_BY_HOP = {"transfer-encoding", "connection", "keep-alive", "upgrade"}


def cfg_error(message: str) -> "int":
    print(f"  [rest] {message}", file=sys.stderr)
    return 4


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_headers(items) -> dict:
    return {
        k: ("<redacted>" if k.lower() in REDACT_HEADERS else v)
        for k, v in items
    }


def encode_body(raw: bytes) -> dict:
    if not raw:
        return {"body": "", "encoding": "text"}
    try:
        return {"body": raw.decode("utf-8"), "encoding": "text"}
    except UnicodeDecodeError:
        return {"body": base64.b64encode(raw).decode("ascii"), "encoding": "base64"}


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------


def cmd_record(args) -> int:
    base = os.environ.get("CAPTURE_BASE_URL", "").rstrip("/")
    if not base:
        return cfg_error("CAPTURE_BASE_URL is not set - see .env.example")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    logfile = out_dir / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.jsonl"
    deadline = time.time() + args.hours * 3600
    counter = {"n": 0}

    extra_auth = os.environ.get("CAPTURE_AUTH_HEADER", "")

    class Recorder(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):  # keep stdout clean; stdout is data
            pass

        def _proxy(self):
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""

            forward = {
                k: v for k, v in self.headers.items()
                if k.lower() not in {"host", "content-length", "accept-encoding"}
            }
            if extra_auth and ":" in extra_auth:
                name, _, value = extra_auth.partition(":")
                forward[name.strip()] = value.strip()

            started = time.time()
            try:
                req = urlrequest.Request(
                    base + self.path, data=body or None,
                    method=self.command, headers=forward,
                )
                with urlrequest.urlopen(req, timeout=60) as resp:
                    status = resp.status
                    resp_headers = list(resp.getheaders())
                    resp_body = resp.read()
            except urlerror.HTTPError as exc:
                status = exc.code
                resp_headers = list(exc.headers.items())
                resp_body = exc.read()
            except Exception as exc:  # upstream unreachable
                self.send_error(502, f"upstream unreachable: {exc}")
                return

            entry = {
                "ts": stamp(),
                "ms": round((time.time() - started) * 1000),
                "method": self.command,
                "path": self.path,
                "request": {
                    "headers": safe_headers(self.headers.items()),
                    **encode_body(body),
                },
                "status": status,
                "response": {
                    "headers": safe_headers(resp_headers),
                    **encode_body(resp_body),
                },
            }
            with logfile.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
            counter["n"] += 1

            self.send_response(status)
            for key, value in resp_headers:
                if key.lower() in HOP_BY_HOP or key.lower() == "content-length":
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        do_GET = do_POST = do_PUT = do_PATCH = _proxy
        do_DELETE = do_HEAD = do_OPTIONS = _proxy

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Recorder)
    server.timeout = 1
    print(
        f"  [rest] recording http://127.0.0.1:{args.port} -> {base}\n"
        f"  [rest] for {args.hours}h, into {logfile}. Ctrl-C to stop early.",
        file=sys.stderr,
    )
    try:
        while time.time() < deadline:
            server.handle_request()
    except KeyboardInterrupt:
        print("\n  [rest] stopped", file=sys.stderr)
    finally:
        server.server_close()

    print(f"  [rest] {counter['n']} exchange(s) recorded", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# reduction
# ---------------------------------------------------------------------------

UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                  r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def templated(path: str) -> str:
    """/invoices/4471/lines -> /invoices/{id}/lines"""
    clean = path.split("?", 1)[0]
    parts = []
    for segment in clean.split("/"):
        if segment.isdigit() or UUID.match(segment):
            parts.append("{id}")
        else:
            parts.append(segment)
    return "/".join(parts) or "/"


def read_raw(raw_dir: Path) -> "list[dict]":
    entries: list[dict] = []
    for path in sorted(raw_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def group(entries: "list[dict]") -> dict:
    grouped: dict = {}
    for entry in entries:
        key = (templated(entry.get("path", "/")), entry.get("method", "GET"))
        slot = grouped.setdefault(key, {
            "count": 0, "statuses": {}, "example": entry,
            "first": entry.get("ts"), "last": entry.get("ts"),
        })
        slot["count"] += 1
        status = str(entry.get("status", "000"))
        slot["statuses"][status] = slot["statuses"].get(status, 0) + 1
        slot["last"] = entry.get("ts")
    return grouped


def yaml_dump(value, indent: int = 0) -> str:
    """Minimal YAML writer. The structure emitted here is fully known, so a
    dependency on PyYAML would buy nothing."""
    pad = "  " * indent
    if isinstance(value, dict):
        if not value:
            return " {}\n"
        out = "\n"
        for key, item in value.items():
            rendered = yaml_dump(item, indent + 1)
            out += f"{pad}  {json.dumps(str(key))}:{rendered}"
        return out
    if isinstance(value, list):
        if not value:
            return " []\n"
        out = "\n"
        for item in value:
            out += f"{pad}  -{yaml_dump(item, indent + 1).rstrip()}\n"
        return out
    if isinstance(value, bool):
        return f" {'true' if value else 'false'}\n"
    if isinstance(value, (int, float)):
        return f" {value}\n"
    return f" {json.dumps(str(value))}\n"


def cmd_contract(args, raw_dir: Path) -> int:
    entries = read_raw(raw_dir)
    if not entries:
        print(f"  [rest] no recordings in {raw_dir}", file=sys.stderr)
        print("  [rest] run:  python scripts/capture.py <system> record", file=sys.stderr)
        return 4

    grouped = group(entries)
    paths: dict = {}
    for (template, method), slot in sorted(grouped.items()):
        responses = {
            code: {"description": f"observed {n} time(s)"}
            for code, n in sorted(slot["statuses"].items())
        }
        paths.setdefault(template, {})[method.lower()] = {
            "summary": f"observed {slot['count']} time(s) in capture",
            "x-observed": {
                "count": slot["count"],
                "first_seen": slot["first"],
                "last_seen": slot["last"],
            },
            "responses": responses,
        }

    doc = {
        "openapi": "3.0.3",
        "info": {
            "title": f"{args.area} (observed)",
            "version": "0.0.0-observed",
            "description": (
                f"GENERATED by scripts/adapters/capture/rest.py on {stamp()} "
                f"from {len(entries)} recorded exchange(s). Do not hand-edit. "
                f"Re-run: python scripts/capture.py {args.area} contract. "
                "This describes what was OBSERVED, not what was intended. An "
                "operation absent here was not called during the capture "
                "window - check the window before concluding it is dead."
            ),
        },
        "paths": paths,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = (
        f"# GENERATED by scripts/adapters/capture/rest.py on {stamp()}\n"
        f"# Source: {len(entries)} exchange(s) under {raw_dir.name}/. Do not hand-edit.\n"
        f"# Re-run: python scripts/capture.py {args.area} contract\n\n"
    )
    for key, value in doc.items():
        text += f"{json.dumps(key)}:{yaml_dump(value, 0)}"
    out.write_text(text, encoding="utf-8")

    print(f"  [rest] {len(grouped)} operation(s) from {len(entries)} exchange(s)",
          file=sys.stderr)
    return 0


def cmd_fixtures(args, raw_dir: Path) -> int:
    entries = read_raw(raw_dir)
    if not entries:
        print(f"  [rest] no recordings in {raw_dir}", file=sys.stderr)
        return 4

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []

    for (template, method), slot in sorted(group(entries).items()):
        example = slot["example"]
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", template).strip("-") or "root"
        name = f"{method.lower()}_{slug}_{example.get('status')}.json"
        payload = {
            "_generated": (
                f"GENERATED by scripts/adapters/capture/rest.py on {stamp()}. "
                f"Do not hand-edit. Re-run: python scripts/capture.py "
                f"{args.area} fixtures"
            ),
            "operation": {"method": method, "path_template": template},
            "observed_count": slot["count"],
            "request": {
                "method": method,
                "path": example.get("path"),
                "headers": example.get("request", {}).get("headers", {}),
                "body": example.get("request", {}).get("body", ""),
            },
            "expected_response": {
                "status": example.get("status"),
                "body": example.get("response", {}).get("body", ""),
            },
        }
        (out_dir / name).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        index.append({"file": name, "method": method, "path": template,
                      "observed_count": slot["count"]})

    (out_dir / "index.json").write_text(
        json.dumps({"generated": stamp(), "fixtures": index}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  [rest] {len(index)} fixture(s) written to {out_dir}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("verb", choices=["record", "contract", "fixtures"])
    parser.add_argument("--area", default=os.environ.get("AREA_NAME", "system"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--raw", default=None,
                        help="raw recordings directory (default: <fixtures>/raw)")
    args = parser.parse_args()

    root = Path(os.environ.get("PROJECT_ROOT", "."))
    raw_dir = Path(args.raw) if args.raw else (
        root / "integration" / "fixtures" / args.area / "raw"
    )

    if args.verb == "record":
        return cmd_record(args)
    if args.verb == "contract":
        return cmd_contract(args, raw_dir)
    return cmd_fixtures(args, raw_dir)


if __name__ == "__main__":
    sys.exit(main())
