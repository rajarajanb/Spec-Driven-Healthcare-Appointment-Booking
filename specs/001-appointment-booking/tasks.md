# Tasks 001 — Implementation breakdown

Each task is small enough for one PR (or one AI-agent run) and names the criteria it satisfies.
A task is "done" only when its listed ACs pass in CI.

| # | Task | Satisfies | Status |
|---|---|---|---|
| T1 | Write `contracts/openapi.yaml` (paths, schemas, error envelope) and get it reviewed | NFR-1, NFR-2 | ✅ |
| T2 | Write `acceptance.yaml` scenarios for every AC | AC-001…AC-010 | ✅ |
| T3 | Add `Clock` abstraction (`SystemClock`, `FixedClock`) | NFR-3 | ✅ |
| T4 | Repository + seed data with relative slot IDs | AC-008 | ✅ |
| T5 | `BookingService.book()` enforcing BR-1, BR-2, BR-3 | AC-001…AC-005 | ✅ |
| T6 | `BookingService.cancel()` enforcing BR-4, BR-5 | AC-006, AC-007 | ✅ |
| T7 | HTTP layer + error-envelope handlers (incl. validation errors) | AC-009, AC-010 | ✅ |
| T8 | Contract, acceptance, rule tests + traceability script | all | ✅ |
| T9 | CI workflow: all four gates must pass before merge | all | ✅ |
