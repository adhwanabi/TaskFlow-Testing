import json
from pathlib import Path
from typing import Any

import pytest
import requests

pytestmark = pytest.mark.api


def _load_cases() -> list[dict[str, Any]]:
    cases_path = Path(__file__).with_name("api_cases.json")
    return json.loads(cases_path.read_text(encoding="utf-8"))


def _create_task(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = requests.post(f"{base_url}/api/tasks", json=payload, timeout=10)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_api_case(case: dict[str, Any], api_base_url: str) -> None:
    base_url = api_base_url.rstrip("/")
    path = case["path"]

    setup = case.get("setup") or {}
    if "create_task" in setup:
        created = _create_task(base_url, setup["create_task"])
        path = path.format(task_id=created["id"])

    method = str(case["method"]).upper()
    url = f"{base_url}{path}"

    resp = requests.request(method, url, json=case.get("json"), timeout=10)

    assert resp.status_code == int(case["expected_status"]), resp.text

    if resp.status_code == 204:
        return

    if case.get("assert_type") == "list":
        assert isinstance(resp.json(), list)

    expected_keys = case.get("assert_keys")
    if expected_keys:
        data = resp.json()
        for key in expected_keys:
            assert key in data

    subset = case.get("assert_json_subset")
    if subset:
        data = resp.json()
        for key, value in subset.items():
            assert data.get(key) == value

