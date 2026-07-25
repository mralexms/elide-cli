import json
import os
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "pt-BR")

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


def get_username() -> str | None:
    return load_config().get("username")


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


def get_active_practice() -> str | None:
    return load_config().get("active_practice")


def set_active_practice(slug: str) -> None:
    data = load_config()
    data["active_practice"] = slug
    save_config(data)


def clear_active_practice() -> None:
    data = load_config()
    data.pop("active_practice", None)
    save_config(data)


def _normalize_detected_language(value: str) -> str:
    """Maps a loosely-formatted system/env locale ("pt_BR", "PT-br",
    "en_US"...) to one of SUPPORTED_LANGUAGES. Used only for best-effort
    auto-detection, where silently falling back to English for anything
    unrecognized is correct — unlike an explicit `set-language`, this must
    never error."""
    code = value.strip().replace("_", "-").lower()
    if code.startswith("pt"):
        return "pt-BR"
    return "en"


_LANGUAGE_ALIASES = {
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "english": "en",
    "pt": "pt-BR",
    "pt-br": "pt-BR",
    "pt-pt": "pt-BR",
    "portuguese": "pt-BR",
    "português": "pt-BR",
}


def resolve_language_alias(value: str) -> str | None:
    """Strict lookup for explicit user input (`eliude config set-language`):
    returns the canonical code, or None if not recognized — unlike the
    lenient auto-detection above, an unrecognized value here should be
    reported as an error, not silently guessed."""
    return _LANGUAGE_ALIASES.get(value.strip().replace("_", "-").lower())


def _detect_system_language() -> str:
    # POSIX convention: LC_ALL overrides LC_MESSAGES overrides LANG.
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if value:
            return _normalize_detected_language(value.split(".")[0])
    return DEFAULT_LANGUAGE


def get_language() -> str:
    env_language = os.environ.get("ELIUDE_LANGUAGE")
    if env_language:
        return _normalize_detected_language(env_language)
    configured = load_config().get("language")
    if configured:
        return configured
    return _detect_system_language()


def set_language(language: str) -> None:
    data = load_config()
    data["language"] = language
    save_config(data)
