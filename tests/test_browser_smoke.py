from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen
import os
import socket
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_static_ui_boots_through_server_in_browser(tmp_path: Path):
    playwright = pytest.importorskip("playwright.sync_api")
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["TOOLING_SHOWCASE_OLLAMA_ENABLED"] = "false"
    env["TOOLING_SHOWCASE_OLLAMA_TIMEOUT"] = "1"
    env["TOOLING_SHOWCASE_WORKSPACE"] = str(tmp_path)
    env["TOOLING_SHOWCASE_PORTFOLIO"] = str(tmp_path)
    env["TOOLING_SHOWCASE_JOURNAL"] = str(tmp_path / "state" / "events.jsonl")
    env["TOOLING_SHOWCASE_BENCHMARKS"] = str(tmp_path / "state" / "model_benchmarks.json")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tooling_showcase.cli",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server(base_url, proc)
        with playwright.sync_playwright() as browser_api:
            try:
                browser = browser_api.chromium.launch()
            except playwright.Error as exc:
                pytest.skip(f"Playwright Chromium is not installed: {exc}")
            try:
                page_errors: list[str] = []
                page = browser.new_page()
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded", timeout=10_000)
                page.wait_for_selector("#promptInput", state="visible", timeout=5_000)
                page.wait_for_selector("#sendBtn", state="visible", timeout=5_000)
                page.wait_for_function(
                      "() => document.querySelectorAll('#toolSelect option').length > 0",
                      timeout=5_000,
                )
                assert page.locator("#runtimeStatusStrip").count() == 1
                assert page.locator("#toolSelect option").count() > 0
                assert page_errors == []
            finally:
                browser.close()
    finally:
        _stop_server(proc)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(base_url: str, proc: subprocess.Popen[str], timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            pytest.fail(f"server exited before startup with code {proc.returncode}: {output}")
        try:
            with urlopen(base_url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    pytest.fail("server did not start before timeout")


def _stop_server(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
