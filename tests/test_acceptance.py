"""Behaviour gate: run every scenario in acceptance.yaml against a fresh app with a frozen clock."""
import pytest
from conftest import ACCEPTANCE, FROZEN_AT, assert_conforms_to_contract
from fastapi.testclient import TestClient

from booking.api import create_app
from booking.clock import FixedClock


def _check_list(body: dict, rule: dict) -> None:
    ids = [item[rule["key"]] for item in body[rule["field"]]]
    for x in rule.get("includes", []):
        assert x in ids, f"expected {x} in {rule['field']}, got {ids}"
    for x in rule.get("excludes", []):
        assert x not in ids, f"did not expect {x} in {rule['field']}, got {ids}"
    if "equals" in rule:
        assert ids == rule["equals"], f"expected exactly {rule['equals']}, got {ids}"


@pytest.mark.parametrize("scenario", ACCEPTANCE["scenarios"], ids=lambda s: s["id"])
def test_acceptance_scenario(scenario):
    client = TestClient(create_app(FixedClock(FROZEN_AT)))
    saved: dict[str, str] = {}

    for n, step in enumerate(scenario["steps"], start=1):
        req, expect = step["request"], step["expect"]
        path = req["path"].format(**saved)
        resp = client.request(req["method"], path, json=req.get("body"))
        body = resp.json()
        where = f"{scenario['id']} step {n}: {req['method']} {path}"

        assert resp.status_code == expect["status"], f"{where} -> {resp.status_code} {body}"
        assert_conforms_to_contract(req["method"], path, resp.status_code, body)
        for key, value in expect.get("body", {}).items():
            assert body.get(key) == value, f"{where}: {key}={body.get(key)!r}, expected {value!r}"
        if "list" in expect:
            _check_list(body, expect["list"])
        for name, field in step.get("save", {}).items():
            saved[name] = body[field]
