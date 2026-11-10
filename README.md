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

## Notlar

- Varsayılan Google çeviri motoru resmi bir API değildir; çok sık istekte geçici olarak engellenebilir.
- Yerel modeller uygulamayla birlikte dağıtılmaz. Kullanıcı kendisi indirir ve modelin lisansına uymaktan kendisi sorumludur.
- Bu proje Sony Interactive Entertainment ile bağlantılı değildir. "PlayStation" ve "PS5" Sony'nin ticari markalarıdır.

## Belgeler

- [Kararlar](docs/kararlar.md)
- [Test kaydı](docs/test-log.md)

## Lisans

MIT
