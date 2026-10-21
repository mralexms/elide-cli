import typer

from .. import config, prompts
from ..client import ApiClient, ApiError
from ..messages import t
from ..session import anonymous_client
from . import change_password, classrooms

# Tries before giving up and pointing at `eliude change-password`.
_NEW_PASSWORD_ATTEMPTS = 3


def open_menus_after_auth(choose) -> None:
    """Runs `choose` (the classroom/practice menus) right after a successful
    login, in a terminal. The command itself already succeeded, so a
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
        result = client.login(username, password)
    except ApiError as e:
        # 400 is the server's "Unable to log in with provided credentials".
        typer.secho(t("login.invalid_credentials") if e.status == 400 else str(e), fg=typer.colors.RED)
        # Accounts are created on the web (e.g. via Google), with no password
        # until the user sets one there.
        typer.echo(t("login.create_password_hint", url=f"{config.get_base_url()}/password/"))
        raise typer.Exit(code=1)
    config.set_token(result["token"], username)
    config.clear_active_classroom()
    typer.secho(t("login.logged_in_as", username=username), fg=typer.colors.GREEN)
    # Until it's changed, the server refuses everything else (403), menus included.
    if result.get("must_change_password") and not _replace_temporary_password(password):
        return
    # Straight into choosing the classroom and practice, same as `eliude switch`.
    open_menus_after_auth(lambda: classrooms.switch(slug=None))


def _replace_temporary_password(current_password: str) -> bool:
    typer.secho(t("login.temporary_password"), fg=typer.colors.YELLOW)
    if prompts.is_interactive():
        for _ in range(_NEW_PASSWORD_ATTEMPTS):
            new_password = typer.prompt(t("prompt.new_password"), hide_input=True)
            new_password_confirm = typer.prompt(t("prompt.confirm_new_password"), hide_input=True)
            if change_password.apply_new_password(current_password, new_password, new_password_confirm):
                return True
    typer.echo(t("login.change_password_later"))
    return False


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
