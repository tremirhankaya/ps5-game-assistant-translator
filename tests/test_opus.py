import pytest

from ps5_translator import settings
from ps5_translator.translation import DeepLEngine, OpusMtEngine, create_engine, opus_engine


class FakeSp:
    def encode(self, text, out_type=str):
        return text.split()

    def decode(self, tokens):
        return " ".join(tokens)


class FakeHyp:
    def __init__(self, tokens):
        self.hypotheses = [tokens]


class FakeTranslator:
    def __init__(self):
        self.seen = None

    def translate_batch(self, batch, **kwargs):
        self.seen = batch
        return [FakeHyp(["Anahtar", "nerede?"])]


def test_source_gets_end_mark_and_output_is_decoded():
    translator = FakeTranslator()
    engine = OpusMtEngine(translator=translator, source_sp=FakeSp(), target_sp=FakeSp())
    assert engine.translate("Where is the key?") == "Anahtar nerede?"
    assert translator.seen == [["Where", "is", "the", "key?", "</s>"]]


def test_only_english_to_turkish():
    with pytest.raises(RuntimeError, match="İngilizce"):
        OpusMtEngine(source="en", target="de", translator=FakeTranslator(), source_sp=FakeSp(), target_sp=FakeSp())


def test_model_is_stored_in_app_data_and_detected(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert str(opus_engine.model_dir()).startswith(str(tmp_path))
    assert not opus_engine.is_downloaded()
    opus_engine.model_dir().mkdir(parents=True)
    for name in opus_engine.MODEL_FILES:
        (opus_engine.model_dir() / name).write_bytes(b"x")
    assert opus_engine.is_downloaded()


def test_engine_choice_is_saved_and_used(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("DEEPL_API_KEY", "abc:fx")
    assert settings.get_engine() == "deepl"
    assert isinstance(create_engine(), DeepLEngine)
    settings.set_engine("opus")
    assert settings.get_engine() == "opus"
    made = []
    monkeypatch.setattr(OpusMtEngine, "_load", staticmethod(lambda: (made.append(1) or FakeTranslator(), FakeSp(), FakeSp())))
    assert isinstance(create_engine(), OpusMtEngine) and made
