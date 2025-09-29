from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterator

import pytest
import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT_DIR / "docker-compose.dev.yml"
STACK_SERVICES = (
    "postgres",
    "zookeeper",
    "kafka",
    "user-service",
    "event-service",
    "matching-service",
    "api-gateway",
)
HEALTH_CHECKS = (
    "http://localhost:8081/health",
    "http://localhost:8083/health",
    "http://localhost:8082/health",
    "http://localhost:8080/health",
)


def _compose_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("COMPOSE_PROJECT_NAME", "meetinity_integration")
    return env


def _run_compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        *args,
    ]
    return subprocess.run(
        command,
        check=check,
        env=_compose_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _wait_for_http(url: str, timeout: float = 180.0, interval: float = 2.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                return
        except requests.RequestException as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(interval)
    message = f"Timed out waiting for service at {url}"
    if last_error is not None:
        message = f"{message}: {last_error}"
    raise RuntimeError(message)


@pytest.fixture(scope="session")
def docker_stack() -> Iterator[dict[str, str]]:
    if not COMPOSE_FILE.exists():
        pytest.skip("Docker Compose file missing; integration stack unavailable")
    if shutil.which("docker") is None:
        pytest.skip("Docker is required to run integration tests")

    try:
        _run_compose("down", "-v", "--remove-orphans", check=False)
        _run_compose("build", *STACK_SERVICES)
        _run_compose("up", "-d", *STACK_SERVICES)
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"Unable to start docker-compose stack: {exc.stdout}")

    try:
        for url in HEALTH_CHECKS:
            _wait_for_http(url)
        # Seed deterministic fixtures
        _run_compose("--profile", "seed", "run", "--rm", "seed-data")
        _wait_for_http("http://localhost:8080/health")
        yield {"gateway": "http://localhost:8080"}
    finally:
        _run_compose("down", "-v", "--remove-orphans", check=False)


@pytest.fixture(scope="session")
def gateway_base_url(docker_stack: dict[str, str]) -> str:
    return docker_stack["gateway"]
