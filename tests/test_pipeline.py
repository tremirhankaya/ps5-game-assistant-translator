from ps5_translator.translation import EchoEngine, Engine, TranslationPipeline, normalize


class CountingEngine(EchoEngine):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def translate(self, text: str) -> str:
        self.calls += 1
        return super().translate(text)


class FailingEngine(Engine):
    name = "Failing"

    def translate(self, text: str) -> str:
        raise ConnectionError("offline")


def codes(result):
    return [e.code for e in result.events]


def test_normalize_joins_lines_and_spaces():
    assert normalize("Where is\nthe   key?") == "Where is the key?"
    assert normalize("some-\nthing") == "something"
    assert normalize("   ") == ""


def test_empty_input_returns_none():
    assert TranslationPipeline(EchoEngine()).process("  \n ") is None


def test_translates_with_engine():
    result = TranslationPipeline(EchoEngine()).process("Hello")
    assert result.translated == "[tr] Hello"
    assert codes(result) == ["engine_call", "translated"]


def test_same_line_twice_is_skipped():
    engine = CountingEngine()
    pipeline = TranslationPipeline(engine)
    pipeline.process("Hello")
    second = pipeline.process("Hello")
    assert second.skipped
    assert codes(second) == ["repeat_skipped"]
    assert engine.calls == 1


def test_earlier_line_comes_from_cache():
    engine = CountingEngine()
    pipeline = TranslationPipeline(engine)
    pipeline.process("Hello")
    pipeline.process("Bye")
    again = pipeline.process("Hello")
    assert again.from_cache
    assert again.translated == "[tr] Hello"
    assert engine.calls == 2


def test_cache_size_is_limited():
    engine = CountingEngine()
    pipeline = TranslationPipeline(engine, cache_size=2)
    for line in ["a", "b", "c", "a"]:
        pipeline.process(line)
    assert engine.calls == 4  # "a" was evicted


def test_engine_error_is_reported_and_retry_allowed():
    pipeline = TranslationPipeline(FailingEngine())
    result = pipeline.process("Hello")
    assert result.error == "offline"
    assert "engine_error" in codes(result)
    retry = pipeline.process("Hello")
    assert not retry.skipped
