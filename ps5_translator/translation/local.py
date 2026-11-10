"""Local translation models served by Ollama (https://ollama.com).

The user installs Ollama and pulls a model once; the app talks to it over
http://localhost:11434. Nothing is sent to the internet.
"""
from __future__ import annotations

import re

import requests

from .engines import Engine

OLLAMA_URL = "http://localhost:11434"

LANGUAGE_NAMES = {
    "en": "English",
    "tr": "Turkish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "ru": "Russian",
    "ar": "Arabic",
}

# Control tokens some models leak into the answer, e.g. <|hy_Assistant|>.
_CONTROL_TOKENS = re.compile(r"<\|?[^<>]*?\|?>")


class OllamaNotAvailable(RuntimeError):
    pass


def clean_output(text: str) -> str:
    """Remove leaked control tokens, wrapping quotes and labels."""
    text = _CONTROL_TOKENS.sub("", text).strip()
    for label in ("Translation:", "Çeviri:"):
        if text.lower().startswith(label.lower()):
            text = text[len(label):].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'“”":
        text = text[1:-1].strip()
    return text


class OllamaEngine(Engine):
    """Base class for models running in Ollama."""

    model = ""
    needs_internet = False
    options: dict = {}
    timeout = 60

    def __init__(self, source: str = "en", target: str = "tr", base_url: str = OLLAMA_URL) -> None:
        super().__init__(source, target)
        self.base_url = base_url.rstrip("/")
        self._check_available()

    # -- setup

    def _check_available(self) -> None:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaNotAvailable(
                "Ollama çalışmıyor. ollama.com adresinden kurup açık olduğundan emin ol."
            ) from exc
        installed = {m.get("name", "") for m in response.json().get("models", [])}
        if self.model not in installed:
            raise OllamaNotAvailable(
                f"{self.model} modeli indirilmemiş. Terminalde çalıştır: ollama pull {self.model}"
            )

    def warm_up(self) -> None:
        """Load the model into memory so the first real line is not slow."""
        self._chat([{"role": "user", "content": "Hi"}], num_predict=1)

    # -- translation

    def build_messages(self, text: str) -> list[dict]:
        raise NotImplementedError

    def translate(self, text: str) -> str:
        return clean_output(self._chat(self.build_messages(text)))

    def _chat(self, messages: list[dict], num_predict: int = 256) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": "30m",
            "options": {**self.options, "num_predict": num_predict},
        }
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["message"]["content"]

    def _lang(self, code: str) -> str:
        return LANGUAGE_NAMES.get(code, code)


class HyMT2Engine(OllamaEngine):
    """Tencent Hy-MT2 1.8B: a small model trained only for translation."""

    name = "Hy-MT2 1.8B (yerel)"
    model = "kaelri/hy-mt2:1.8b-q4_K_M"
    # Values recommended by Tencent for the 1.8B and 7B models.
    options = {"temperature": 0.7, "top_p": 0.6, "top_k": 20, "repeat_penalty": 1.05}

    def build_messages(self, text: str) -> list[dict]:
        # Official prompt format; the model has no system prompt.
        prompt = (
            f"Translate the following segment into {self._lang(self.target)}, "
            f"without additional explanation.\n\n{text}"
        )
        return [{"role": "user", "content": prompt}]


class Gemma4Engine(OllamaEngine):
    """Google Gemma 4 E2B: a small general model (can also answer questions later)."""

    name = "Gemma 4 E2B (yerel)"
    model = "gemma4:e2b"
    options = {"temperature": 0.2}

    def build_messages(self, text: str) -> list[dict]:
        system = (
            f"You translate video game subtitles from {self._lang(self.source)} "
            f"to {self._lang(self.target)}. Reply with the translation only. "
            "Keep character and place names as they are. Use natural, spoken language."
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": text}]
