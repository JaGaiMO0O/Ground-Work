"""A deliberately small YAML-subset parser.

This exists for one reason: the playbook's Phase 0 is a security gate, and a
security gate must never be blocked by `pip install`. If PyYAML is present we
use it. If it is not, we fall back to this.

It handles exactly the shapes `project.yaml` uses:

    key: scalar
    key:
      nested: map
    key:
      - scalar item
      - key: list of maps
        more: keys
    key: [inline, list]
    # comments, blank lines, 'quoted strings'

Anything else raises MinYamlError telling the caller to install PyYAML. Do not
mistake this for a YAML implementation - it is a fallback, and it is allowed to
be narrow.
"""

from __future__ import annotations

__all__ = ["parse", "MinYamlError"]


class MinYamlError(ValueError):
    """Raised on any construct outside the supported subset."""


# --------------------------------------------------------------------------
# scalars
# --------------------------------------------------------------------------

_TRUE = {"true", "yes", "on"}
_FALSE = {"false", "no", "off"}
_NULL = {"null", "~", ""}


def _strip_comment(line: str) -> str:
    """Remove a trailing '# comment', respecting quotes."""
    out: list[str] = []
    quote = None
    i = 0
    while i < len(line):
        c = line[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def _split_commas(s: str) -> list[str]:
    parts, buf, quote, depth = [], [], None, 0
    for c in s:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            buf.append(c)
        elif c in "[{":
            depth += 1
            buf.append(c)
        elif c in "]}":
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _scalar(tok: str):
    t = tok.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        return [_scalar(p) for p in _split_commas(inner)] if inner else []
    if t.startswith("{"):
        raise MinYamlError("inline maps are not supported; install PyYAML")
    low = t.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    if low in _NULL:
        return None
    try:
        return int(t)
    except ValueError:
        pass
    try:
        return float(t)
    except ValueError:
        pass
    return t


def _mapping_split(text: str):
    """Return (key, rest) if `text` opens a mapping entry, else None."""
    quote = None
    depth = 0
    for i, c in enumerate(text):
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == ":" and depth == 0:
            after = text[i + 1:]
            if after == "" or after[0] in " \t":
                key = text[:i].strip()
                if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
                    key = key[1:-1]
                return key, after.strip()
    return None


# --------------------------------------------------------------------------
# line model
# --------------------------------------------------------------------------


def _tokenize(text: str) -> list:
    """-> [(indent, tag, content, lineno)], comments and blanks removed.

    tag is one of:
      "kv"       a mapping entry, `key: value` or `key:`
      "-"        a list item whose value is a nested block
      "-scalar"  a list item holding a scalar, e.g. `- src/**/*.xml`

    A `- key: value` line is split into a bare "-" plus a "kv" row at a deeper
    indent, so the parser only ever meets one construct per row. Scalar items
    are NOT split -- their body is not a mapping and must not be parsed as one.
    """
    rows: list = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise MinYamlError(f"line {lineno}: tab indentation; use spaces")
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        if stripped.lstrip().startswith("---"):
            continue
        indent = len(stripped) - len(stripped.lstrip())
        content = stripped.strip()
        if content == "-":
            rows.append((indent, "-", "", lineno))
        elif content.startswith("- "):
            body = content[2:].strip()
            if _mapping_split(body) is None:
                rows.append((indent, "-scalar", body, lineno))
            else:
                rows.append((indent, "-", "", lineno))
                rows.append((indent + 2, "kv", body, lineno))
        else:
            rows.append((indent, "kv", content, lineno))
    return rows


def _parse_node(rows, i, indent):
    if i >= len(rows):
        return None, i
    ind, tag, _content, _lineno = rows[i]
    if ind < indent:
        return None, i
    if tag in ("-", "-scalar"):
        return _parse_list(rows, i, ind)
    return _parse_map(rows, i, ind)


def _parse_list(rows, i, indent):
    items = []
    while i < len(rows):
        ind, tag, content, lineno = rows[i]
        if ind < indent:
            break
        if ind > indent:
            raise MinYamlError(f"line {lineno}: unexpected indent in list")
        if tag == "-scalar":
            items.append(_scalar(content))
            i += 1
            continue
        if tag != "-":
            break
        i += 1
        value, i = _parse_node(rows, i, indent + 1)
        items.append(value)
    return items, i


def _parse_map(rows, i, indent):
    out: dict = {}
    while i < len(rows):
        ind, tag, content, lineno = rows[i]
        if ind < indent:
            break
        if ind > indent:
            raise MinYamlError(f"line {lineno}: unexpected indent in mapping")
        if tag != "kv":
            break
        split = _mapping_split(content)
        if split is None:
            raise MinYamlError(f"line {lineno}: expected 'key: value', got {content!r}")
        key, rest = split
        i += 1
        if rest:
            out[key] = _scalar(rest)
        else:
            out[key], i = _parse_node(rows, i, indent + 1)
    return out, i


def parse(text: str):
    """Parse a YAML subset document into Python data."""
    rows = _tokenize(text)
    if not rows:
        return {}
    value, i = _parse_node(rows, 0, rows[0][0])
    if i < len(rows):
        raise MinYamlError(f"line {rows[i][3]}: could not parse past here")
    return value
