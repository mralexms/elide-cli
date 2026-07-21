import typer

from . import __version__
from .commands import classrooms, config_cmd, exercises, get, login, status, submissions, submit, update
from .version_check import maybe_warn_outdated

app = typer.Typer(name="eliude", help="CLI for the Eliude C programming judge")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    maybe_warn_outdated()
    if ctx.invoked_subcommand is None:
        typer.echo(f"eliude {__version__}")
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.command(name="login")(login.login)
app.command(name="logout")(login.logout)
app.command(name="submit")(submit.submit)
app.command(name="switch")(classrooms.switch)
app.command(name="update")(update.update)
app.command(name="get")(get.get)
app.command(name="status")(status.status)
app.command(name="show")(exercises.show_exercise)

classrooms_app = typer.Typer(help="Manage your classrooms")
classrooms_app.command("list")(classrooms.list_classrooms)
app.add_typer(classrooms_app, name="classrooms")

exercises_app = typer.Typer(help="Browse exercises")
exercises_app.command("list")(exercises.list_exercises)
exercises_app.command("show")(exercises.show_exercise)
app.add_typer(exercises_app, name="exercises")

submissions_app = typer.Typer(help="Check submission results")
submissions_app.command("status")(submissions.status)
app.add_typer(submissions_app, name="submissions")

config_app = typer.Typer(help="CLI configuration")
config_app.command("set-url")(config_cmd.set_url)
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
