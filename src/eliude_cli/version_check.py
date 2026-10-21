import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from packaging.version import InvalidVersion, Version

from . import __version__ as installed_version_str
from . import prompts
from .client import ApiError
from .messages import t
from .session import anonymous_client

# Commands that must keep working even when the installed CLI is
# incompatible with the configured server — otherwise a wrong base_url (or
# an unreachable/misconfigured server) would leave the user with no way to
# fix their own setup.
EXEMPT_SUBCOMMANDS = {"config"}

# The only repo the CLI will ever install itself from. Fixed here rather
# than taken from the server's repo_url: otherwise whoever controls a server
# could make every student's machine install code from anywhere.
REPO_URL = "https://github.com/mralexms/elide-cli.git"

# Only plain version tags (v0.4.0, 0.4.0) go into the git ref we install.
_VERSION_TAG = re.compile(r"v?\d+(\.\d+)*")

# Set on the re-executed command after an update, so a server that keeps
# declaring a version we can't reach doesn't turn into an update loop.
_UPDATED_ENV = "ELIUDE_JUST_UPDATED"


def check_version_compatibility(ctx: typer.Context) -> None:
    """Confirms the installed CLI version matches exactly what the
    configured server declares (see cli_releases on the backend). Runs on
    every invocation — there's no daily throttle, since a mismatch can
    change the moment a school upgrades or rolls back their server.

    Fails **closed** (blocks the command) only on a confirmed mismatch.
    Fails **open** (lets the command run normally) if the check itself
    can't be completed — server unreachable, no release published, or a
    malformed version — since those are infra problems, not confirmed
    incompatibility, and must never brick the CLI.

    On a mismatch, offers to install the right version when it can (see
    _can_self_update) and, if the user agrees, runs the command again on
    it. The CLI never changes itself without that confirmation.

    Also skipped whenever `--help` was requested anywhere in the command
    line (see HelpOnInvalidCommandGroup.resolve_command in main.py) —
    --help must never depend on network access, at any nesting depth.
    """
    if ctx.invoked_subcommand is None or ctx.invoked_subcommand in EXEMPT_SUBCOMMANDS:
        return
    if ctx.meta.get("eliude_help_requested"):
        return

    try:
        release = anonymous_client().get_latest_release()
        required = Version(release["version"])
        installed = Version(installed_version_str)
    # ValueError: a non-JSON body (e.g. an HTML error page from a proxy).
    except (ApiError, KeyError, InvalidVersion, ValueError):
        return

    if required == installed:
        return

    reinstall_command = f'pipx install --force "git+{release["repo_url"]}@{release["version"]}"'
    if required > installed:
        reason = t("version.requires_newer", required=required, installed=installed)
    else:
        reason = t("version.requires_older", required=required, installed=installed)

    typer.secho(reason, fg=typer.colors.RED)
    if _can_self_update(release) and prompts.confirm(t("version.update_prompt", required=required), default=True):
        _self_update(release["version"])
    typer.echo(f"\n  {reinstall_command}\n")
    raise typer.Exit(code=1)


def _can_self_update(release: dict) -> bool:
    """Only offered when it's safe to do it unattended: someone at a
    terminal to confirm, a pipx install (not an editable/dev one) with pipx
    and git around, and a server pointing at our own repo. Not on Windows,
    where the running CLI's files are locked and `pipx install --force`
    fails halfway through."""
    if os.environ.get(_UPDATED_ENV) or os.name == "nt" or not prompts.is_interactive():
        return False
    if release.get("repo_url") != REPO_URL or not _VERSION_TAG.fullmatch(str(release["version"])):
        return False
    if shutil.which("pipx") is None or shutil.which("git") is None:
        return False
    # pipx keeps each app in its own venv at <PIPX_HOME>/venvs/<package>.
    prefix = Path(sys.prefix)
    return prefix.name == "eliude-cli" and prefix.parent.name == "venvs"


def _self_update(tag: str) -> None:
    """Installs `tag` with pipx and re-runs the user's command on it. Only
    returns if the install failed (the caller then shows the manual
    command)."""
    typer.echo(t("version.updating", tag=tag))
    result = subprocess.run(["pipx", "install", "--force", f"git+{REPO_URL}@{tag}"])
    if result.returncode != 0:
        typer.secho(t("version.update_failed"), fg=typer.colors.RED)
        return

    typer.secho(t("version.updated"), fg=typer.colors.GREEN)
    sys.stdout.flush()
    os.environ[_UPDATED_ENV] = "1"
    # The shebang made argv[0] the full path to the pipx-installed script,
    # which now points at the new version.
    if os.path.isabs(sys.argv[0]):
        os.execv(sys.argv[0], sys.argv)
    os.execvp("eliude", ["eliude", *sys.argv[1:]])
