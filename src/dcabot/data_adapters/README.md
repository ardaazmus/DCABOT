# data_adapters — port deseni sözleşmesi (B.6)

Bu dizin, DCABOT'un dış dünyayla konuşan TEK katmanıdır: yerel dosyalar,
herkese açık piyasa verisi ve Binance testnet. Ekonomik karar (`domain/`,
`application/` motorları) buraya girmez; bu dizin karar almaz, taşır.

## Yön ve portlar

- Bağımlılık yönü: `application/` → `data_adapters/` → (`domain/`
  tipleri). Adaptörler `application/`'dan yalnız imza/kimlik/sözleşme
  modüllerini (`credential_boundary`, `signed_request`,
  `order_list_contract`, `reconciliation` tipleri) tüketir; motor,
  emir-karar veya plan mantığı import edilmez.
- Uygulama-tarafı port sözleşmeleri `src/dcabot/ports/` içindedir
  (`Journal`: `transact`/`load`/`audit`; depolama ayrıntısı adaptöründür).
- Her taşıma modülü, test-enjekte edilebilir `typing.Protocol`
  seam'leri tanımlar (`*Response` + `*Opener`, soketlerde `*Socket`):
  üretim urllib/websocket nesnelerini, testler fake'leri verir. Ağ ve
  saate karşı gerçek test yazılmaz.

## Üç aile (13 modül) + capability matrisi

`capabilities.py` (C.4): hangi venue/mod'un hangi yönü desteklediğini
kaydeden salt-okunur matris (`VenueCapability` + `supports()`; bilinmeyen
kayıt fail-closed `CapabilityError`). Tüketimi (C.5/P4) ayrı dilim.

Yerel/çevrimdışı (ağ yok, kararlı):
`public_sources` (allowlist'li indirme sözleşmeleri),
`public_download` (sınırlı HTTPS + atomik cache),
`download_jobs` (bellek-içi iş orkestrasyonu),
`catalog` (seçim sözleşmesi), `historical` (salt-okunur kanonik barlar),
`quality` (salt-okunur CSV/ZIP kontrolleri).

Herkese açık piyasa (credential YOK):
`public_feed` (gözlem + reconnect kapısı; aday/emir/bakiye üretmez),
`binance_public` (ağsız normalizasyon — soket açmaz),
`binance_public_transport` (herkese açık REST+WS açabilen TEK modül;
yanıtlar sınırlanır, salt-okunur gözleme indirgenir).

Testnet (imzalı):
`binance_testnet_public` (salt-okunur snapshot),
`binance_testnet_account` (salt-okunur HMAC hesap okuma),
`binance_testnet_user_stream` (salt-okunur kullanıcı WS),
`binance_testnet_order_execution` (gerçek emir verebilen TEK modül;
Faz 3.4 mutation gate'i — kill-switch, `max_entry_notional`,
idempotent `clientOrderId` + `AttemptStore`, tek-uçuş, testnet-only URL).

## Değişmez kurallar

1. Sınırlı I/O: her yanıt bayt/sayı sınırından geçer, sonra çözülür.
2. Fail-closed: tip'li hata (`*Error`), sessiz varsayılan yok; UNKNOWN
   asla başarı sayılmaz.
3. Salt-okunur varsayılan; mutation yalnız `order_execution` içinden
   ve gate ile.
4. Taşıma/normalizasyon ayrımı: soket açan modül normalize etmez,
   normalize eden modül soket açmaz.
5. Secret dosyaya/fixture'a/log'a girmez; kimlik bilgisi yalnız
   `credential_boundary` üzerinden akar.

## Yeni venue ekleme (P4 — Arda onayı ŞART, mainnet NO-GO)

1. `public_<venue>.py` (ağsız normalizasyon) + `<venue>_transport.py`
   (sınırlı taşıma, `*Response`/`*Opener` seam'leriyle) yaz.
2. Testnet gerekiyorsa salt-okunur modülleri çoğalt; mutation ASLA yeni
   dosyaya taşınmaz — `binance_testnet_order_execution` tek kalır
   (çok-venue emir ayrı ürün/ekonomi kararıdır).
3. Önce fake-seam'li testler, sonra checker yeşili. Yeni borsa bu
   dilimde EKLENMEDİ — yalnız desen belgelendi.
