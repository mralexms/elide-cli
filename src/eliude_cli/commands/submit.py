from pathlib import Path

import typer

from ..client import ApiError
from ..formatting import print_submission_result
from ..session import require_client


def submit(slug: str, file: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Submit a C solution for an exercise."""
    client = require_client()
    source_code = file.read_text()
    try:
        result = client.submit(slug, source_code)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    print_submission_result(result)
    if result["status"] not in ("passed",):
        raise typer.Exit(code=1)
