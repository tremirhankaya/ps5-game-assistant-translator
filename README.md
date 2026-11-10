# PS5 Game Assistant Translator

PS5 oyunlarındaki İngilizce altyazıları webcam ile okuyup Türkçeye çeviren bir Windows uygulaması. Çevirileri ikinci monitörde veya aynı ağdaki bir telefonun tarayıcısında takip edebilirsin.

Oyun oynarken diyalogları daha rahat takip edebilmek için Claude ile konuşarak geliştirdiğim bir hobi projesi. Henüz erken sürüm; eksikler ve hatalar olabilir. Katkılara ve PR'lara açık.

> Resmî bir ürün değildir. Sony Interactive Entertainment ile bağlantısı yoktur. “PlayStation” ve “PS5”, Sony'nin ticari markalarıdır.

## Başlamadan önce

Gerekenler:

- Windows 10 veya 11 yüklü bir bilgisayar.
- Bilgisayara bağlayabileceğin bir webcam. 1080p önerilir.
- Çevirileri takip etmek için ikinci monitör veya telefon/tablet.
- İlk kurulum ve dosyaları indirmek için internet bağlantısı.

PS5, oyun oynadığın monitöre bağlı kalıyor. Webcam'i bilgisayara bağlayıp monitördeki altyazıları görecek şekilde yerleştiriyorsun. Uygulama bu görüntüdeki yazıyı okuyor, çeviriyor ve seçtiğin ekranda gösteriyor. Capture card veya Remote Play gerekmiyor.

Oyunun kendi ayarlarından **İngilizce altyazıları açmayı** unutma.

## 1. Projeyi indir

