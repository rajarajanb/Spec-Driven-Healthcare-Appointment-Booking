"""Shared helpers: load the spec artefacts and validate responses against the OpenAPI contract."""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "specs" / "001-appointment-booking"
sys.path.insert(0, str(ROOT / "src"))

from booking.api import create_app  # noqa: E402
from booking.clock import FixedClock  # noqa: E402

OPENAPI = yaml.safe_load((SPEC_DIR / "contracts" / "openapi.yaml").read_text())
ACCEPTANCE = yaml.safe_load((SPEC_DIR / "acceptance.yaml").read_text())
FROZEN_AT = datetime.fromisoformat(ACCEPTANCE["clock"].replace("Z", "+00:00"))


def pytest_configure(config):
    config.addinivalue_line("markers", "ac(id): links a test to an acceptance criterion in spec.md")


def _path_regex(template: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\{[^/]+\}", r"[^/]+", template) + "$")


SPEC_OPERATIONS = [
    (method.upper(), template, _path_regex(template), op)
    for template, item in OPENAPI["paths"].items()
    for method, op in item.items()
]


def find_operation(method: str, path: str):
    path = path.split("?")[0]
    for m, template, rx, op in SPEC_OPERATIONS:
        if m == method.upper() and rx.match(path):
            return template, op
    return None, None


def assert_conforms_to_contract(method: str, path: str, status: int, body) -> None:
    """NFR-1: the status must be documented and the body must match its schema exactly."""
    template, op = find_operation(method, path)
    assert op is not None, f"{method} {path} is not in openapi.yaml"
    documented = op["responses"]
    assert str(status) in documented, (
        f"{method} {template} returned {status}, but the contract only documents {sorted(documented)}"
    )
    schema = documented[str(status)]["content"]["application/json"]["schema"]
    validator = Draft202012Validator({**schema, "components": OPENAPI["components"]})
    errors = sorted(validator.iter_errors(body), key=lambda e: list(e.path))
    assert not errors, f"{method} {template} {status} violates the contract: " + "; ".join(
        f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
    )


@pytest.fixture
def frozen_app():
    return create_app(FixedClock(FROZEN_AT))
