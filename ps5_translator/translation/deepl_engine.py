"""DeepL translation through the official deepl package.

Needs a free DeepL API key (500,000 characters per month):
https://www.deepl.com/pro-api
"""
from __future__ import annotations

from .. import settings
from .engines import Engine

# DeepL wants a regional variant for some target languages.
_TARGET_CODES = {"en": "EN-US", "pt": "PT-PT"}


class MissingApiKey(RuntimeError):
    pass


class DeepLEngine(Engine):
    name = "DeepL"
    needs_internet = True
    ready_note = (
        "Bir önceki replik DeepL'e bağlam olarak da gönderilecek.",
        "Tek başına \"Did he see it?\" cümlesinde \"he\" ve \"it\" belirsizdir. "
        "Önceki repliği görmek doğru çeviriyi kolaylaştırır. Bağlam çevrilmez ve kotadan düşmez.",
    )

    def __init__(self, source: str = "en", target: str = "tr", api_key: str | None = None, client=None) -> None:
        super().__init__(source, target)
        if client is None:
            key = api_key or settings.get_deepl_key()
            if not key:
                raise MissingApiKey(
                    "DeepL anahtarı girilmemiş. deepl.com/pro-api adresinden ücretsiz anahtar al "
                    "ve uygulamada Ayarlar'dan gir."
                )
            import deepl

            client = deepl.DeepLClient(key)
        self._client = client
        self._previous: str | None = None

    def translate(self, text: str) -> str:
        import deepl

        try:
            result = self._client.translate_text(
                text,
                source_lang=self.source.upper(),
                target_lang=_TARGET_CODES.get(self.target, self.target.upper()),
                context=self._previous,
            )
        except deepl.AuthorizationException as exc:
            raise RuntimeError("DeepL anahtarı geçersiz. Ayarlar'dan kontrol et.") from exc
        except deepl.QuotaExceededException as exc:
            raise RuntimeError("DeepL aylık ücretsiz kotası doldu. Gelecek ay sıfırlanır.") from exc
        except deepl.ConnectionException as exc:
            raise RuntimeError("DeepL'e bağlanılamadı. İnternet bağlantını kontrol et.") from exc
        self._previous = text
        return result.text

    def usage(self) -> tuple[int, int] | None:
        """Characters used and the monthly limit, or None if unknown."""
        usage = self._client.get_usage()
        if usage.character.valid:
            return usage.character.count, usage.character.limit
        return None
