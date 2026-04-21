import pytest
import requests

pytestmark = pytest.mark.api


def test_security_headers_present(api_base_url: str) -> None:
    resp = requests.get(f"{api_base_url}/", timeout=10)
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"

    csp = headers.get("Content-Security-Policy")
    assert csp is not None and "default-src" in csp

