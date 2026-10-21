import typer

from ..client import ApiError
from ..messages import t
from ..session import require_client


def apply_new_password(current_password: str, new_password: str, new_password_confirm: str) -> bool:
    """Sends the new password, printing why it was refused if it was. Also
    used by `eliude login` when the account is on a temporary password."""
    if new_password != new_password_confirm:
        typer.secho(t("change_password.mismatch"), fg=typer.colors.RED)
        return False

    client = require_client()
    try:
        client.change_password(current_password, new_password, new_password_confirm)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        return False

    typer.secho(t("change_password.success"), fg=typer.colors.GREEN)
    return True


def change_password(
    current_password: str = typer.Option(..., prompt=t("prompt.current_password"), hide_input=True),
    new_password: str = typer.Option(..., prompt=t("prompt.new_password"), hide_input=True),
    new_password_confirm: str = typer.Option(..., prompt=t("prompt.confirm_new_password"), hide_input=True),
) -> None:
    """Set a new password — required if you're still on a temporary one your teacher set."""
    if not apply_new_password(current_password, new_password, new_password_confirm):
        raise typer.Exit(code=1)
