import pytest
import requests

from ps5_translator.translation import local
from ps5_translator.translation.local import Gemma4Engine, HyMT2Engine, OllamaNotAvailable, clean_output


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture
def ollama(monkeypatch):
    """Pretend Ollama is running with both models installed."""
    sent = []

    def fake_get(url, timeout):
        models = [{"name": HyMT2Engine.model}, {"name": Gemma4Engine.model}]
        return FakeResponse({"models": models})

    def fake_post(url, json, timeout):
        sent.append(json)
        return FakeResponse({"message": {"content": "<|hy_Assistant|>Anahtar nerede?"}})

    monkeypatch.setattr(local.requests, "get", fake_get)
    monkeypatch.setattr(local.requests, "post", fake_post)
    return sent


def test_clean_output_removes_control_tokens_and_quotes():
    assert clean_output("<|hy_Assistant|>Merhaba<hy-Assistant}>") == "Merhaba"
    assert clean_output('"Anahtar nerede?"') == "Anahtar nerede?"
    assert clean_output("Translation: Gidelim.") == "Gidelim."


def test_hymt2_uses_official_prompt(ollama):
    result = HyMT2Engine().translate("Where is the key?")
    assert result == "Anahtar nerede?"
    payload = ollama[0]
    assert payload["think"] is False
    assert payload["messages"][0]["content"].startswith("Translate the following segment into Turkish")
    assert payload["messages"][0]["content"].endswith("Where is the key?")


def test_gemma_uses_system_prompt(ollama):
    Gemma4Engine().translate("Hi")
    roles = [m["role"] for m in ollama[0]["messages"]]
    assert roles == ["system", "user"]


def test_missing_ollama_gives_clear_message(monkeypatch):
    def fail(url, timeout):
        raise requests.ConnectionError()

    monkeypatch.setattr(local.requests, "get", fail)
    with pytest.raises(OllamaNotAvailable, match="Ollama"):
        HyMT2Engine()


def test_missing_model_tells_how_to_pull(monkeypatch):
    monkeypatch.setattr(local.requests, "get", lambda url, timeout: FakeResponse({"models": []}))
    with pytest.raises(OllamaNotAvailable, match="ollama pull kaelri/hy-mt2"):
        HyMT2Engine()
