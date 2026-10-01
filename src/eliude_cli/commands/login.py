import typer

from .. import config, prompts
from ..client import ApiClient, ApiError
from ..messages import t
from ..session import anonymous_client
from . import classrooms


def open_menus_after_auth(choose) -> None:
    """Runs `choose` (the classroom/practice menus) right after a successful
    login/signup, in a terminal. The command itself already succeeded, so a
    cancelled menu or a failure here (e.g. 403 while still on a temporary
    password) must not turn it into a failed command — just point at
    `eliude switch`."""
    if not prompts.is_interactive():
        return
    try:
        choose()
    except typer.Exit as e:
        if e.exit_code:
            typer.echo(t("login.switch_later"))


def login(
    username: str = typer.Option(..., prompt=t("prompt.username")),
    password: str = typer.Option(..., prompt=t("prompt.password"), hide_input=True),
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
    typer.secho(t("login.logged_in_as", username=username), fg=typer.colors.GREEN)
    # Straight into choosing the classroom and practice, same as `eliude switch`.
    open_menus_after_auth(lambda: classrooms.switch(slug=None))


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
    typer.echo(t("login.logged_out"))
