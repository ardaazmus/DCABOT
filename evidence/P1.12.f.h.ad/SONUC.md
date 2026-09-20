# P1.12.f.h.ad — Greenfield ürün teslim sınırı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
**Legacy migration/publish:** `NOT_APPLICABLE` — ürün yeni kuruluyor

## Karar

DCABOT için başlangıçta içe aktarılacak eski bir üretim veritabanı, işlem
kaydı veya kullanıcı tarafından hazırlanmış kaynak export beklenmeyecek.
Futures DCA/Grid ürünü boş durumdan, kendi kanonik domain ve persistence
sözleşmeleriyle oluşturulacak.

Eski başarısız DCA projesi ve `YEDEK_ESKI_PROJE` içeriği ise veri migration
kaynağı değil, seçici teknik referanstır. Doğrulanmış ve kaliteli bir algoritma,
test yaklaşımı veya UI/UX fikri gerektiğinde mevcut aktif kodla karşılaştırılır;
uyumluysa kontrollü biçimde yeniden kullanılabilir. Bu kullanım
`docs/YEDEKTEN_AKTARIM.md` ve `reuse/REGISTER.md` kanıt akışına bağlıdır.
Yedek runtime’a otomatik bağlanmaz, eski talimatlar yeni plana dönüşmez.

Kullanıcının test çalıştırması, gerçek emir vermesi veya gerçek işlem kaydı
oluşturması bu fazın ön koşulu değildir. Önceki `source-to-target` ve
`publish-readiness` zinciri yalnız gelecekteki legacy import için güvenlik
sınırı olarak korunur; ürün teslimatının aktif bağımlılığı değildir.

## Doğrulama

- Proje içindeki mevcut split store ve journal kodu incelendi.
- Gerçek kullanıcı kaydı veya eski üretim export’u bulunmadığı doğrulandı.
- `562/562 PASS` mevcut yerel, offline regresyon kanıtıdır; kullanıcı testi
  veya Binance işlem kanıtı değildir.
- Binance Testnet mutation, mainnet, secret ve canlı emir açılmadı.

## Sonraki tek iş

`P1.12.f.h.ae` — greenfield Futures DCA journal’ında event + reservation +
fill-release + economic-posting cursor sahipliğini kanonik tek akışta
uygulama ve failure/replay testleri.
