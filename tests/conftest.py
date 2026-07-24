import pytest

from eliude_cli import config
from eliude_cli.client import ApiClient


@pytest.fixture
def cli_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".eliude"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_dir / "config.json")
    return config


@pytest.fixture(autouse=True)
def _skip_version_check(monkeypatch):
    # Commands invoked through CliRunner shouldn't trigger real network calls
    # via the root callback. Patched at the main.py call site (not on
    # version_check itself) so tests that exercise version_check directly
    # are unaffected.
    monkeypatch.setattr("eliude_cli.main.check_version_compatibility", lambda ctx: None)


@pytest.fixture(autouse=True)
def _stub_server_health(monkeypatch):
    # `eliude status` pings /api/health/ unauthenticated; stub it so tests
    # not concerned with that behavior don't make a real network call.
    # Tests exercising it directly can still override via monkeypatch.
    monkeypatch.setattr(ApiClient, "get_health", lambda self: {"status": "ok", "version": "0.0.0-test"})
