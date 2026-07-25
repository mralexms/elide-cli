import typer

from .. import config
from ..messages import t


def set_url(base_url: str) -> None:
    """Point the CLI at a different Eliude backend."""
    config.set_base_url(base_url)
    typer.echo(t("config.base_url_set", url=base_url))


def set_language(
    language: str = typer.Argument(..., help=t("help.arg.config_set_language")),
) -> None:
    """Set the language eliude's messages are shown in."""
    resolved = config.resolve_language_alias(language)
    if resolved is None:
        typer.secho(
            t("config.unsupported_language", language=language, supported=", ".join(config.SUPPORTED_LANGUAGES)),
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    config.set_language(resolved)
    typer.echo(t("config.language_set", language=resolved))
