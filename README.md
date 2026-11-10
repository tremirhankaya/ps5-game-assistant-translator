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
- Tek ve sade bir kurulum: okuma için RapidOCR, çeviri için DeepL.

## Kurulum

Repoyu indir ve `setup.bat` dosyasını çalıştır. Gerekirse Python 3.13'ü kurar, sanal ortamı oluşturur ve paketleri yükler. Sonra uygulamayı `run.bat` ile aç.

```powershell
git clone https://github.com/tremirhankaya/ps5-game-assistant-translator.git
cd ps5-game-assistant-translator
.\setup.bat
.\run.bat
```

Python 3.13 kullanılır, çünkü RapidOCR'ın ihtiyaç duyduğu onnxruntime daha yeni sürümleri henüz desteklemiyor.

## Çeviri: DeepL

1. [deepl.com/pro-api](https://www.deepl.com/pro-api) adresinden ücretsiz **DeepL API Free** hesabı aç (ayda 500.000 karakter).
2. Hesap sayfasından API anahtarını kopyala (sonu `:fx` ile biter).
3. Uygulamada **Ayarlar** düğmesine bas ve anahtarı yapıştır.

Anahtar Windows Kimlik Bilgisi Yöneticisi'nde saklanır, proje klasörüne yazılmaz. İstersen `DEEPL_API_KEY` ortam değişkeni de kullanılabilir.

Her çeviride bir önceki replik DeepL'e bağlam olarak gönderilir; bu, "he/it" gibi belirsiz kelimelerin doğru çevrilmesine yardım eder ve kotadan düşmez.

## Çevirileri gösterme

- **Tam ekran** (F11): çevirileri uygulamanın bulunduğu monitörde tam ekran gösterir. Geçmiş ve arama için H.
- **Telefonda göster**: aynı Wi-Fi'daki bir telefon ya da tablet, ekrandaki QR kodu okutarak çevirileri tarayıcısında görür. Uygulama kurmak gerekmez. Sayfada yalnızca çevrilmiş altyazılar bulunur.

## Güvenlik ve gizlilik

- **DeepL anahtarı** yalnızca senin bilgisayarında, Windows Kimlik Bilgisi Yöneticisi'nde saklanır. Proje klasörüne ya da ayar dosyasına yazılmaz ve yalnızca DeepL'e gönderilir.
- **Kamera görüntüleri** diske kaydedilmez ve hiçbir yere gönderilmez. İnternete çıkan tek şey, çevrilmek üzere DeepL'e gönderilen altyazı metinleridir. DeepL'in ücretsiz API'si gönderilen metinleri saklayabilir; ayrıntı için DeepL'in kendi koşullarına bak.
- **Telefonda göster** özelliği varsayılan olarak kapalıdır. Açıldığında bilgisayar yerel ağda şifresiz (http) bir sayfa yayınlar. Sayfada yalnızca çevrilmiş altyazılar bulunur ve adresteki rastgele kod olmadan açılamaz. Yine de aynı ağdaki biri trafiği dinleyerek altyazıları görebilir; bu özelliği yalnızca güvendiğin ev ağında kullan, ortak ağlarda (yurt, kafe, iş yeri) açma.
- **Ekran görüntüsü paylaşırken** "Telefonda göster" penceresindeki QR kodu ve adresi gösterme; gizli kodu ve yerel IP adresini içerir.
- **Paket sürümleri** henüz sabitlenmedi: `setup.bat` her kurulumda paketlerin güncel sürümlerini indirir.

## Notlar

- Bu proje Sony Interactive Entertainment ile bağlantılı değildir. "PlayStation" ve "PS5" Sony'nin ticari markalarıdır.

## Belgeler

- [Kararlar](docs/kararlar.md)
- [Test kaydı](docs/test-log.md)

## Lisans

MIT
