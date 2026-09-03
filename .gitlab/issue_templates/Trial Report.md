<!--
One of these per tester, filed when you finish - separate from the individual
bugs, which stay as their own issues.

This is the report that answers the question the test suites cannot: does this
help. Fill it in even if you found nothing, because "nothing broke and it also
did not help" is the most useful result this build could get.
-->

### Which tracks you ran

- [ ] A - a project from scratch
- [ ] B - adoption into an existing project
- [ ] C - the guardrails
- [ ] D - the numbers (`usage.py --all`)

### Build

<!-- Output of: git describe --tags -->

```
```

### Did adoption keep its promise

<!--
Track B's claim: adds files, modifies nothing that was already there, and the
undo restores exactly. Answer from your hash comparison, not your impression.
-->

- Files modified that you did not create:
- Files deleted that you did not create:
- Did the after-undo state match your baseline:

### Bugs you filed

<!-- Just the issue numbers: #12, #13 -->

### Where you got stuck

<!--
The most valuable section. Anywhere you had to re-read something, guess, or
ask a person. Include the places you worked out yourself - if it cost you five
minutes it will cost the next person five minutes.
-->

### Did it make anything easier

<!--
Honestly. This is the open question: three trials proved adoption is safe, none
has shown it makes the work cheaper. If it was overhead with no return, that is
the finding, and it is more useful than a bug.
-->

### Would you use it on your own project

<!-- Yes / No / Not as it stands - and the reason, which is the part that matters. -->

### Anything the documentation claimed that was not true

<!-- Quote the line. A wrong safety claim is treated as a bug, not a doc nit. -->

/label ~"build-0A" ~"trial-report"
