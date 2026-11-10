"""Local translation with OPUS-MT (no API key, no internet after the first download).

Model: Helsinki-NLP opus-mt-tc-big-en-tr (CC BY 4.0), in a version converted for
CTranslate2, which runs it fast on the CPU. About 470 MB, downloaded once from
Hugging Face into the user's app data folder. The app does not ship the model.

Quality is below DeepL: it translates each line on its own and is weaker with
idioms and slang.
"""
from __future__ import annotations

from pathlib import Path

from .. import settings
from .engines import Engine

MODEL_REPO = "ooeoeo/opus-mt-tc-big-en-tr-ct2-float16"
# Pinned to one exact version of the repository, so a later change to it cannot
# silently change what gets downloaded.
MODEL_REVISION = "4729dd2c625df6a5782d0a2225a36b14d52925b0"
MODEL_FILES = ["config.json", "model.bin", "shared_vocabulary.json", "source.spm", "target.spm"]
MODEL_SIZE_MB = 470


def model_dir() -> Path:
    return settings.config_path().parent / "models" / "opus-mt-tc-big-en-tr"


def is_downloaded() -> bool:
    return all((model_dir() / name).is_file() for name in MODEL_FILES)


def download_model() -> Path:
    from huggingface_hub import snapshot_download

    target = model_dir()
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(MODEL_REPO, revision=MODEL_REVISION, local_dir=str(target), allow_patterns=MODEL_FILES)
    return target


class OpusMtEngine(Engine):
    name = "Yerel model (OPUS-MT)"
    needs_internet = False
    ready_note = (
        "Çeviri bu bilgisayarda yapılıyor; internet, anahtar ve kota gerekmiyor.",
        "Model küçük olduğu için kalitesi DeepL'in altında: her repliği tek başına çevirir, "
        "deyim ve argoda daha çok hata yapar. Ayarlar'dan istediğin zaman DeepL'e geçebilirsin.",
    )

    def __init__(self, source: str = "en", target: str = "tr", translator=None, source_sp=None, target_sp=None) -> None:
        super().__init__(source, target)
        if (source, target) != ("en", "tr"):
            raise RuntimeError("Yerel model yalnızca İngilizce → Türkçe çeviri yapar.")
        if translator is None:
            translator, source_sp, target_sp = self._load()
        self._translator = translator
        self._source_sp = source_sp
        self._target_sp = target_sp

    @staticmethod
    def _load():
        try:
            import ctranslate2
            import sentencepiece
        except ImportError as exc:
            raise RuntimeError("Yerel model paketleri kurulu değil. setup.bat dosyasını çalıştır.") from exc
        if not is_downloaded():
            try:
                download_model()
            except Exception as exc:
                raise RuntimeError(
                    f"Model indirilemedi ({MODEL_SIZE_MB} MB, internet gerekir): {exc}"
                ) from exc
        path = model_dir()
        # One thread on purpose. OCR runs all the time on the other CPU cores; when the
        # translator also spread over several cores, the two fought for them and a single
        # line sometimes took many seconds. One thread is steady and fast enough for a subtitle.
        translator = ctranslate2.Translator(str(path), device="cpu", compute_type="int8", intra_threads=1)
        source_sp = sentencepiece.SentencePieceProcessor(model_file=str(path / "source.spm"))
        target_sp = sentencepiece.SentencePieceProcessor(model_file=str(path / "target.spm"))
        return translator, source_sp, target_sp

    def translate(self, text: str) -> str:
        # The model expects an end-of-sentence mark after the source tokens.
        tokens = self._source_sp.encode(text, out_type=str) + ["</s>"]
        result = self._translator.translate_batch([tokens], beam_size=4, max_decoding_length=160)
        return self._target_sp.decode(result[0].hypotheses[0]).strip()
