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
    (tmp_path / "README.md").write_text("# Demo\n\nBrowser smoke README.\n", encoding="utf-8")
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
                console_errors: list[str] = []
                page = browser.new_page()
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
                )
                page.goto(base_url, wait_until="domcontentloaded", timeout=10_000)
                page.wait_for_selector("#promptInput", state="visible", timeout=5_000)
                page.wait_for_selector("#sendBtn", state="visible", timeout=5_000)
                page.wait_for_function(
                    "() => document.querySelectorAll('#toolSelect option').length > 0",
                    timeout=5_000,
                )
                assert page.locator("#runtimeStatusStrip").count() == 1
                assert page.locator("#toolSelect option").count() > 0
                page.click("#composerMoreBtn")
                page.click("#composerSettingsBtn")
                page.wait_for_function("!document.querySelector('#settingsModal').hidden")
                page.click("#saveSettingsBtn")
                page.wait_for_function("document.querySelector('#settingsModal').hidden")
                page.fill("#promptInput", "find file README")
                page.click("#sendBtn")
                page.wait_for_selector(
                    'article.message:has-text("README.md") button[data-message-action="sources"]',
                    timeout=10_000,
                )
                page.wait_for_selector('#sidebarSessionHistory >> text="find file README"', timeout=5_000)
                page.locator('article.message:has-text("README.md") button[data-message-action="sources"]').last.click()
                page.wait_for_selector("#detailModal:not([hidden]) .source-card", timeout=5_000)
                page.click("#detailCloseBtn")
                page.locator('article.message:has-text("README.md") button[data-message-action="retry"]').last.click()
                page.wait_for_function("!document.querySelector('#retryDialog').hidden")
                page.click("#runRetryBtn")
                page.wait_for_selector(".variant-switcher", timeout=10_000)
                assert "2 of 2" in page.locator(".variant-switcher span").last.text_content()
                page.locator('.variant-switcher button[data-message-action="variant-prev"]').last.click()
                page.wait_for_function(
                    "document.querySelector('.variant-switcher span')?.textContent.includes('1 of 2')"
                )
                page.set_viewport_size({"width": 390, "height": 820})
                page.locator("#settingsBtn").click()
                page.wait_for_selector("#settingsModal:not([hidden])", timeout=5_000)
                page.locator("#closeSettingsBtn").click()
                page.locator("#sidebarToggleBtn").click()
                page.locator('.sidebar-page-link[data-page-target="help"]').click()
                page.wait_for_selector('.help-page.active #helpTopicNav', timeout=5_000)
                page.locator("#sidebarToggleBtn").click()
                page.locator('.sidebar-page-link[data-page-target="tools"]').click()
                page.wait_for_selector('.tools-page.active #toolSelect', timeout=5_000)
                page.locator("#sidebarToggleBtn").click()
                page.locator('.sidebar-page-link[data-page-target="chat"]').click()
                page.wait_for_selector("#promptInput", state="visible", timeout=5_000)
                page.locator("#composerMoreBtn").click()
                page.wait_for_selector("#composerMoreMenu:not([hidden])", timeout=5_000)
                page.locator("#composerResearchToggleBtn").click()
                page.wait_for_selector("#composerResearchRevealBtn:not([hidden])", timeout=5_000)
                page.locator("#composerResearchRevealBtn").click()
                page.wait_for_selector("#composerResearchMenu:not([hidden])", timeout=5_000)
                assert page_errors == []
                assert console_errors == []
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
