import deepl
import pytest

from ps5_translator import settings
from ps5_translator.translation.deepl_engine import DeepLEngine, MissingApiKey


class FakeResult:
    def __init__(self, text):
        self.text = text


class FakeClient:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def translate_text(self, text, source_lang, target_lang, context):
        self.calls.append({"text": text, "source": source_lang, "target": target_lang, "context": context})
        if self.error:
            raise self.error
        return FakeResult(f"TR:{text}")


def test_previous_line_is_sent_as_context():
    client = FakeClient()
    engine = DeepLEngine(client=client)
    engine.translate("Did you see him?")
    engine.translate("He was here.")
    assert client.calls[0]["context"] is None
    assert client.calls[1]["context"] == "Did you see him?"
    assert client.calls[1]["source"] == "EN"
    assert client.calls[1]["target"] == "TR"


def test_english_target_uses_regional_code():
    client = FakeClient()
    DeepLEngine(source="de", target="en", client=client).translate("Hallo")
    assert client.calls[0]["target"] == "EN-US"


def test_errors_become_clear_messages():
    engine = DeepLEngine(client=FakeClient(error=deepl.QuotaExceededException("quota")))
    with pytest.raises(RuntimeError, match="kotası doldu"):
        engine.translate("Hi")


def test_missing_key_explains_what_to_do(monkeypatch):
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)
    monkeypatch.setattr(settings, "get_deepl_key", lambda: None)
    with pytest.raises(MissingApiKey, match="deepl.com/pro-api"):
        DeepLEngine()


def test_env_variable_is_used(monkeypatch):
    monkeypatch.setenv("DEEPL_API_KEY", " abc:fx ")
    assert settings.get_deepl_key() == "abc:fx"
