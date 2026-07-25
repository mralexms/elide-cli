# eliude-cli

CLI for the Eliude C programming judge.

## Installing the eliude CLI

1. Make sure [pipx](https://pipx.pypa.io/) is available:
   ```bash
   python3 -m pip install --user pipx && python3 -m pipx ensurepath
   ```
2. Install directly from this repo:
   ```bash
   pipx install "git+https://github.com/mralexms/elide-cli.git"
   ```
3. Point the CLI at your server, if it isn't the default (`http://localhost:8000`):
   ```bash
   eliude config set-url http://<your-eliude-host>
   ```
4. If you're a student, either `eliude login` with credentials your teacher gave you, or self-register with a classroom join code (see below).

## Student self-signup

A teacher can share a classroom's join code (shown on that classroom's page in the teacher portal). Any student can then join without an account being created for them first:

```bash
eliude signup
```

Prompts for full name, email, password (twice, to confirm), and the classroom code. On success you're logged in and switched into that classroom automatically.

## Language

The CLI's own messages (not exercise content, which comes from the server as-is) are available in English and Portuguese (`pt-BR`). By default it follows your system locale (`LANG`/`LC_ALL`/`LC_MESSAGES`), falling back to English if that can't be determined. Override explicitly:

```bash
eliude config set-language pt-BR
eliude config set-language en
```

`ELIUDE_LANGUAGE` (an environment variable) takes priority over both the system locale and the saved setting, if set.

## Version compatibility

Every time you run a command, the CLI checks that its version matches exactly what your configured server declares as compatible. If it doesn't match — either direction — the command is refused and the CLI prints the exact command to reinstall the right version, e.g.:

```bash
pipx install --force "git+https://github.com/mralexms/elide-cli.git@v0.2.0"
```

There's no self-update command — you always run that command yourself. `eliude config set-url` (and nothing else) keeps working even when versions don't match, so you can always fix a wrong server URL. If the server is unreachable or hasn't published a release, the check fails open and your commands run normally.

## Releasing a new version

1. Bump `version` in `pyproject.toml` and commit.
2. Tag and push:
   ```bash
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```
3. On the backend, mark it as the current release:
   ```bash
   python manage.py publish_cli_release vX.Y.Z
   ```
