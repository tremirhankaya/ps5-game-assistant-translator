# PS5 Game Assistant Translator

PS5 oyunlarındaki İngilizce altyazıları webcam ile okuyup anlık olarak Türkçeye çeviren açık kaynak bir Windows uygulaması. Çeviriyi ikinci monitörde ya da telefonunda gösterir.

> Reads English subtitles from PS5 games through a webcam, translates them to Turkish in real time and shows them on a second monitor or a phone. Windows only.

**Durum:** Erken sürüm. Çalışıyor, ama hatalarla karşılaşabilirsin.

> **Resmî bir ürün değildir.** Hobi projesidir; Sony Interactive Entertainment ile bağlantısı yoktur. "PlayStation" ve "PS5" Sony'nin ticari markalarıdır.

## Nasıl çalışır

```
Webcam → altyazı alanını düzleştir → OCR (yazıyı oku) → DeepL (çevir) → ikinci monitör / telefon
```

- PS5 kablolaması değişmez: konsol doğrudan monitöre bağlı kalır, oyun görüntüsüne ve gecikmesine dokunulmaz.
- Uygulama her adımda ne yaptığını ve neden yaptığını kısa açıklamalarla gösterir.

## Gerekenler

- Windows 10 ya da 11
- Bir webcam (1080p önerilir)
- İnternet bağlantısı ve ücretsiz bir DeepL API anahtarı
- Çeviriyi göstermek için ikinci bir monitör ya da aynı Wi-Fi'da bir telefon / tablet

## Kurulum

```powershell
git clone https://github.com/tremirhankaya/ps5-game-assistant-translator.git
cd ps5-game-assistant-translator
.\setup.bat
```

`setup.bat` gerekirse Python 3.13'ü kurar, sanal ortamı oluşturur ve paketleri yükler. Python 3.13 kullanılır, çünkü yazı okuma için gereken onnxruntime daha yeni sürümleri henüz desteklemiyor.

Uygulamayı açmak için: `.\run.bat`

## Kullanım

### 1. DeepL anahtarını gir (bir kez)

