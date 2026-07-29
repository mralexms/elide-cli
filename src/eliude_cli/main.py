import typer
from typer.core import TyperGroup

from . import __version__
from .commands import (
    change_password,
    classrooms,
    config_cmd,
    get,
    login,
    practices,
    questions,
    signup,
    status,
    submissions,
    submit,
)
from .messages import t
from .version_check import check_version_compatibility


class HelpOnInvalidCommandGroup(TyperGroup):
    """On an unknown subcommand, show this group's help instead of a generic usage error."""

    def resolve_command(self, ctx: typer.Context, args: list[str]):
        cmd = self.get_command(ctx, args[0])
        if cmd is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=2)
        # A subcommand's own --help is parsed after this group's callback
        # (main_callback, below) already ran — so `eliude <cmd> --help`
        # would otherwise still trigger a live version-compatibility check
        # first. ctx.meta is shared across the whole context chain, so
        # setting it here (root level sees the full remaining args, even
        # for nested groups) is visible from main_callback regardless of
        # nesting depth.
        if "--help" in args[1:]:
            ctx.meta["eliude_help_requested"] = True
        return args[0], cmd, args[1:]


app = typer.Typer(name="eliude", help=t("help.root"), cls=HelpOnInvalidCommandGroup)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"eliude {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help=t("help.opt.version")
    ),
) -> None:
    check_version_compatibility(ctx)
    if ctx.invoked_subcommand is None:
        typer.echo(f"eliude {__version__}")
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.command(name="login", help=t("help.cmd.login"))(login.login)
app.command(name="logout", help=t("help.cmd.logout"))(login.logout)
app.command(name="change-password", help=t("help.cmd.change_password"))(change_password.change_password)
app.command(name="signup", help=t("help.cmd.signup"))(signup.signup)
app.command(name="submit", help=t("help.cmd.submit"))(submit.submit)
app.command(name="switch", help=t("help.cmd.switch"))(classrooms.switch)
app.command(name="get", help=t("help.cmd.get"))(get.get)
app.command(name="status", help=t("help.cmd.status"))(status.status)
app.command(name="show", help=t("help.cmd.show"))(questions.show_question)

classrooms_app = typer.Typer(help=t("help.group.classrooms"), cls=HelpOnInvalidCommandGroup)
classrooms_app.command("list", help=t("help.cmd.classrooms_list"))(classrooms.list_classrooms)
app.add_typer(classrooms_app, name="classrooms")

practices_app = typer.Typer(help=t("help.group.practices"), cls=HelpOnInvalidCommandGroup)


@practices_app.callback(invoke_without_command=True)
def practices_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        practices.list_practices()
        raise typer.Exit()


practices_app.command("list", help=t("help.cmd.practices_list"))(practices.list_practices)
practices_app.command("switch", help=t("help.cmd.practices_switch"))(practices.switch)
app.add_typer(practices_app, name="practices")

questions_app = typer.Typer(help=t("help.group.questions"), cls=HelpOnInvalidCommandGroup)


@questions_app.callback(invoke_without_command=True)
def questions_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        questions.list_questions(show_timestamp=False, unsolved=False)
        raise typer.Exit()


questions_app.command("list", help=t("help.cmd.questions_list"))(questions.list_questions)
questions_app.command("show", help=t("help.cmd.show"))(questions.show_question)
app.add_typer(questions_app, name="questions")

submissions_app = typer.Typer(help=t("help.group.submissions"), cls=HelpOnInvalidCommandGroup)
submissions_app.command("status", help=t("help.cmd.submissions_status"))(submissions.status)
app.add_typer(submissions_app, name="submissions")

config_app = typer.Typer(help=t("help.group.config"), cls=HelpOnInvalidCommandGroup)
config_app.command("set-url", help=t("help.cmd.config_set_url"))(config_cmd.set_url)
config_app.command("set-language", help=t("help.cmd.config_set_language"))(config_cmd.set_language)
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
