import pytest
import typer

from eliude_cli import version_check
from eliude_cli.client import ApiClient, ApiError

RELEASE = {"version": "0.2.0", "repo_url": "https://github.com/mralexms/elide-cli.git"}


class FakeContext:
    def __init__(self, invoked_subcommand, help_requested=False):
        self.invoked_subcommand = invoked_subcommand
        self.meta = {"eliude_help_requested": True} if help_requested else {}


def test_exempt_subcommand_skips_the_check(cli_config, monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: calls.append(1))
    version_check.check_version_compatibility(FakeContext("config"))
    assert calls == []


def test_bare_invocation_skips_the_check(cli_config, monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: calls.append(1))
    version_check.check_version_compatibility(FakeContext(None))
    assert calls == []


def test_help_requested_skips_the_check(cli_config, monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: calls.append(1))
    version_check.check_version_compatibility(FakeContext("submit", help_requested=True))
    assert calls == []


def test_matching_version_does_not_block(cli_config, monkeypatch):
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: RELEASE)
    monkeypatch.setattr(version_check, "installed_version_str", "0.2.0")
    version_check.check_version_compatibility(FakeContext("submit"))  # must not raise


def test_blocks_and_explains_when_server_requires_newer(cli_config, monkeypatch, capsys):
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: RELEASE)
    monkeypatch.setattr(version_check, "installed_version_str", "0.1.0")
    with pytest.raises(typer.Exit) as exc_info:
        version_check.check_version_compatibility(FakeContext("submit"))
    assert exc_info.value.exit_code == 1
    output = capsys.readouterr().out
    assert "requires eliude-cli 0.2.0" in output
    assert 'pipx install --force "git+https://github.com/mralexms/elide-cli.git@0.2.0"' in output


def test_blocks_and_explains_when_server_requires_older(cli_config, monkeypatch, capsys):
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: RELEASE)
    monkeypatch.setattr(version_check, "installed_version_str", "0.3.0")
    with pytest.raises(typer.Exit) as exc_info:
        version_check.check_version_compatibility(FakeContext("submit"))
    assert exc_info.value.exit_code == 1
    assert "expects an older eliude-cli (0.2.0)" in capsys.readouterr().out


def test_network_failure_fails_open(cli_config, monkeypatch):
    def raise_error(self):
        raise ApiError("offline")

    monkeypatch.setattr(ApiClient, "get_latest_release", raise_error)
    version_check.check_version_compatibility(FakeContext("submit"))  # must not raise/block


def test_malformed_release_fails_open(cli_config, monkeypatch):
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: {"repo_url": "https://x"})  # no "version"
    version_check.check_version_compatibility(FakeContext("submit"))  # must not raise/block


def test_invalid_version_fails_open(cli_config, monkeypatch):
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "not-a-version", "repo_url": "https://x"}
    )
    version_check.check_version_compatibility(FakeContext("submit"))  # must not raise/block
