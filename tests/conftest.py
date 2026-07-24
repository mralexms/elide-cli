import pytest

from eliude_cli import config


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
