# Profiles

The core of this repo knows nothing about any particular kind of work. A profile
adds the artifacts and rules that a *kind* of project needs.

Set one in `project.yaml`:

```yaml
profile: general
```

| Profile | For |
|---|---|
| [`general`](general/) | Almost everything. One repository, local areas. **The default.** |
| [`legacy-modernization`](legacy-modernization/) | Replacing or integrating old systems you do not own: multi-repo, seams, strangler sequencing, traffic capture. |

## What a profile may contain

```
profiles/<name>/
├── README.md          what this profile is for, and when NOT to use it
├── rules.py           extra validation (optional)
├── scaffold/          files copied into the project by init.py (optional)
├── adapters/          extra adapters, searched after the core ones (optional)
├── docs/              profile-specific reference (optional)
└── examples/          worked examples (optional)
```

Everything is optional. A profile that only adds a rule is a `rules.py` and
nothing else.

## Adding one

1. `mkdir profiles/my-profile`
2. Put anything `init.py` should copy under `scaffold/`, mirroring the layout it
   should land in.
3. If it needs extra validation, add `rules.py`:

```python
EXTRA_CARD_SECTIONS = ["Risks"]     # sections every card must carry

def register(ctx):
    """ctx has .project, .root, .error/.warn/.note, .read/.rel"""
    if not (ctx.root / "docs" / "threat-model.md").exists():
        ctx.warn("my-profile", "no threat model", "docs/threat-model.md")
```

4. `python scripts/check.py` - it will tell you if the profile does not load.

That is the whole mechanism. There is deliberately no plugin registry, no entry
points, and no base class: a profile is a directory with optional parts, so the
cost of adding one stays near zero.

## The rule that keeps this honest

**Core must never import a profile.** Dependencies point one way. If something
in `scripts/` needs to know which profile is active in order to work, it belongs
in the profile instead - otherwise the "general" case slowly accumulates
special-casing for domains most users do not have.
