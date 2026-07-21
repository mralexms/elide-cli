# eliude-cli

CLI for the Eliude C programming judge.

## Installing the eliude CLI

1. Make sure [pipx](https://pipx.pypa.io/) is available:
   ```bash
   python3 -m pip install --user pipx && python3 -m pipx ensurepath
   ```
2. Fetch and install the latest release published by your Eliude server:
   ```bash
   URL=$(curl -s http://<your-eliude-host>/api/cli/latest/ | python3 -c "import sys,json;print(json.load(sys.stdin)['download_url'])")
   pipx install "$URL"
   ```
3. Point the CLI at your server, if it isn't the default (`http://localhost:8000`):
   ```bash
   eliude config set-url http://<your-eliude-host>
   ```

## Updating

The CLI checks for a newer version once a day and prints a warning if you're behind. To upgrade:

```bash
eliude update
```
