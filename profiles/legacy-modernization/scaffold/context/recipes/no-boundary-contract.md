# Recipe: contract for a system with no observable boundary

Use when: `capture.py` cannot record this system. Oracle Forms, a green-screen
terminal app, a batch-only job, a desktop client speaking a proprietary
protocol, anything where the "interface" is a database session rather than a
request.

The traffic-capture path assumes an HTTP-ish seam exists. Often it does not.
This is what to do instead, and it is a normal situation, not a failure.

## Fallback order, most trustworthy first

1. **Access / audit logs.** What was actually called, and how often. The
   closest thing to observed truth available, and it also tells you what is
   *unused* - which shrinks scope more than anything else here.
2. **Integration tests.** Someone already encoded the expected contract.
3. **Client code.** Usually more honest about the real contract than the
   service is, because it had to work against reality.
4. **The service's own source.** Last, and least trustworthy.

For a database-centric system, add: DB audit trail, `DBA_DEPENDENCIES`, grants,
and which packages the UI actually calls. In an Oracle Forms application the
PL/SQL package boundary *is* the contract, whether or not anyone designed it
that way.

Load, in order:
1. `map/<system>/CARD.md`
2. `map/<system>/derived/**` - the converted, greppable sources
3. `map/<system>/schema.sql` - for Forms, the database IS the interface
4. Only then: the derived source itself

Do NOT load: `.fmb`, `.fmx`, `.rdf`, or any other binary source directly. Grep
cannot read them, and opening one burns context on garbage. Run the derive step
first - see `profiles/legacy-modernization/docs/stacks/oracle-forms.md`.

MCP servers: none.

Done when: `integration/contracts/<system>.v0.yaml` exists, **every operation
in it cites its evidence** (a log line, a test, a caller), and operations you
could not find evidence for are listed explicitly as `unknown: true` rather
than quietly omitted. An unknown you have named is manageable; one you have
dropped is a cutover incident.
