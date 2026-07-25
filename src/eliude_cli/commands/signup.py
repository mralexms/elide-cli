import typer

from .. import config
from ..client import ApiError
from ..session import anonymous_client


def signup(
    name: str = typer.Option(..., prompt="Full name"),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    password_confirm: str = typer.Option(..., prompt="Confirm password", hide_input=True),
    classroom_code: str = typer.Option(..., prompt="Classroom code"),
) -> None:
    """Self-register as a student using a classroom join code, and log in."""
    if password != password_confirm:
        typer.secho("Passwords don't match.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    client = anonymous_client()
    try:
        result = client.signup(name, email, password, password_confirm, classroom_code)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config.set_token(result["token"], email)
    classroom = result["classroom"]
    config.set_active_classroom(classroom["slug"])
    config.clear_active_practice()
    typer.secho(
        f"Welcome, {name}! Joined classroom '{classroom['name']}' ({classroom['slug']}).", fg=typer.colors.GREEN
    )
