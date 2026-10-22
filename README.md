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
3. The CLI already points at the production server (`https://fabrica.ifma.edu.br/eliude`). Only if you use a different one (e.g. a backend running locally):
   ```bash
   eliude config set-url http://localhost:8000
   ```
4. If you're a student, either `eliude login` with credentials your teacher gave you, or self-register with a classroom join code (see below).

## Trying it in an ephemeral container

No install, nothing touches your machine: `Dockerfile.try` builds a throwaway image with the CLI (installed via pipx from this repo, same as above) plus `git`, `nano`/`vim`, and `gcc` — enough to write and locally compile a solution before `eliude submit` sends it off.

```bash
docker build -f Dockerfile.try -t eliude-cli-try .
docker run --rm -it eliude-cli-try
```

`ELIUDE_BASE_URL` defaults to the production server baked into the image. Pointing at a server running on your own machine instead (e.g. local dev)?

```bash
docker run --rm -it --add-host=host.docker.internal:host-gateway \
  -e ELIUDE_BASE_URL=http://host.docker.internal:8000 eliude-cli-try
```

`--add-host` is what makes `host.docker.internal` resolve — a no-op on Docker Desktop (which already does this), needed for the same name to work on Linux.

`exit` the shell and the container (config, login token, any files you created) is gone.

## Accounts

Accounts are created on the web, not by the CLI: a teacher enrolls the student, or the student signs in with Google on the Eliude site and joins a classroom with its code. To use the CLI, set a password on the web first (the "Senha do CLI" page, `<server>/password/`), then:

```bash
eliude login
```

## Language

The CLI's own messages (not exercise content, which comes from the server as-is) are available in English and Portuguese (`pt-BR`). By default it follows your system locale (`LANG`/`LC_ALL`/`LC_MESSAGES`), falling back to English if that can't be determined. Override explicitly:

```bash
eliude config set-language pt-BR
eliude config set-language en
```

`ELIUDE_LANGUAGE` (an environment variable) takes priority over both the system locale and the saved setting, if set.

## Reading a question

`eliude show q1` renders the statement's Markdown (headings, **bold**, lists, tables, colored C code) and, when it doesn't fit the screen, opens it in `less` (with `LESS=FRX` unless you set your own `LESS`, or another pager through `PAGER`). Single line breaks in the statement are kept, as on the web. Piped or redirected (`eliude show q1 > q1.txt`), it prints the statement as written, with no colors and no pager. On Windows there's no pager.

Colors are 256 by default, which PuTTY, macOS Terminal and most terminals support even when `TERM` doesn't say so. Set `ELIUDE_COLORS` to `16`, `256`, `truecolor` or `none` to change it; `NO_COLOR` also turns colors off.

## Version compatibility

Every time you run a command, the CLI checks that its version matches exactly what your configured server declares as compatible. If it doesn't match — either direction — the command is refused and the CLI prints the exact command to reinstall the right version, e.g.:

```bash
pipx install --force "git+https://github.com/mralexms/elide-cli.git@v0.2.0"
```

When you're at a terminal and installed with pipx (as above), the CLI first offers to run that command for you — `Install eliude-cli vX.Y.Z now? (Y/n)` — and then runs your command again on the new version. It never updates without asking, and it doesn't offer on Windows (the running CLI's files are locked there) or when the server points at a repo other than this one; in those cases, or if the update fails, run the command yourself. `eliude config set-url` (and nothing else) keeps working even when versions don't match, so you can always fix a wrong server URL. If the server is unreachable or hasn't published a release, the check fails open and your commands run normally.

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
