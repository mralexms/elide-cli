import json
import os
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"

CONFIG_DIR = Path(os.environ.get("ELIUDE_CONFIG_DIR", Path.home() / ".eliude"))
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(CONFIG_FILE, 0o600)


def get_base_url() -> str:
    env_url = os.environ.get("ELIUDE_BASE_URL")
    if env_url:
        return env_url
    return load_config().get("base_url", DEFAULT_BASE_URL)


def get_token() -> str | None:
    return load_config().get("token")


def set_token(token: str, username: str) -> None:
    data = load_config()
    data["token"] = token
    data["username"] = username
    save_config(data)


def set_base_url(base_url: str) -> None:
    data = load_config()
    data["base_url"] = base_url
    save_config(data)


def clear_token() -> None:
    data = load_config()
    data.pop("token", None)
    data.pop("username", None)
    save_config(data)


def get_active_classroom() -> str | None:
    return load_config().get("active_classroom")


def set_active_classroom(slug: str) -> None:
    data = load_config()
    data["active_classroom"] = slug
    save_config(data)


def clear_active_classroom() -> None:
    data = load_config()
    data.pop("active_classroom", None)
    save_config(data)


def get_last_version_check() -> float | None:
    return load_config().get("last_version_check")


def set_last_version_check(timestamp: float) -> None:
    data = load_config()
    data["last_version_check"] = timestamp
    save_config(data)
