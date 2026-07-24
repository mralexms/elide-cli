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

## Updating

The CLI checks for a newer version once a day and prints a warning if you're behind. Your Eliude server declares which version (a git tag in this repo) it's compatible with — `eliude update` installs exactly that one:

```bash
eliude update
```

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
