from .deepl_engine import DeepLEngine
from .engines import EchoEngine, Engine
from .opus_engine import OpusMtEngine
from .pipeline import Event, Result, TranslationPipeline, normalize


def create_engine() -> Engine:
    """The engine chosen in Settings: DeepL (default) or the local OPUS-MT model."""
    from .. import settings

    if settings.get_engine() == settings.ENGINE_OPUS:
        return OpusMtEngine()
    return DeepLEngine()


__all__ = [
    "Engine",
    "DeepLEngine",
    "OpusMtEngine",
    "EchoEngine",
    "TranslationPipeline",
    "Result",
    "Event",
    "normalize",
    "create_engine",
]