1. [deepl.com/pro-api](https://www.deepl.com/pro-api) adresinden ücretsiz **DeepL API Free** hesabı aç (ayda 500.000 karakter).
2. Hesap sayfasından API anahtarını kopyala (sonu `:fx` ile biter).
3. Uygulamada **Ayarlar** düğmesine bas ve anahtarı yapıştır.

Sağ üstte "DeepL kotası: ..." yazısını görüyorsan anahtar çalışıyor. Alttaki kutuya İngilizce bir cümle yazıp Enter'a basarak çeviriyi deneyebilirsin.

### 2. Kamerayı yerleştir

- Kamerayı masaya, monitörün altına, altyazıların çıktığı bölgeye bakacak şekilde koy. Böylece oyun oynarken seni rahatsız etmez.
- Kamera ne kadar yakın ve ne kadar az eğik bakarsa yazı o kadar iyi okunur.
- Kamerayı sabitle: yerinden oynarsa ayarı yeniden yapman gerekir.

### 3. Altyazı alanını ayarla (bir kez)

**Kamera** düğmesine bas.

1. **Kamera:** Görüntü gelmiyorsa ya da yanlış kamera açıldıysa üstten başka bir numara seç. NVIDIA Broadcast ve OBS gibi programlar da sanal kamera ekler.
2. **Kamera neyi görüyor:** Kamera monitörün tamamını görüyorsa "Ekranın tamamını", yalnızca alt kısmını görüyorsa "Ekranın alt kısmını" seç.
3. **Köşeler:** Soldaki görüntüde 4 köşeye tıkla.
   - "Ekranın tamamı" modunda monitör ekranının 4 köşesi.
   - "Ekranın alt kısmı" modunda, ekranın görünen kısmında kenarlara paralel bir dikdörtgen: alt köşeler ekranın alt kenarında, üst köşeler altyazının biraz üstünde.
   - Köşeleri sürükleyerek düzeltebilirsin. Sarı ızgara ekranın kenarlarına paralel durmalı.
4. **Altyazı alanı:** Sağdaki düzleştirilmiş görüntüde altyazının çıktığı alanı fareyle sürükleyerek seç. İki satırlık altyazılar da sığacak kadar yüksek tut.
5. **Otomatik ayarla:** Ekranda bir altyazı görünürken bu düğmeye bas. Uygulama eğimi, yüksekliği ve alanı kendisi ayarlar. Birkaç saniye ile bir dakika arası sürebilir.

Pencerenin altındaki "OCR okudu: ..." satırı altyazıyı doğru gösteriyorsa ayar tamamdır. Ayarlar kaydedilir; kamera yerinden oynamadıkça tekrar yapman gerekmez.

### 4. Canlı çeviriyi başlat

Ana pencerede **Canlı çeviri** kutusunu işaretle. Kamera penceresini kapatabilirsin; arka planda çalışmaya devam eder. Durdurmak için kutunun işaretini kaldır.

### 5. Çeviriyi göster

- **Tam ekran** (F11): Çevirileri, uygulama penceresinin bulunduğu monitörde tam ekran gösterir. Önce pencereyi ikinci monitöre sürükle. Çıkmak için Esc ya da çift tık.
- **Telefonda göster:** Düğmeye bas ve çıkan QR kodu telefonun kamerasıyla okut. Çeviriler telefonun tarayıcısında açılır; uygulama kurmak gerekmez. Telefon ve bilgisayar aynı Wi-Fi ağında olmalı.
- **Geçmiş:** Tam ekranda H tuşu ya da "Geçmiş" düğmesi, o ana kadarki tüm çevirileri listeler; arama kutusuyla eski bir repliği bulabilirsin. Telefondaki sayfada da aynı düğme var.

## Sorun giderme

| Sorun | Çözüm |
|---|---|
| Kamera görüntüsü gelmiyor | Üstten başka bir kamera numarası seç. Kamerayı kullanan başka programları kapat. |
| "OCR yazı görmedi" ya da yanlış okuyor | Altyazı ekrandayken **Otomatik ayarla**'ya bas. Olmazsa kamerayı yaklaştır, açıyı azalt, köşeleri yeniden seç. |
| Çeviri gelmiyor | **Ayarlar**'dan DeepL anahtarını kontrol et. Açıklama panelindeki hata mesajına bak. |
| Telefonda sayfa açılmıyor | İkisi aynı Wi-Fi'da mı? Windows Güvenlik Duvarı'nda uygulamaya "Özel ağlar" için izin ver. |
| Telefonun ekranı kapanıyor | Telefonun ayarlarından ekran zaman aşımını uzat. |
| Telefonda "Tam ekran" düğmesi yok | iPhone'lar buna izin vermiyor. Safari'de Paylaş > "Ana Ekrana Ekle" ile aynı sonucu alırsın. |

## Güvenlik ve gizlilik

- **DeepL anahtarı** yalnızca senin bilgisayarında, Windows Kimlik Bilgisi Yöneticisi'nde saklanır. Proje klasörüne ya da ayar dosyasına yazılmaz ve yalnızca DeepL'e gönderilir. Anahtarını kimseyle paylaşma.
- **Kamera görüntüleri** diske kaydedilmez ve hiçbir yere gönderilmez. İnternete çıkan tek şey, çevrilmek üzere DeepL'e gönderilen altyazı metinleridir. DeepL'in ücretsiz API'si gönderilen metinleri saklayabilir; ayrıntı için DeepL'in kendi koşullarına bak.
- **Telefonda göster** özelliği varsayılan olarak kapalıdır. Açıldığında bilgisayar yerel ağda şifresiz (http) bir sayfa yayınlar. Sayfada yalnızca çevrilmiş altyazılar bulunur ve adresteki rastgele kod olmadan açılamaz. Yine de aynı ağdaki biri trafiği dinleyerek altyazıları görebilir. **Bu özelliği yalnızca güvendiğin ev ağında kullan; ortak ağlarda (yurt, kafe, iş yeri) açma.**
- **Ekran görüntüsü ya da video paylaşırken** "Telefonda göster" penceresindeki QR kodu ve adresi gösterme; gizli kodu ve yerel IP adresini içerir.
- **Paket sürümleri** henüz sabitlenmedi: `setup.bat` her kurulumda paketlerin güncel sürümlerini indirir.

## Bilinen sınırlar

- Yalnızca Windows; yalnızca İngilizce → Türkçe için denendi.
- Okuma kalitesi kameranın konumuna, çözünürlüğüne ve ışığa bağlıdır.
- Çeviri, altyazı ekrana geldikten kısa bir süre sonra görünür (okuma + çeviri süresi).
- Çeviri geçmişi uygulama kapanınca silinir.

## Lisans

MIT
