import os
import subprocess

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


def test_non_json_release_response_fails_open(cli_config, monkeypatch):
    def raise_error(self):
        raise ValueError("Expecting value: line 1 column 1 (char 0)")

    monkeypatch.setattr(ApiClient, "get_latest_release", raise_error)
    version_check.check_version_compatibility(FakeContext("submit"))  # must not raise/block


TAG_RELEASE = {"version": "v0.2.0", "repo_url": version_check.REPO_URL}


@pytest.fixture
def pipx_install(monkeypatch, tmp_path):
    """Pretends to be a pipx install of an outdated CLI, at a terminal."""
    monkeypatch.setattr(ApiClient, "get_latest_release", lambda self: TAG_RELEASE)
    monkeypatch.setattr(version_check, "installed_version_str", "0.1.0")
    monkeypatch.setattr(version_check.prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(version_check.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(version_check.sys, "prefix", str(tmp_path / "pipx" / "venvs" / "eliude-cli"))
    monkeypatch.setattr(version_check.sys, "argv", ["/home/aluno/.local/bin/eliude", "submit", "q1"])
    monkeypatch.delenv(version_check._UPDATED_ENV, raising=False)
    state = {"confirms": [], "answer": True, "runs": [], "returncode": 0, "execs": []}

    def confirm(message, default=False):
        state["confirms"].append((message, default))
        return state["answer"]

    def run(cmd):
        state["runs"].append(cmd)
        return subprocess.CompletedProcess(cmd, state["returncode"])

    def execv(path, argv):
        state["execs"].append((path, argv, os.environ.get(version_check._UPDATED_ENV)))
        raise SystemExit(0)  # execv never returns

    monkeypatch.setattr(version_check.prompts, "confirm", confirm)
    monkeypatch.setattr(version_check.subprocess, "run", run)
    monkeypatch.setattr(version_check.os, "execv", execv)
    return state


def test_offers_update_and_reruns_the_command(cli_config, pipx_install):
    with pytest.raises(SystemExit):
        version_check.check_version_compatibility(FakeContext("submit"))
    assert pipx_install["confirms"] == [("Install eliude-cli 0.2.0 now?", True)]
    assert pipx_install["runs"] == [
        ["pipx", "install", "--force", "git+https://github.com/mralexms/elide-cli.git@v0.2.0"]
    ]
    assert pipx_install["execs"] == [
        ("/home/aluno/.local/bin/eliude", ["/home/aluno/.local/bin/eliude", "submit", "q1"], "1")
    ]


def test_declined_update_blocks_with_the_manual_command(cli_config, pipx_install, capsys):
    pipx_install["answer"] = False
    with pytest.raises(typer.Exit) as exc_info:
        version_check.check_version_compatibility(FakeContext("submit"))
    assert exc_info.value.exit_code == 1
    assert pipx_install["runs"] == []
    assert 'pipx install --force "git+https://github.com/mralexms/elide-cli.git@v0.2.0"' in capsys.readouterr().out


def test_failed_update_blocks_with_the_manual_command(cli_config, pipx_install, capsys):
    pipx_install["returncode"] = 1
    with pytest.raises(typer.Exit) as exc_info:
        version_check.check_version_compatibility(FakeContext("submit"))
    assert exc_info.value.exit_code == 1
    assert pipx_install["execs"] == []
    output = capsys.readouterr().out
    assert "The update failed" in output
    assert 'pipx install --force "git+https://github.com/mralexms/elide-cli.git@v0.2.0"' in output


@pytest.mark.parametrize(
    "setup",
    [
        pytest.param(lambda mp: mp.setattr(version_check.os, "name", "nt"), id="windows"),
        pytest.param(lambda mp: mp.setattr(version_check.prompts, "is_interactive", lambda: False), id="no-terminal"),
        pytest.param(lambda mp: mp.setattr(version_check.shutil, "which", lambda name: None), id="no-pipx"),
        pytest.param(lambda mp: mp.setattr(version_check.sys, "prefix", "/src/eliude-cli/.venv"), id="not-pipx-venv"),
        pytest.param(lambda mp: mp.setenv(version_check._UPDATED_ENV, "1"), id="just-updated"),
        pytest.param(
            lambda mp: mp.setattr(
                ApiClient, "get_latest_release", lambda self: {**TAG_RELEASE, "repo_url": "https://evil.example/x.git"}
            ),
            id="other-repo",
        ),
        pytest.param(
            lambda mp: mp.setattr(
                ApiClient, "get_latest_release", lambda self: {**TAG_RELEASE, "version": "0.2.0+main"}
            ),
            id="odd-tag",
        ),
    ],
)
def test_no_update_offer_when_unsafe(cli_config, pipx_install, monkeypatch, setup):
    setup(monkeypatch)
    with pytest.raises(typer.Exit):
        version_check.check_version_compatibility(FakeContext("submit"))
    assert pipx_install["confirms"] == []
    assert pipx_install["runs"] == []
