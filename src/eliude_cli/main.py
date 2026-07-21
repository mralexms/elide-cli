import typer

from .commands import classrooms, config_cmd, exercises, login, submissions, submit

app = typer.Typer(name="eliude", help="CLI for the Eliude C programming judge")
app.command(name="login")(login.login)
app.command(name="logout")(login.logout)
app.command(name="submit")(submit.submit)
app.command(name="switch")(classrooms.switch)

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
