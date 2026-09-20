# P1.12.f.h.q — Split-store migration kapsam envanteri

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; migration `NO-GO`

## Kanıt

Read-only migration preflight mevcut `FuturesDcaEventStore` ve
`ReservationLedger` kaynaklarını v1 journal’ın tam immutable alan envanteriyle
karşılaştıracak şekilde genişletildi. Envanter artık profile, event/execution,
reservation ve posting sahiplerinin tamamını kapsıyor; eksik alanlar default
değerle kapatılmıyor.

Gerçek split kaynaklarda yalnız event identity/sequence/hash ile reservation
identity/owner/amount karşılıkları gözleniyor. Profile revision ve contract-size,
execution ekonomik alanları, release/version/state, source-event ve posting
alanları eksik kaldığı için sonuç `NO_GO` oluyor.

Odak testler: migration preflight + journal coordinator — `11/11 PASS`.  
Tam proje kontrolü `tools/run_checks.py` — `543/543 PASS` (çalışan runtime’a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu faz yalnız alan envanteri ve migration karar kapısıdır; mevcut split store
verisi taşınmadı, journal hedefi doldurulmadı, eksik fee/slippage/rounding veya
release/posting alanları tahmin edilmedi. Canlı venue, order mutation ve core
economic binding açılmadı.

## Sonraki tek iş

Eksik profile/economic/release/posting alanlarının üretileceği kaynak sözleşmesini
ayrı ve exact bir karar kapısı olarak tanımlamak; kanıtlanamayan alanlar için
migration’ı `NO-GO` tutmaktır.
