from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.commands import update as update_cmd
from eliude_cli.main import app

runner = CliRunner()


def test_update_reports_already_up_to_date(cli_config, monkeypatch):
    monkeypatch.setattr(update_cmd, "_is_editable_install", lambda: False)
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "0.1.0", "download_url": "http://x/whl"}
    )
    monkeypatch.setattr(update_cmd, "installed_version_str", "0.1.0")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "up to date" in result.output.lower()


def test_update_runs_pip_install_when_outdated(cli_config, monkeypatch):
    monkeypatch.setattr(update_cmd, "_is_editable_install", lambda: False)
    monkeypatch.setattr(
        ApiClient,
        "get_latest_release",
        lambda self: {"version": "9.9.9", "download_url": "http://x/eliude_cli-9.9.9-py3-none-any.whl"},
    )
    monkeypatch.setattr(update_cmd, "installed_version_str", "0.1.0")

    calls = {}

    class FakeResult:
        returncode = 0

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return FakeResult()

    monkeypatch.setattr(update_cmd.subprocess, "run", fake_run)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert calls["cmd"][-1] == "http://x/eliude_cli-9.9.9-py3-none-any.whl"


def test_update_refuses_on_editable_install(cli_config, monkeypatch):
    monkeypatch.setattr(update_cmd, "_is_editable_install", lambda: True)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 1
    assert "editable" in result.output.lower() or "development" in result.output.lower()
