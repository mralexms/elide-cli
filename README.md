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
