# Instructions for AI coding agents (Claude Code, GitHub Copilot, Cursor, Kiro, …)

This repository is **spec-driven**. The spec is the source of truth; code is an output.

## Read order before changing anything

1. `specs/<feature>/spec.md` — what and why. Acceptance criteria have IDs (`AC-xxx`).
2. `specs/<feature>/contracts/openapi.yaml` — the exact API shape.
3. `specs/<feature>/plan.md` — the agreed technical approach.
4. `specs/<feature>/tasks.md` — pick ONE task; do not work outside it.

## Rules

- Never change behaviour that is not described in `spec.md`. If the spec is unclear or
  missing a case, **stop and propose a spec change** instead of guessing in code.
- Never edit `openapi.yaml` to make a failing test pass. The contract changes only when the
  spec changes, and a human approves it.
- Every new acceptance criterion needs a scenario in `acceptance.yaml` or a test tagged
  `@pytest.mark.ac("AC-xxx")`.
- Error codes must be the exact strings listed in `spec.md`.
- The domain layer (`domain.py`) must not import FastAPI.

## Definition of done

```bash
python -m pytest                       # contract + acceptance + rule gates
python tools/check_traceability.py     # every AC covered, no orphans
```

Both must pass. Report which `AC-xxx` your change satisfies.

## Example prompts

- "Implement task T6 from specs/001-appointment-booking/tasks.md. Only BR-4 and BR-5. Run the gates."
- "Draft spec 002 for rescheduling in the same format as spec 001. Do not write code yet."
- "AC-007 is failing. Explain which rule in spec.md the code violates before changing anything."
