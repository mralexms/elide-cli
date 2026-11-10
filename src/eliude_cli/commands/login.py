from typing import Optional

import typer

from .. import config, prompts
from ..client import ApiClient, ApiError
from ..messages import t
from ..session import anonymous_client
from . import classrooms

# Wrong codes accepted in one `eliude login` before giving up.
_CODE_ATTEMPTS = 3


def open_menus_after_auth(choose) -> None:
    """Runs `choose` (the classroom/practice menus) right after a successful
    login, in a terminal. The command itself already succeeded, so a
    cancelled menu or a failure here must not turn it into a failed
    command — just point at `eliude switch`."""
    if not prompts.is_interactive():
        return
    try:
        choose()
    except typer.Exit as e:
        if e.exit_code:
            typer.echo(t("login.switch_later"))


def login(
    login_: Optional[str] = typer.Option(None, "--login", "-l", help=t("help.opt.login_login")),
    code: Optional[str] = typer.Option(None, "--code", "-c", help=t("help.opt.login_code")),
    no_email: bool = typer.Option(False, "--no-email", help=t("help.opt.login_no_email")),
) -> None:
    """Log in with a code sent to your email, and store an auth token locally."""
    if not login_:
        login_ = typer.prompt(t("prompt.login")).strip()
    client = anonymous_client()
    cli_code_url = f"{config.get_base_url()}/cli-code/"

    # A code given up front (or generated on the web, with --no-email) is
    # used as is; otherwise one is emailed now.
    if code is None and not no_email:
        try:
            sent = client.request_login_code(login_)
        except ApiError as e:
            message = t("login.email_unavailable", url=cli_code_url) if e.status == 503 else str(e)
            typer.secho(message, fg=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(t("login.code_sent", minutes=sent.get("minutes", 10)))
        typer.echo(t("login.code_from_web", url=cli_code_url))

    result = _verify(client, login_, code)
    if result is None:
        typer.echo(t("login.try_again", url=cli_code_url))
        raise typer.Exit(code=1)

    username = result.get("username") or login_
    config.set_token(result["token"], username)
    config.clear_active_classroom()
    typer.secho(t("login.logged_in_as", username=username), fg=typer.colors.GREEN)
    # Straight into choosing the classroom and practice, same as `eliude switch`.
    open_menus_after_auth(lambda: classrooms.switch(slug=None))


def _verify(client, login_: str, code: Optional[str]) -> Optional[dict]:
    """The server's {"token", "username"}, or None once the code was wrong
    too many times (just once for a code given with --code)."""
    attempts = 1 if code is not None else _CODE_ATTEMPTS
    for _ in range(attempts):
        typed = code if code is not None else typer.prompt(t("prompt.code"))
        try:
            return client.verify_login_code(login_, typed.strip())
        except ApiError as e:
            # 400 is the server's "invalid or expired code", whatever the cause.
            typer.secho(t("login.invalid_code") if e.status == 400 else str(e), fg=typer.colors.RED)
            if e.status != 400:
                return None
    return None


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
