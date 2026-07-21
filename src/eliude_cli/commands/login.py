import typer

from .. import config
from ..client import ApiError
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
    typer.secho(f"Logged in as {username}.", fg=typer.colors.GREEN)


def logout() -> None:
    """Clear the locally stored auth token."""
    config.clear_token()
    typer.echo("Logged out.")
