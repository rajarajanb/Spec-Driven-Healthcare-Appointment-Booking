## Which spec does this PR implement or change?

- Spec: `specs/___/spec.md`
- Acceptance criteria touched: AC-___

## Spec-first checklist

- [ ] If behaviour changed, `spec.md` was updated **first** (in this PR or an earlier one)
- [ ] If the API shape changed, `contracts/openapi.yaml` was updated
- [ ] New/changed ACs have scenarios in `acceptance.yaml` or tagged tests (`@pytest.mark.ac`)
- [ ] `python -m pytest` and `python tools/check_traceability.py` pass locally
