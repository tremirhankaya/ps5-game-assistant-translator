# Kararlar

## Donanım yolu
- Monitör (ASUS ROG Strix XG27ACG) üzerine metin çizmek mümkün değil: DDC/CI yalnızca sayısal ayarlar taşıyor, PiP/PBP yok. Ayrıntılar: [test-log.md](test-log.md).
- Prototip: mevcut webcam → PC → çeviri **ikinci monitörde** gösterilir. PS5 kablolaması değişmez.
- İleride isabet yetmezse: capture kart (passthrough + PC'ye kopya).

## Platform ve ilkeler
- Yalnızca Windows.
- İşi görecek kadar hafif araçlar; ortalama bir oyuncu PC'sini zorlayan büyük modeller varsayılan olmaz.
- Her parça değiştirilebilir: kamera, OCR, çeviri motoru, AI.
- Araçlar kendi verimizle ölçülerek seçilir (küçük benchmark aracı).
- Modeller dağıtılmaz; kullanıcı kendisi indirir.
- Hedef dil ayarlanabilir (varsayılan Türkçe).

## Bileşen kısa listesi
- **Arayüz:** PySide6 (Qt).
- **Kamera + görüntü işleme:** OpenCV; perspektif düzeltme (homografi).
- **OCR:**
  - Windows OCR (`winocr` / `winrt-Windows.Media.Ocr`): ek model yok, çok hafif. "Package identity" gereksinimi pratikte doğrulanacak.
  - RapidOCR (PaddleOCR modelleri, ONNX, CPU'da çalışır).
- **Çeviri:**
  - Google (deep-translator): anahtar yok, temel çizgi.
  - Küçük yerel model, opsiyonel: Hy-MT2 1.8B veya Gemma 4 E2B.
  - 7B+ modeller varsayılan değil; ayarlardan seçilebilir.
- **LLM çalıştırma:** OpenAI uyumlu API (Ollama / llama.cpp / LM Studio).

## Pipeline
Kamera → perspektif düzeltme + bölge kırpma → OCR → kararlılık kontrolü → tekrar/önbellek → çeviri → ikinci ekran.

## Açıklama paneli
- "Bu adımı neden yapıyoruz" metinleri sabit şablonlardır; LLM üretmez (hızlı, her zaman doğru).

## Opsiyonel AI özellikleri
- AI sunucusu algılanırsa etkinleşir; yoksa gri görünür ve kurulum açıklaması gösterilir.
- Çeviri motoru olarak LLM.
- Diyalog soru-cevap: diyalog geçmişi üzerinden, yalnızca o ana kadarki repliklerle; "yalnızca verilen diyaloglara dayan" kuralı; canlı çeviri her zaman önceliklidir.
