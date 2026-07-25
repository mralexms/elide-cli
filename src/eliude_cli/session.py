import typer

from . import config
from .client import ApiClient
from .messages import t


def require_client() -> ApiClient:
    token = config.get_token()
    if not token:
        typer.secho(t("session.not_logged_in"), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return ApiClient(config.get_base_url(), token=token, classroom=config.get_active_classroom())


def require_classroom_client() -> ApiClient:
    client = require_client()
    if not config.get_active_classroom():
        typer.secho(t("session.no_active_classroom"), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return client


def require_practice_client() -> ApiClient:
    require_classroom_client()
    if not config.get_active_practice():
        typer.secho(t("session.no_active_practice"), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return ApiClient(
        config.get_base_url(),
        token=config.get_token(),
        classroom=config.get_active_classroom(),
        practice=config.get_active_practice(),
    )


def anonymous_client() -> ApiClient:
    return ApiClient(config.get_base_url())
