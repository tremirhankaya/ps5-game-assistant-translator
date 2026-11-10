from ps5_translator.explain import _TEMPLATES, explain
from ps5_translator.translation import EchoEngine, Event, TranslationPipeline


def test_every_pipeline_event_has_an_explanation():
    pipeline = TranslationPipeline(EchoEngine())
    seen = set()
    for line in ["Hello\nthere", "Hello there", "Bye", "Hello there"]:
        result = pipeline.process(line)
        seen.update(e.code for e in result.events)
    assert seen <= set(_TEMPLATES)


def test_details_are_filled_in():
    text = explain(Event("translated", {"engine": "Google", "ms": 123.4})).what
    assert "Google" in text and "123" in text


def test_unknown_event_does_not_crash():
    assert explain(Event("something_new")).what == "something_new"
