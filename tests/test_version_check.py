import time

from eliude_cli import version_check
from eliude_cli.client import ApiClient, ApiError


def test_skips_network_call_within_a_day(cli_config, monkeypatch):
    cli_config.set_last_version_check(time.time())
    calls = []
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: calls.append(1))
    version_check.maybe_warn_outdated()
    assert calls == []


def test_warns_when_outdated(cli_config, monkeypatch, capsys):
    cli_config.set_last_version_check(0)
    monkeypatch.setattr(
        ApiClient,
        "get_latest_release",
        lambda self: {"version": "999.0.0", "download_url": "http://x/eliude_cli-999.0.0-py3-none-any.whl"},
    )
    monkeypatch.setattr(version_check, "installed_version_str", "0.1.0")
    version_check.maybe_warn_outdated()
    assert "new version" in capsys.readouterr().out.lower()
    assert cli_config.get_last_version_check() is not None


def test_network_failure_is_silent(cli_config, monkeypatch):
    cli_config.set_last_version_check(0)

    def raise_error(self):
        raise ApiError("offline")

    monkeypatch.setattr(ApiClient, "get_latest_release", raise_error)
    version_check.maybe_warn_outdated()  # must not raise
    assert cli_config.get_last_version_check() is not None
