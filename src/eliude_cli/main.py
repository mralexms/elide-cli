import typer
from typer.core import TyperGroup

from . import __version__
from .commands import classrooms, config_cmd, get, login, practices, questions, signup, status, submissions, submit
from .version_check import check_version_compatibility


class HelpOnInvalidCommandGroup(TyperGroup):
    """On an unknown subcommand, show this group's help instead of a generic usage error."""

    def resolve_command(self, ctx: typer.Context, args: list[str]):
        cmd = self.get_command(ctx, args[0])
        if cmd is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=2)
        return args[0], cmd, args[1:]


app = typer.Typer(name="eliude", help="CLI for the Eliude C programming judge", cls=HelpOnInvalidCommandGroup)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"eliude {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show the version and exit."
    ),
) -> None:
    check_version_compatibility(ctx)
    if ctx.invoked_subcommand is None:
        typer.echo(f"eliude {__version__}")
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.command(name="login")(login.login)
app.command(name="logout")(login.logout)
app.command(name="signup")(signup.signup)
app.command(name="submit")(submit.submit)
app.command(name="switch")(classrooms.switch)
app.command(name="get")(get.get)
app.command(name="status")(status.status)
app.command(name="show")(questions.show_question)

classrooms_app = typer.Typer(help="Manage your classrooms", cls=HelpOnInvalidCommandGroup)
classrooms_app.command("list")(classrooms.list_classrooms)
app.add_typer(classrooms_app, name="classrooms")

practices_app = typer.Typer(help="Manage practices in the active classroom", cls=HelpOnInvalidCommandGroup)


@practices_app.callback(invoke_without_command=True)
def practices_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        practices.list_practices()
        raise typer.Exit()


practices_app.command("list")(practices.list_practices)
practices_app.command("switch")(practices.switch)
app.add_typer(practices_app, name="practices")

questions_app = typer.Typer(help="Browse the active practice's questions", cls=HelpOnInvalidCommandGroup)


@questions_app.callback(invoke_without_command=True)
def questions_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        questions.list_questions(show_timestamp=False, unsolved=False)
        raise typer.Exit()


questions_app.command("list")(questions.list_questions)
questions_app.command("show")(questions.show_question)
app.add_typer(questions_app, name="questions")

submissions_app = typer.Typer(help="Check submission results", cls=HelpOnInvalidCommandGroup)
submissions_app.command("status")(submissions.status)
app.add_typer(submissions_app, name="submissions")

config_app = typer.Typer(help="CLI configuration", cls=HelpOnInvalidCommandGroup)
config_app.command("set-url")(config_cmd.set_url)
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
