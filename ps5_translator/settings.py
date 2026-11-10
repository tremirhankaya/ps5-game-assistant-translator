"""User settings.

Secrets (API keys) are stored in Windows Credential Manager through the
keyring package, never in a plain text file inside the project folder.
The DEEPL_API_KEY environment variable is also accepted.
"""
from __future__ import annotations

import os

SERVICE = "ps5-game-assistant-translator"
_DEEPL_USER = "deepl-api-key"


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
