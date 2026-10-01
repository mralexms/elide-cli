import typer

from ..client import ApiError
from ..messages import t
from ..session import require_client


def change_password(
    current_password: str = typer.Option(..., prompt=t("prompt.current_password"), hide_input=True),
    new_password: str = typer.Option(..., prompt=t("prompt.new_password"), hide_input=True),
    new_password_confirm: str = typer.Option(..., prompt=t("prompt.confirm_new_password"), hide_input=True),
) -> None:
    """Set a new password — required if you're still on a temporary one your teacher set."""
    if new_password != new_password_confirm:
        typer.secho(t("change_password.mismatch"), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    client = require_client()
    try:
        client.change_password(current_password, new_password, new_password_confirm)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(t("change_password.success"), fg=typer.colors.GREEN)
