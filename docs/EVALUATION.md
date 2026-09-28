# Evaluation

## Question
Can explicit evidence, owner and dependency state reduce ambiguity in long-running institutional processes?

## Metrics
- Missing-evidence detection
- Dependency-state correctness
- False-ready rate
- Audit completeness
- Next-action determinism

## Falsification
- A case becomes READY with missing evidence.
- An unresolved blocker is ignored.
- Ownerless cases progress to READY.
