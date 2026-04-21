import os
import socket
import subprocess
import sys
import tempfile
import time
import importlib.util

import pytest
import requests


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Base URL untuk API.

    - Jika env var `API_BASE_URL` diset: fixture hanya mengembalikan nilainya (asumsi server sudah running).
    - Jika tidak: fixture akan menyalakan uvicorn untuk durasi session.
    """
    external = os.environ.get("API_BASE_URL")
    if external:
        return external.rstrip("/")

    if importlib.util.find_spec("uvicorn") is None:
        pytest.skip(
            "uvicorn belum terinstall dan API_BASE_URL tidak diset. "
            "Install dependencies dengan `pip install -r requirements-test.txt` "
            "atau jalankan backend lalu set API_BASE_URL."
        )

    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory(prefix="taskflow-test-") as tmpdir:
        db_path = os.path.join(tmpdir, "tasks.db")
        env = os.environ.copy()
        env["TASKFLOW_DB_PATH"] = db_path

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=os.getcwd(),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            deadline = time.time() + 30
            last_err: Exception | None = None
            while time.time() < deadline:
                try:
                    resp = requests.get(f"{base_url}/", timeout=2)
                    if resp.status_code == 200:
                        yield base_url
                        return
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
                time.sleep(0.25)

            out = ""
            if process.stdout:
                try:
                    out = process.stdout.read()[-2000:]
                except Exception:  # noqa: BLE001
                    out = ""
            raise RuntimeError(
                f"API server tidak siap di {base_url} dalam 30s. Last error: {last_err}\n"
                f"--- uvicorn output (tail) ---\n{out}"
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
