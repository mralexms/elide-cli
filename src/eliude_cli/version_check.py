import typer
from packaging.version import InvalidVersion, Version

from . import __version__ as installed_version_str
from .client import ApiError
from .session import anonymous_client

# Commands that must keep working even when the installed CLI is
# incompatible with the configured server — otherwise a wrong base_url (or
# an unreachable/misconfigured server) would leave the user with no way to
# fix their own setup.
EXEMPT_SUBCOMMANDS = {"config"}


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
    """
    if ctx.invoked_subcommand is None or ctx.invoked_subcommand in EXEMPT_SUBCOMMANDS:
        return

    try:
        release = anonymous_client().get_latest_release()
        required = Version(release["version"])
        installed = Version(installed_version_str)
    except (ApiError, KeyError, InvalidVersion):
        return

    if required == installed:
        return

    reinstall_command = f'pipx install --force "git+{release["repo_url"]}@{release["version"]}"'
    if required > installed:
        reason = f"This server requires eliude-cli {required}, but you have {installed} installed."
    else:
        reason = f"This server expects an older eliude-cli ({required}); you have {installed} installed."

    typer.secho(reason, fg=typer.colors.RED)
    typer.echo(f"\n  {reinstall_command}\n")
    raise typer.Exit(code=1)
