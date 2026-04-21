import pytest
import requests

pytestmark = pytest.mark.api


def test_sqli_payload_in_title_should_not_crash_and_is_stored_as_text(api_base_url: str) -> None:
    payload = {"title": "' OR 1=1 --", "description": "sqli", "status": "pending"}
    resp = requests.post(f"{api_base_url}/api/tasks", json=payload, timeout=10)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == payload["title"]


def test_sqli_payload_as_task_id_should_be_rejected(api_base_url: str) -> None:
    resp = requests.get(f"{api_base_url}/api/tasks/%27%20OR%201%3D1%20--", timeout=10)
    assert resp.status_code == 422
