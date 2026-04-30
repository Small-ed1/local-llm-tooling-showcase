from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen
import json
import shutil
import sys

from tooling_showcase import __version__
from tooling_showcase.config import ShowcaseConfig


def run_doctor(config: ShowcaseConfig, *, json_output: bool = False) -> int:
    checks = collect_doctor_checks(config)
    if json_output:
        print(json.dumps({"ok": _overall_ok(checks), "version": __version__, "checks": checks}, indent=2, sort_keys=True))
    else:
        print(f"tooling-showcase doctor {__version__}")
        for check in checks:
            marker = {"ok": "OK", "warn": "WARN", "error": "ERROR"}[check["status"]]
            print(f"[{marker}] {check['name']}: {check['detail']}")
    return 0 if _overall_ok(checks) else 1


def collect_doctor_checks(config: ShowcaseConfig) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    checks.append(_check(sys.version_info >= (3, 11), "python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "Python 3.11+ required"))
    checks.append(_path_check("project_root", config.project_root, must_be_dir=True))
    checks.append(_path_check("workspace_root", config.workspace_root, must_be_dir=True))
    checks.append(_path_check("portfolio_root", config.portfolio_root, must_be_dir=True))
    static_dir = Path(__file__).with_name("static")
    checks.append(_path_check("static_ui", static_dir / "index.html"))
    checks.append(_path_check("frontend_js", static_dir / "app.js"))
    checks.append(_path_check("install_script", config.project_root / "install.sh", required=False))
    checks.append(_path_check("start_servers_script", config.project_root / "start-servers.sh", required=False))
    checks.append(_writable_parent_check("journal_parent", config.journal_path.parent))
    if config.benchmark_path is not None:
        checks.append(_writable_parent_check("benchmark_parent", config.benchmark_path.parent))
    checks.append(_command_check("node", required=False))
    checks.append(_ollama_check(config))
    return checks


def _overall_ok(checks: list[dict[str, str]]) -> bool:
    return all(check["status"] != "error" for check in checks)


def _check(ok: bool, name: str, detail: str, error_detail: str) -> dict[str, str]:
    return {"name": name, "status": "ok" if ok else "error", "detail": detail if ok else error_detail}


def _path_check(name: str, path: Path, *, must_be_dir: bool = False, required: bool = True) -> dict[str, str]:
    exists = path.is_dir() if must_be_dir else path.exists()
    missing_status = "error" if required else "warn"
    return {"name": name, "status": "ok" if exists else missing_status, "detail": str(path) if exists else f"missing: {path}"}


def _writable_parent_check(name: str, path: Path) -> dict[str, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {"name": name, "status": "error", "detail": f"cannot create {path}: {exc}"}
    return {"name": name, "status": "ok" if path.is_dir() else "error", "detail": str(path)}


def _command_check(command: str, *, required: bool) -> dict[str, str]:
    found = shutil.which(command)
    if found:
        return {"name": command, "status": "ok", "detail": found}
    return {"name": command, "status": "error" if required else "warn", "detail": f"{command} not found"}


def _ollama_check(config: ShowcaseConfig) -> dict[str, str]:
    if not config.ollama.enabled:
        return {"name": "ollama", "status": "warn", "detail": "disabled by TOOLING_SHOWCASE_OLLAMA_ENABLED"}
    tags_url = _ollama_tags_url(config.ollama.endpoint)
    try:
        with urlopen(tags_url, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return {"name": "ollama", "status": "warn", "detail": f"HTTP {exc.code} from {tags_url}"}
    except (URLError, TimeoutError, OSError) as exc:
        return {"name": "ollama", "status": "warn", "detail": f"unavailable at {tags_url}: {exc}"}
    except json.JSONDecodeError as exc:
        return {"name": "ollama", "status": "warn", "detail": f"invalid JSON from {tags_url}: {exc}"}
    models = data.get("models", []) if isinstance(data, dict) else []
    return {"name": "ollama", "status": "ok", "detail": f"{len(models)} model(s) from {tags_url}"}


def _ollama_tags_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return "http://127.0.0.1:11434/api/tags"
    return f"{parsed.scheme}://{parsed.netloc}/api/tags"
