import typer

from .. import config
from ..client import ApiClient, ApiError
from ..session import anonymous_client


def login(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Log in and store an auth token locally."""
    client = anonymous_client()
    try:
        token = client.login(username, password)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    config.set_token(token, username)
    config.clear_active_classroom()
    typer.secho(f"Logged in as {username}.", fg=typer.colors.GREEN)


def logout() -> None:
    """Clear the locally stored auth token."""
    token = config.get_token()
    if token:
        try:
            ApiClient(config.get_base_url(), token=token).logout()
        except ApiError:
            pass  # best-effort: still clear local state below even if offline
    config.clear_token()
    config.clear_active_classroom()
    typer.echo("Logged out.")
