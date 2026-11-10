# PS5 Game Assistant Translator

PS5 oyunlarındaki İngilizce altyazıları webcam ile okuyup anlık olarak Türkçeye çeviren, sonucu ikinci ekranda gösteren açık kaynak bir Windows uygulaması.

> Reads English subtitles from PS5 games through a webcam, translates them in real time and shows the result on a second screen. Windows only.

**Durum:** Erken geliştirme aşamasında. Henüz kullanıma hazır değil.

## Nasıl çalışır

```
Webcam → görüntüyü düzleştir + altyazı bölgesini kırp → OCR → kararlılık kontrolü → çeviri → ikinci ekran
```

- **OCR:** Görüntüdeki yazıyı metne çevirir (henüz İngilizce).
- **Çeviri:** Metni Türkçeye çevirir.
- Uygulama her adımda ne yaptığını ve neden yaptığını kısa açıklamalarla gösterir.

PS5 kablolaması değişmez: konsol doğrudan monitöre bağlı kalır, oyun görüntüsüne dokunulmaz.

## Hedefler

- Sadece Windows.
- Ortalama bir oyuncu bilgisayarında rahat çalışacak hafif araçlar.
- Her parça değiştirilebilir: OCR motoru, çeviri motoru, opsiyonel yerel AI.
- Opsiyonel AI kuruluysa: daha iyi çeviri ve diyaloglar hakkında soru sorabilme.

## Kurulum (geliştirme)

Python 3.11 veya üzeri gerekir.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m ps5_translator
```

## Yerel çeviri modelleri (opsiyonel)

İnternet ve hesap gerektirmeden çeviri için [Ollama](https://ollama.com) kur ve modelleri bir kez indir:

```powershell
ollama pull kaelri/hy-mt2:1.8b-q4_K_M   # Hy-MT2 1.8B: sadece çeviri, ~1-2 GB
ollama pull gemma4:e2b                  # Gemma 4 E2B: genel model, ~7 GB indirme
```

Uygulamada motor listesinden seçmen yeterli. Motorları aynı cümlelerle karşılaştırmak için:

```powershell
python tools/compare_engines.py
```

## Notlar

- Varsayılan Google çeviri motoru resmi bir API değildir; çok sık istekte geçici olarak engellenebilir.
- Yerel modeller uygulamayla birlikte dağıtılmaz. Kullanıcı kendisi indirir ve modelin lisansına uymaktan kendisi sorumludur.
- Bu proje Sony Interactive Entertainment ile bağlantılı değildir. "PlayStation" ve "PS5" Sony'nin ticari markalarıdır.

## Belgeler

- [Kararlar](docs/kararlar.md)
- [Test kaydı](docs/test-log.md)

## Lisans

MIT
