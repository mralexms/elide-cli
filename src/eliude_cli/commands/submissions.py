import typer

from ..client import ApiError
from ..formatting import print_submission_result
from ..session import require_client


def status(submission_id: int) -> None:
    """Check the status/result of a previous submission."""
    client = require_client()
    try:
        result = client.get_submission(submission_id)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    print_submission_result(result)
