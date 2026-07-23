import typer

from . import __version__
from .commands import classrooms, config_cmd, get, login, practices, questions, status, submissions, submit, update
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
app.command(name="show")(questions.show_question)

classrooms_app = typer.Typer(help="Manage your classrooms")
classrooms_app.command("list")(classrooms.list_classrooms)
app.add_typer(classrooms_app, name="classrooms")

practices_app = typer.Typer(help="Manage practices in the active classroom")


@practices_app.callback(invoke_without_command=True)
def practices_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        practices.list_practices()
        raise typer.Exit()


practices_app.command("list")(practices.list_practices)
practices_app.command("switch")(practices.switch)
app.add_typer(practices_app, name="practices")

questions_app = typer.Typer(help="Browse the active practice's questions")


@questions_app.callback(invoke_without_command=True)
def questions_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        questions.list_questions(show_timestamp=False, unsolved=False)
        raise typer.Exit()


questions_app.command("list")(questions.list_questions)
questions_app.command("show")(questions.show_question)
app.add_typer(questions_app, name="questions")

submissions_app = typer.Typer(help="Check submission results")
submissions_app.command("status")(submissions.status)
app.add_typer(submissions_app, name="submissions")

config_app = typer.Typer(help="CLI configuration")
config_app.command("set-url")(config_cmd.set_url)
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