1. [Projenin GitHub sayfasını](https://github.com/tremirhankaya/ps5-game-assistant-translator) aç.
2. Dosyaların üstündeki yeşil **Code** düğmesine bas.
3. **Download ZIP** seçeneğine tıkla.
4. İnen ZIP dosyasına sağ tıklayıp **Tümünü ayıkla** ile bir klasöre çıkar.
5. Çıkardığın klasörü aç. İçinde `setup.bat`, `run.bat` ve `README.md` dosyalarını görmelisin.

Dosyaları ZIP'in içinden çalıştırma; önce klasöre çıkarmış ol.

Git kullanıyorsan ZIP yerine terminalden indirebilirsin:

```powershell
git clone https://github.com/tremirhankaya/ps5-game-assistant-translator.git
cd ps5-game-assistant-translator
```

## 2. Kurulumu yap

1. Proje klasöründeki **setup.bat** dosyasına çift tıkla.
2. Açılan terminal penceresini kapatmadan kurulumun bitmesini bekle. İnternet hızına göre birkaç dakika sürebilir.
3. **“Kurulum tamam”** mesajını gördüğünde pencereyi kapatabilirsin.
4. Uygulamayı açmak için aynı klasördeki **run.bat** dosyasına çift tıkla.

`setup.bat`, Python 3.13'ü arar; bulamazsa Windows'un `winget` aracıyla kurmayı dener. Ardından uygulamanın ihtiyaç duyduğu paketleri yükler. Python'ı veya paketleri önceden elle kurman gerekmiyor.

Python kurulamazsa [python.org](https://www.python.org/downloads/windows/) üzerinden **Python 3.13** sürümünü kurup `setup.bat` dosyasını yeniden çalıştır.

Sonraki kullanımlarda yalnızca **run.bat** dosyasını açman yeterli. Her seferinde kurulum yapmana gerek yok.

## 3. Çeviri yöntemini seç

Uygulama açıldığında **Ayarlar** düğmesine bas. İki seçenek var:

| | DeepL | Yerel model (OPUS-MT) |
|---|---|---|
| Çeviri | Deyim ve diyaloglarda genellikle daha iyi | Deyim ve argoda daha çok hata yapabilir |
| API anahtarı | Gerekli | Gerekmiyor |
| İnternet | Çeviri sırasında gerekli | Model indirildikten sonra gerekmiyor |
| İlk indirme | Ayrı bir çeviri modeli indirilmez | Yaklaşık 470 MB |
| Metinler | DeepL'e gönderilir | Bilgisayarda çevrilir |

### DeepL kullanacaksan

1. [DeepL API sayfasından](https://www.deepl.com/pro-api) bir API hesabı aç. Normal DeepL çeviri üyeliği yerine **API erişimi** gerekiyor.
2. DeepL hesabındaki API anahtarını kopyala.
3. Uygulamada **Ayarlar** bölümünü aç ve **DeepL** seçeneğini işaretle.
4. Anahtarı ilgili kutuya yapıştırıp kaydet.
5. Ana pencerenin sağ üstünde **“DeepL kotası”** bilgisinin görünmesini bekle.

Anahtarını GitHub'a veya bir ekran görüntüsüne ekleme. Uygulama anahtarı Windows Kimlik Bilgisi Yöneticisi'nde saklar.

### Yerel model kullanacaksan

1. **Ayarlar** bölümünde **Yerel model (OPUS-MT)** seçeneğini işaretle.
2. Kaydet.
3. İlk kullanımda yaklaşık 470 MB'lık modelin indirilmesini bekle. İndirme ve yükleme durumu ana penceredeki açıklama bölümünde görünür.

Model bir kez indirilir. Sonraki açılışlarda yeniden indirilmez; çeviri bilgisayarda yapılır.

Kamerayı ayarlamadan önce çeviriyi deneyebilirsin: ana pencerenin altındaki kutuya İngilizce bir cümle yazıp **Enter**'a bas. Türkçe karşılığını görüyorsan bu adım tamam.

## 4. Kamerayı yerleştir

1. Webcam'i bilgisayara bağla.
2. PS5'te bir oyun aç ve İngilizce altyazının göründüğü bir sahneye gel.
3. Kamerayı monitördeki altyazıları görecek şekilde yerleştir. Monitörün altında, masanın üzerinde durabilir; ekranın tamamını görmesi gerekmiyor.
4. Kamerayı sabitle. Yerinden oynarsa uygulamadaki alan seçimini yeniden yapman gerekir.

Kamera görüntüsünde yazılar bulanıksa veya çok küçük görünüyorsa önce kameranın konumunu düzelt. Daha yakından ve daha az eğik bakması genellikle okumayı kolaylaştırır. Altyazının başı ve sonu kadrajın dışında kalmasın.

## 5. Uygulamada kamera ayarını yap

Ana penceredeki **Kamera** düğmesine bas. Uygulama, görüntüyü düzleştirmek ve altyazı alanını seçmek için sana yardımcı oluyor.

### Doğru kamerayı seç

Üstteki **Kamera** listesinden görüntünün geldiği kamerayı seç. Görüntü yoksa veya başka bir kamera görünüyorsa diğer numaraları dene. OBS ve NVIDIA Broadcast gibi programlar da listede sanal kamera olarak görünebilir.

### Kameranın neyi gördüğünü seç

**Kamera neyi görüyor** listesinden konumuna uygun seçeneği seç:

- **Ekranın tamamını:** Monitörün dört köşesi de kamera görüntüsünde görünüyorsa.
- **Ekranın alt kısmını:** Kamera yalnızca altyazıların olduğu alt bölgeye bakıyorsa.

### Dört köşeyi işaretle

Soldaki kamera görüntüsünde dört köşeye tıkla:

- Ekranın tamamını seçtiysen monitörün görüntü alanının dört köşesini işaretle.
- Ekranın alt kısmını seçtiysen altyazıyı içine alan bir dikdörtgenin dört köşesini işaretle. Alt köşeler ekranın alt kenarına, üst köşeler altyazının biraz üstüne gelebilir.

Sağ tarafta seçtiğin alanın düzleştirilmiş hâli görünür. Sarı ızgara çizgilerinin ekranın kenarlarıyla aynı yönde olmasına bak. Bir köşe yanlış yerdeyse sürükleyerek düzelt; baştan seçmek istersen **Köşeleri sıfırla** düğmesini kullan.

### Altyazı alanını seç

Sağdaki düzleştirilmiş görüntüde fareyle sürükleyerek altyazıların çıktığı alanı seç. İki satırlık altyazılar da içine sığsın. Alanı çok dar seçersen cümlenin başı veya sonu kesilebilir.

Pencerenin altındaki önizleme, uygulamanın yazı okumak için kullanacağı görüntüyü gösterir.

### Otomatik ayarı çalıştır

1. Oyunda bir altyazı görünmesini bekle. Mümkünse altyazı görünürken oyunu duraklat.
2. **Otomatik ayarla** düğmesine bas.
3. İşlem bitene kadar bekle; yaklaşık 10–60 saniye sürebilir.

Uygulama, düğmeye bastığın andaki görüntü üzerinde farklı ayarları deneyip yazıyı daha iyi okuyabildiği ayarı seçer. Kamera konumunu fiziksel olarak değiştirmez; görüntünün eğimini, yüksekliğini ve altyazı alanını düzenler.

Alttaki **“OCR okudu: …”** satırında oyundaki İngilizce altyazıyı doğru görüyorsan ayar tamam. OCR, görüntüdeki yazıyı metne çeviren bölümün adı.

Yazılar hâlâ basık görünüyorsa “Ekranın alt kısmını” modundaki **Yükseklik düzeltme** kaydırıcısını deneyebilirsin. Yanlış alan seçtiysen **Altyazı alanını sıfırla** düğmesiyle yeniden seç.

Kamera ve alan ayarları kaydedilir. Kamera yerinden oynamadıkça her açılışta bunları tekrarlamana gerek yok.

## 6. Canlı çeviriyi başlat

1. Ana pencereye dön.
2. **Canlı çeviri** kutusunu işaretle.
3. Oyunda yeni bir altyazı çıktığında Türkçe çevirisinin gelmesini bekle.

Uygulama kameradan okunan yazıyı kontrol edip çeviriye gönderir. Aynı altyazı ekranda dururken sürekli yeniden çevrilmez.

Canlı çeviri açıkken kamera ayar penceresini kapatabilirsin; kamera arka planda çalışmaya devam eder. Çeviriyi durdurmak için **Canlı çeviri** kutusunun işaretini kaldır.

## 7. Çevirileri hangi ekranda takip edeceğini seç

### İkinci monitör

1. Uygulamanın ana penceresini ikinci monitöre sürükle.
2. **Tam ekran** düğmesine bas veya **F11** tuşunu kullan.
3. Türkçe çeviri ve İngilizce metin bu monitörde gösterilir.

Tam ekrandan çıkmak için **Esc**'ye bas veya ekrana çift tıkla. **Geçmiş** düğmesiyle önceki replikleri görebilir, arama kutusundan bir kelimeyi arayabilirsin. Canlı görünümde **H** tuşu da geçmişi açar.

### Telefon veya tablet

1. Telefonun ve bilgisayarın aynı yerel ağda olduğundan emin ol. Bilgisayar modeme kabloyla, telefon Wi-Fi ile bağlı olabilir.
2. Uygulamada **Telefonda göster** düğmesine bas.
3. Açılan penceredeki QR kodu telefonun kamerasıyla okut.
4. Bağlantıyı tarayıcıda aç. Anlık çeviriler burada görünür; telefona uygulama kurman gerekmiyor.

Telefondaki **Geçmiş** düğmesinden önceki repliklere bakabilirsin. Paylaşımı kapatmak için bilgisayardaki **Telefonda göster** düğmesine tekrar bas.

Windows Güvenlik Duvarı izin isterse, güvendiğin ev ağında **Özel ağlar** için izin ver. Bu özellik HTTP kullanır; QR kodu ve bağlantıyı bilen, bilgisayarına ağ üzerinden erişebilen kişiler altyazıları ve geçmişi okuyabilir. QR kodunu veya adresi herkese açık bir fotoğraf ya da videoda gösterme.

## Bir şey çalışmazsa

| Sorun | Ne yapabilirsin? |
|---|---|
| Python kurulamadı | Python 3.13'ü elle kur, ardından `setup.bat` dosyasını tekrar çalıştır. |
| Kurulum hata verdi | Terminalin sonundaki hata mesajını kontrol et. Yardım isterken mesajı metin olarak veya ekran görüntüsüyle paylaş. |
| `run.bat` önce kurulum yapmamı istiyor | Aynı klasördeki `setup.bat` dosyasını çalıştır ve “Kurulum tamam” mesajını bekle. |
| Kamera görüntüsü gelmiyor | Kamera listesindeki diğer numaraları dene. Kamerayı kullanan başka programları kapat ve Windows kamera izinlerini kontrol et. |
| “OCR yazı görmedi” yazıyor | Oyunda altyazı açıkken **Otomatik ayarla**'ya bas. Alttaki önizlemede yazının tamamı görünüyor mu kontrol et. |
| Yazı yanlış veya eksik okunuyor | Kameranın odağını ve konumunu düzelt. Seçtiğin alanı genişlet; iki satırın da sığdığından emin ol. |
| İngilizce metin okunuyor ama çeviri gelmiyor | **Canlı çeviri** açık mı kontrol et. Çeviriyi alttaki metin kutusundan dene; açıklama bölümündeki hata mesajına bak. |
| DeepL anahtarı kabul edilmiyor | API anahtarını doğru kopyaladığını kontrol et. İstersen Ayarlar'dan yerel modele geç. |
| Telefonda sayfa açılmıyor | Telefonun mobil veri veya misafir ağı yerine bilgisayarla aynı yerel ağda olduğunu kontrol et. Güvenlik duvarındaki özel ağ iznine bak. |
| Telefonun ekranı kapanıyor | Telefon ayarlarından ekran zaman aşımını uzat. |

## Veriler nerede tutuluyor?

- Kamera görüntüleri uygulama tarafından diske kaydedilmez veya paylaşım sayfasına gönderilmez.
- DeepL seçiliyse altyazı metni ve önceki replik bağlam olarak DeepL'e gönderilir. Servisin veri işleme koşulları için DeepL'in kendi belgelerine bak.
- Yerel model seçiliyse çeviri bilgisayarda yapılır. Model ilk kullanımda Hugging Face'ten indirilir; indirilecek depo sürümü kodda sabitlenmiştir.
- DeepL anahtarı proje klasörüne veya ayar dosyasına yazılmaz; Windows Kimlik Bilgisi Yöneticisi'nde saklanır.
- Telefon paylaşımı varsayılan olarak kapalıdır. Açıldığında İngilizce metin, Türkçe çeviri ve oturumdaki çeviri geçmişi paylaşılır; API anahtarı paylaşılmaz. Bu özelliği güvendiğin ev ağında kullan.
- Çeviri geçmişi uygulama kapanınca silinir.
- Paket sürümleri henüz sabitlenmemiştir; kurulum sırasında indirilen sürümler zamanla değişebilir.

## Eksikler ve katkı

Uygulama Windows'ta İngilizce → Türkçe çeviri için geliştiriliyor. Okuma ve çeviri anlık değildir; kamera görüntüsünün okunması ve metnin çevrilmesi biraz zaman alır. Sonuç, kameraya ve seçtiğin çeviri yöntemine göre değişir.

Bir hata bulursan [issue açabilirsin](https://github.com/tremirhankaya/ps5-game-assistant-translator/issues). Hangi adımda olduğunu, beklediğin sonucu ve varsa hata mesajını yazman yeterli. Ekran görüntüsü eklerken API anahtarını ve telefon paylaşım adresini gizle.

Düzeltme veya geliştirme göndermek istersen PR açabilirsin.

## Lisans ve kullanılan araçlar

Uygulamanın kodu MIT lisanslıdır.

Yazı okuma için [RapidOCR](https://github.com/RapidAI/RapidOCR) kullanılır. Yerel çeviri modeli uygulamayla birlikte dağıtılmaz; ilk kullanımda [Hugging Face'teki CTranslate2 dönüşümünden](https://huggingface.co/ooeoeo/opus-mt-tc-big-en-tr-ct2-float16) indirilir. Kaynak model, Helsinki Üniversitesi Dil Teknolojileri Araştırma Grubu'nun [OPUS-MT](https://github.com/Helsinki-NLP/Opus-MT) projesindeki `opus-mt-tc-big-en-tr` modelidir (CC BY 4.0).
