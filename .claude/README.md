# .claude/ - the playbook's rules, made mechanical

The playbook states six operational rules and several hard constraints. Stated
in prose, they hold until somebody is in a hurry. This directory turns the ones
that can be enforced into things the harness enforces.

## settings.json

| Rule (prose) | Mechanism |
|---|---|
| "Legacy repos are READ-ONLY" | `Write`/`Edit` denied on `systems/**` |
| "Secrets live in .env - never read, never echo" | `Read` denied on `.env` and `**/.env` |
| "Generated files carry a header. Never hand-edit" | `Write`/`Edit` denied on `schema.sql`, `erd.mmd`, `derived/**`, `.rgignore` |
| Raw captures are production data | `Read` denied on `integration/fixtures/**/raw/**` |

The `allow` list covers the control-plane scripts and read-only git, so routine
work does not generate permission prompts.

**Limitation, stated plainly.** These rules bind the `Read`/`Write`/`Edit`
tools. A sufficiently creative `Bash` invocation can still write into
`systems/`. The deny list raises the floor; it is not a sandbox. The real
guarantee is that `systems/` is gitignored and reproducible, so anything
written there is discarded by the next `sync.py`.

## skills/

| Skill | Does |
|---|---|
| `survey-area` | Survey one area and write its card: dedicated session, delegate the wide reading, output only the card, then stop |
| `trace-field` | Trace a value end to end in the right load order |
| `handoff` | Write the dated session handoff |
| `check` | Run the validator and explain what each failure means |

The `legacy-modernization` profile adds `survey-system`, which is the same
protocol extended for an external system you do not own.

Skills mirror `context/recipes/`. The recipes are the canonical text - the
skills are the executable path to the same thing. If they ever disagree, the
recipe wins and the skill is the bug.

## agents/

`surveyor` is a read-only reconnaissance subagent. It has no `Write` or `Edit`
tool at all, which is deliberate: it exists to absorb the cost of reading forty
files and hand back a summary, so that forty files of raw content never enter
the main conversation. The main session writes the card.
