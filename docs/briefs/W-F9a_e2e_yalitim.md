# muse — Görev W-F9a: e2e yalıtımı + kararlılık + küçük görsel düzeltmeler

İşbölümü aynı: yalnız bu görev, bana rapor. `STATE.md`, `TASK.md`, `docs/KARARLAR.md`, `src/` ve `web/src/lib/decimal.ts` değiştirilmez.

## W-F3 geri bildirimi
W-F4.1 + W-F3 kabul edildi. vitest 127/127; görüntüler eksiksiz. Ancak iki tam e2e koşumda iki farklı test düştü:
1. **`settings.spec.ts` "yedek alınır ve listede görünür"** — beklenen 26, görünen 25. Her e2e koşusu kullanıcının gerçek `data/backups` klasörüne yedek yazıyor; sayı 25'i geçti, tablo sayfa başına 25 satır gösteriyor. Bu test bundan sonra her koşuda düşer.
2. **`market.spec.ts` "erişilebilirlik: kritik ihlal yok"** — tam koşuda düştü, tek başına geçti (kararsız).

## Backend değişikliği (hazır)
`DCABOT_DATA_DIR` ortam değişkeni (mutlak yol) API'nin tüm değişken durumunu o klasöre taşır: yedekler, botlar, kill switch, mum önbelleği, geçmiş koşular, dataset önbelleği, tek-worker kilidi. Tanımlı değilse bugünkü `data/`. Kilit de klasöre bağlı olduğu için e2e API'si senin geliştirme API'nle aynı anda çalışabilir.

## Yapılacaklar
### A. e2e yalıtımı
1. **`playwright.config.ts` `webServer` iki süreç başlatır:**
   - **API:** `uv run --frozen uvicorn dcabot.server.api:app --host 127.0.0.1 --port 8001`
     - Repo kökünden, `PYTHONPATH=src`.
     - `DCABOT_DATA_DIR=<repo>/web/.e2e-data` (mutlak yol).
     - `url`: `http://127.0.0.1:8001/api/health`.
   - **Web:** `next dev --port 3001`, `DCABOT_API_URL=http://127.0.0.1:8001`.
   - `baseURL` 3001. `reuseExistingServer: false`, yani her koşuda temiz başlar. Geliştirme sunucuların (8000/3000) açık kalabilir; çakışmaz.
2. **`globalSetup`:**
   - `web/.e2e-data`'yı silip yeniden oluştur.
   - Repo `data/public_cache` klasörünü içine **kopyala**. Dataset testi VERIFIED kaydı bekliyor; kopya salt okunur kaynaktan yapılır, asıl klasöre yazılmaz.
   - `web/.e2e-data` `.gitignore`'a eklenir.
3. **CI'daki e2e işi:** elle başlatılan backend adımını kaldır; Playwright `webServer` her şeyi başlatır.
4. **Sayıya bağlı testler:**
   - Yedek testi artık "önce N, sonra N+1 satır" saymaz. Yeni yedeğin dosya adının listede göründüğünü doğrular; tabloda sıralama ya da ilk sayfa kontrolü kullan.
   - `bots-list.png` tabanının test sırasına bağımlılığı (sapma 3) giderilsin: liste testi kendi botlarını oluşturur ve sayar.
5. **Kararsız a11y testi:**
   - Kök nedeni bul. Trace ya da `error-context`'te hangi axe kuralı düşüyor? Muhtemelen tablo satırları yüklenmeden analiz yapılıyor.
   - Analizi içerik yüklendikten sonra yap.
   - `retries` artırarak **gizleme**.
6. **Kabul:** tam paket üst üste **3 koşu** yeşil. Her koşudan sonra `data/backups`'taki dosya sayısı ve `data/bots.sqlite3`'ün değiştirilme zamanı değişmemiş olmalı; bunu raporda göster.

### B. Küçük görsel düzeltmeler (W-F3)
1. **Aylık getiri:** ay etiketi "Eyl 2026" biçiminde (TR/EN yerel ay adı), değer `%−0,01` biçiminde (`formatDecimal`, 2 ondalık, yüzde işareti).
2. **Equity x ekseni:** aynı gün etiketi iki kez görünüyor ("14 14"). Eksen biçimleyicide tekrar eden etiketi bastır.
3. **Ondalık girişi:** strateji ve bütçe alanlarında kullanıcı "1,5" yazarsa gönderilen metin "1.5" olur. Bu yalnız metin dönüşümüdür, hesap değildir. Binlik ayırıcı nokta ("1.000") kabul edilmez: alan altında "Ondalık için virgül ya da nokta kullanın, binlik ayırıcı kullanmayın" uyarısı. Birim testi.
4. **Hydration uyarısı:** raporundaki `/` başlığı uyarısının kök nedeni bulunup giderilir (büyük olasılıkla tema ya da dil istemcide farklı render oluyor).

## Rapor
Her zamanki biçimde.

Ek olarak:
- 3 ardışık tam koşunun son satırları.
- Koşu öncesi ve sonrası `data/backups` dosya sayısı ile `data/bots.sqlite3` değiştirilme zamanı.
- Kararsız a11y testinin kök nedeni.
