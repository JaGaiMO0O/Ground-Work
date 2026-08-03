# Examples

Two worked system cards, plus the `project.yaml` that declares them.

**These are reference material, not real systems.** `scripts/init.py` deletes
this whole directory when you personalize the template. Read them first.

| Example | Demonstrates |
|---|---|
| [`billing-legacy/`](billing-legacy/) | The straightforward case: source in git, an HTTP boundary you can record, a database you can read. This is the shape the playbook is written around. |
| [`orders-forms-legacy/`](orders-forms-legacy/) | The hard case: Oracle Forms. Binary sources that grep cannot read, business logic inside the `.fmb` triggers, no HTTP boundary to capture, and a contract that lives in PL/SQL packages. |
| [`project.yaml`](project.yaml) | All three system shapes - `kind: repo`, `kind: database`, and a repo with a `derive:` block. |

## Read them in this order

1. `billing-legacy/CARD.md` - what a good card looks like, and how claims cite
   evidence rather than impressions.
2. `billing-legacy/seams.md` - why an honestly-recorded ENTANGLED seam is worth
   more than an optimistic one.
3. `orders-forms-legacy/CARD.md` - what changes when the playbook's assumptions
   do not hold.
4. `project.yaml` - how all of that is declared.

Each file ends with a commented block explaining *why* it is shaped the way it
is. Those blocks are for you, not for an agent - delete them from your own
cards.

## The thing worth copying

Not the format. The **evidence discipline**.

Both cards distinguish between what was observed and what was assumed. "Dead
since 2019, zero hits in 12 months of access logs" is a fact the next person
can act on. "Looks unused" is a guess, and guesses belong in the `Confidence:`
line where they are labelled as such.

That distinction is what makes a card safe to trust without re-reading the
code - which is the entire economic argument for writing one.
