import typer

from . import config
from .client import ApiClient


def require_client() -> ApiClient:
    token = config.get_token()
    if not token:
        typer.secho("Not logged in. Run `eliude login` first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return ApiClient(config.get_base_url(), token=token)


def anonymous_client() -> ApiClient:
    return ApiClient(config.get_base_url())
