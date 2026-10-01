from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_plugin_module():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("mnemosyne_dashboard_plugin_test", root / "__init__.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_status_reports_reachable_when_pid_file_is_stale(tmp_path, monkeypatch):
    mod = load_plugin_module()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    cfg = mod.save_config(host="0.0.0.0", port=8765, db_path=str(tmp_path / "mnemosyne.db"), auth_enabled=True, password="secret")
    mod._pid_file().write_text("999999")
    mod._write_runtime(999999, cfg, tmp_path / "server.log")
    monkeypatch.setattr(mod, "_alive", lambda pid: False)
    monkeypatch.setattr(mod, "_reachable_detail", lambda cfg, timeout=2: {"ok": True, "status": 200, "url": cfg.local_url + "api/auth/status", "error": ""})
    monkeypatch.setattr(mod, "_listener_pids", lambda port: [1234])

    payload = json.loads(mod._status({}))

    assert payload["running"] is True
    assert payload["reachable"] is True
    assert payload["stale_pid"] is True
    assert payload["pid"] == 1234
    assert payload["pid_file_pid"] == 999999
    assert payload["probe"]["status"] == 200


def test_start_repairs_stale_pid_instead_of_spawning_duplicate(tmp_path, monkeypatch):
    mod = load_plugin_module()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    db = tmp_path / "mnemosyne.db"
    db.write_text("")
    mod.save_config(host="0.0.0.0", port=8765, db_path=str(db))
    mod._pid_file().write_text("999999")
    monkeypatch.setattr(mod, "_alive", lambda pid: False)
    monkeypatch.setattr(mod, "_reachable_detail", lambda cfg, timeout=2: {"ok": True, "status": 200, "url": cfg.local_url + "api/auth/status", "error": ""})
    monkeypatch.setattr(mod, "_listener_pids", lambda port: [4321])

    class ForbiddenPopen:
        def __init__(self, *args, **kwargs):
            raise AssertionError("should not spawn duplicate server when port is reachable")
    monkeypatch.setattr(mod.subprocess, "Popen", ForbiddenPopen)

    payload = json.loads(mod._start({}))

    assert payload["ok"] is True
    assert payload["already_running"] is True
    assert payload["stale_pid_repaired"] is True
    assert payload["pid"] == 4321
    assert mod._pid_file().read_text().strip() == "4321"
    repaired_runtime = json.loads(mod._runtime_file().read_text())
    assert repaired_runtime["pid"] == 4321
    assert repaired_runtime["source"] == "plugin-start-repair"


def test_server_writes_runtime_metadata_for_launchd_starts(tmp_path, monkeypatch):
    import server as dashboard_server
    from config import effective_config

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    cfg = effective_config({"host": "0.0.0.0", "port": 8765, "db_path": str(tmp_path / "mnemosyne.db")})

    dashboard_server._write_runtime_metadata(cfg)

    root = tmp_path / "hermes" / "plugin-data" / "mnemosyne-dashboard"
    assert (root / "server.pid").read_text().strip().isdigit()
    runtime = json.loads((root / "runtime.json").read_text())
    assert runtime["source"] == "server.py"
    assert runtime["local_url"] == "http://127.0.0.1:8765/"
    assert runtime["db_path"] == str(tmp_path / "mnemosyne.db")

    status = dashboard_server._runtime_status(cfg)
    assert status["ok"] is True
    assert status["running"] is True
    assert status["reachable"] is True
    assert status["pid"] == runtime["pid"]
    assert status["runtime_source"] == "server.py"
    assert status["probe"]["url"] == "http://127.0.0.1:8765/api/auth/status"
