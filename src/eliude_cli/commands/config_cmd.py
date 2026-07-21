import typer

from .. import config


def set_url(base_url: str) -> None:
    """Point the CLI at a different Eliude backend."""
    config.set_base_url(base_url)
    typer.echo(f"Base URL set to {base_url}")
