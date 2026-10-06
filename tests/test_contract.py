"""Contract gate: the running app exposes exactly the operations in openapi.yaml — no more, no less."""
from conftest import OPENAPI, SPEC_OPERATIONS
from fastapi.routing import APIRoute

FRAMEWORK_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def _app_operations(app) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute) and route.path not in FRAMEWORK_ROUTES
        for method in route.methods - {"HEAD", "OPTIONS"}
    }


def test_every_spec_operation_is_implemented(frozen_app):
    spec_ops = {(m, t) for m, t, _, _ in SPEC_OPERATIONS}
    missing = spec_ops - _app_operations(frozen_app)
    assert not missing, f"In the contract but not implemented: {sorted(missing)}"


def test_app_exposes_nothing_outside_the_spec(frozen_app):
    spec_ops = {(m, t) for m, t, _, _ in SPEC_OPERATIONS}
    extra = _app_operations(frozen_app) - spec_ops
    assert not extra, f"Implemented but not in the contract (update the spec first): {sorted(extra)}"


def test_error_codes_in_spec_match_contract():
    """The error codes named in spec.md are exactly the enum in openapi.yaml."""
    import re
    from conftest import SPEC_DIR

    spec_text = (SPEC_DIR / "spec.md").read_text()
    in_spec = set(re.findall(r"`([A-Z]+(?:_[A-Z]+)+)`", spec_text))
    in_contract = set(OPENAPI["components"]["schemas"]["Error"]["properties"]["code"]["enum"])
    assert in_spec == in_contract, f"spec.md only: {in_spec - in_contract}; openapi only: {in_contract - in_spec}"
