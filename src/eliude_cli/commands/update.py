import subprocess
import sys
from importlib.metadata import PackageNotFoundError, distribution

import typer
from packaging.version import InvalidVersion, Version

from .. import __version__ as installed_version_str
from ..client import ApiError
from ..session import anonymous_client


def _is_editable_install() -> bool:
    try:
        dist = distribution("eliude-cli")
        direct_url_text = dist.read_text("direct_url.json")
    except (PackageNotFoundError, FileNotFoundError):
        return False
    return bool(direct_url_text) and '"editable": true' in direct_url_text


def update() -> None:
    """Upgrade the installed eliude CLI to the latest published version."""
    if _is_editable_install():
        typer.secho(
            "This is a development (editable) install of eliude-cli. `eliude update` would "
            "overwrite it with a built wheel. Run `git pull` in the cli/ project instead.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)

    try:
        release = anonymous_client().get_latest_release()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        latest = Version(release["version"])
    except InvalidVersion:
        typer.secho(f"Server reported an invalid version: {release['version']!r}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    installed = Version(installed_version_str)

    if latest <= installed:
        typer.secho(f"Already up to date (version {installed}).", fg=typer.colors.GREEN)
        return

    typer.echo(f"Upgrading eliude-cli {installed} -> {latest} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", release["download_url"]],
    )
    if result.returncode != 0:
        typer.secho("Upgrade failed. See the pip output above for details.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Upgraded to eliude-cli {latest}.", fg=typer.colors.GREEN)
