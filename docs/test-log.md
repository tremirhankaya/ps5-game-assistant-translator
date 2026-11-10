# Test kaydı

## T-001 — DisplayWidget Center statik analiz (2026-11-10)
**Monitör:** ASUS ROG Strix XG27ACG (FW 101).
**Yöntem:** `C:\Program Files (x86)\ASUS\DisplayWidgetCenter` salt okunur incelendi (dosya listesi + strings). Monitöre hiçbir komut gönderilmedi.

**Bulgular**
- Uygulama monitörle standart Windows DDC/CI API'si ile konuşuyor: `AsusDisplayMonitorInfo.dll` → `dxva2.dll`. Özel sürücü yok.
- GamePlus Crosshair = VCP **0xE3** (hazır stil seçimi). Display Alignment = VCP **0xE7** (aç/kapa).
- Uygulama yazdıktan sonra geri okuyarak doğruluyor.
- "EZOSD" Windows tarafında çizilen bir pencere, monitör OSD'si değil.

## T-002 — ControlMyMonitor VCP dökümü + capability string (2026-11-10)
**Yöntem:** ControlMyMonitor salt okunur; `C:\ProgramData\ASUS\DisplayWidgetCenter\UserConfig\CapabilityData.json` okundu.

**Bulgular**
- Capability: `cmds(01 02 03 07 0C E3 F3)` → yalnızca VCP oku/yaz, timing, kaydet, capabilities. **Table Write yok.**
- 0x60 Input: 15 = DisplayPort, 17 = HDMI, 26 = USB-C.
- 0xE3: 0 = kapalı, 7–12 = 6 hazır crosshair stili. Crosshair açılınca değer 0 → 7 oldu.
- 0xE9: 5150 (0x141E), max 25720. Konum olabileceği düşünüldü; crosshair taşındıktan sonra değer değişmedi.
- DisplayWidget logları şifreli.

**Sonuç:** GamePlus/DDC ile PS5 görüntüsüne metin çizmek mümkün değil.

## T-005 — Donanım PiP/PBP (2026-11-10)
- DisplayWidget "MultiScreen > MultiFrame" bir Windows pencere yerleşim aracı, donanım PiP değil.
- Resmi XG27ACG özelliklerinde PiP/PBP yok; OSD'de de bulunamadı.
- HDMI 2.0 girişi 48–144 Hz → PS5 1440p/120 mümkün.

**Sonuç:** Monitörün kendi donanımıyla PS5 görüntüsüne overlay yolu yok.

## Açık / opsiyonel
- T-003: Crosshair konum kodu.
- T-004: Giriş HDMI iken PC'den crosshair değişikliği görünüyor mu?
