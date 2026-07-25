import os
import subprocess
import sys

import pytest


def _run_help(*args, language, tmp_path):
    env = {
        **os.environ,
        "ELIUDE_CONFIG_DIR": str(tmp_path),
        "ELIUDE_LANGUAGE": language,
        # A subcommand's own --help still runs the root's version-compatibility
        # check first (see main.py/version_check.py) — point at an address
        # nothing answers so that check fails open quickly and deterministically,
        # regardless of whether a real backend happens to be running locally.
        "ELIUDE_BASE_URL": "http://127.0.0.1:1",
    }
    result = subprocess.run(
        [sys.executable, "-m", "eliude_cli.main", *args, "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    return result.stdout


@pytest.mark.parametrize(
    "args,en_snippet,pt_snippet",
    [
        ([], "CLI for the Eliude C programming judge", "CLI para o corretor de exercícios de C Eliude"),
        (["classrooms"], "Manage your classrooms", "Gerencie suas turmas"),
        (["config"], "CLI configuration", "Configuração do CLI"),
        (["show"], "sample test cases", "casos de teste de amostra"),
    ],
)
def test_help_text_is_translated(args, en_snippet, pt_snippet, tmp_path):
    en_output = _run_help(*args, language="en", tmp_path=tmp_path / "en")
    pt_output = _run_help(*args, language="pt-BR", tmp_path=tmp_path / "pt")

    assert en_snippet in en_output
    assert pt_snippet in pt_output
    assert en_snippet not in pt_output
    assert pt_snippet not in en_output


def test_help_chrome_stays_english_regardless_of_language(tmp_path):
    # "Usage:"/"Options"/"Commands" come from Click/Typer itself — out of
    # scope (see plan), so both languages should show them identically.
    en_output = _run_help(language="en", tmp_path=tmp_path / "en")
    pt_output = _run_help(language="pt-BR", tmp_path=tmp_path / "pt")

    for chrome in ("Usage:", "Options", "Commands"):
        assert chrome in en_output
        assert chrome in pt_output
