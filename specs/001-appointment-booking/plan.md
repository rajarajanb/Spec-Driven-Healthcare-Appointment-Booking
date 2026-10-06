# Plan 001 — Technical approach

> This file describes **how** we will satisfy `spec.md`. If the spec changes, this plan is
> reviewed. If this plan changes, the spec does not have to.

## Stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Team default, fast to read in a blog |
| HTTP | FastAPI | Typed request models, easy test client |
| Contract | OpenAPI 3.1 (`contracts/openapi.yaml`) | Hand-written, reviewed like code — **the contract is not generated from the code** |
| Storage | In-memory repository | v1 scope; the repository interface keeps a DB swap local |
| Time | Injected `Clock` | NFR-3: rules like BR-2/BR-4 must be testable deterministically |
| Tests | pytest | Unit, contract and acceptance tests in one runner |

## Architecture

```
api.py          HTTP layer: maps requests/responses, translates domain errors to the envelope
domain.py       BookingService: enforces BR-1..BR-5, raises typed DomainError(code, status)
repository.py   InMemoryRepository + seed data (providers, slots)
clock.py        Clock protocol, SystemClock, FixedClock
```

The domain layer never imports FastAPI. Error codes in the domain (`SLOT_UNAVAILABLE`, …) are
the same strings listed in `spec.md` and `openapi.yaml`.

## Verification gates (run locally and in CI)

1. **Contract gate** — `tests/test_contract.py`
   - Every operation in `openapi.yaml` is implemented, and the app exposes nothing extra.
2. **Behaviour gate** — `tests/test_acceptance.py`
   - Executes every scenario in `acceptance.yaml` against the app with a fixed clock.
   - Validates every response body against the OpenAPI schema for that status (NFR-1).
3. **Rule gate** — `tests/test_rules.py`
   - Fast unit tests on `BookingService`, each tagged with the AC it proves.
4. **Traceability gate** — `tools/check_traceability.py`
   - Every `AC-xxx` in `spec.md` is covered by at least one scenario or test.
   - No test references an AC that is not in the spec (no orphan tests).

## Seed data

Two providers, slots for today + 3 days at 08:00, 09:30, 11:00, 14:00, 16:00 (UTC).
Slot IDs are relative to "today" so they are stable in any run: `PR-001-D1-0930` means
provider PR-001, tomorrow, 09:30.
