"""User settings.

Secrets (API keys) are stored in Windows Credential Manager through the
keyring package, never in a plain text file inside the project folder.
The DEEPL_API_KEY environment variable is also accepted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SERVICE = "ps5-game-assistant-translator"
_DEEPL_USER = "deepl-api-key"


def config_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / SERVICE / "config.json"


def load_config() -> dict:
    """Non-secret settings (camera index, subtitle region, ...)."""
    try:
        return json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(**changes) -> None:
    config = load_config()
    config.update(changes)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


ENGINE_DEEPL = "deepl"
ENGINE_OPUS = "opus"


def get_engine() -> str:
    """Which translation engine the user chose (DeepL unless they picked the local model)."""
    return ENGINE_OPUS if load_config().get("engine") == ENGINE_OPUS else ENGINE_DEEPL


def set_engine(engine: str) -> None:
    save_config(engine=ENGINE_OPUS if engine == ENGINE_OPUS else ENGINE_DEEPL)


def _keyring():
    try:
        import keyring

        return keyring
    except Exception:
        return None


def get_deepl_key() -> str | None:
    env = os.environ.get("DEEPL_API_KEY", "").strip()
    if env:
        return env
    kr = _keyring()
    if kr is None:
        return None
    try:
        return kr.get_password(SERVICE, _DEEPL_USER) or None
    except Exception:
        return None


def set_deepl_key(key: str) -> None:
    kr = _keyring()
    if kr is None:
        raise RuntimeError("keyring paketi kurulu değil: pip install keyring")
    key = key.strip()
    if key:
        kr.set_password(SERVICE, _DEEPL_USER, key)
    else:
        try:
            kr.delete_password(SERVICE, _DEEPL_USER)
        except Exception:
            pass
