import time

import typer
from packaging.version import InvalidVersion, Version

from . import __version__ as installed_version_str
from . import config
from .client import ApiError
from .session import anonymous_client

CHECK_INTERVAL_SECONDS = 24 * 60 * 60


def maybe_warn_outdated() -> None:
    last_check = config.get_last_version_check()
    now = time.time()
    if last_check is not None and (now - last_check) < CHECK_INTERVAL_SECONDS:
        return

    try:
        _warn_if_outdated()
    except Exception:
        # A background version check must never break a real command.
        pass
    finally:
        config.set_last_version_check(now)


def _warn_if_outdated() -> None:
    try:
        release = anonymous_client().get_latest_release()
        latest = Version(release["version"])
        installed = Version(installed_version_str)
    except (ApiError, KeyError, InvalidVersion):
        return

    if latest > installed:
        typer.secho(
            f"A new version of eliude-cli is available: {latest} (you have {installed}). "
            "Run `eliude update` to upgrade.",
            fg=typer.colors.YELLOW,
        )
