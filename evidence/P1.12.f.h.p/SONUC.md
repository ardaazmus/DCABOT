# P1.12.f.h.p — Event + reservation atomic coordinator kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; release/posting ve legacy split-store migration `NO-GO`

## Kanıt

Profile-bound immutable event ile `source_event_id` üzerinden ona bağlı
reservation artık bounded Futures DCA journal’ında tek SQLite transaction’ında
yazılabiliyor. Coordinator:

- event profile scope, sequence, identity ve exact payload kurallarını korur;
- reservation’ın source event’inin coordinator event’i olmasını zorunlu kılar;
- iki kayıt da exact duplicate ise `DUPLICATE`, yeni kayıt varsa `ACCEPTED`
  döndürür;
- farklı payload, source mismatch veya eksik profile/event fail-closed kalır;
- reservation insert’ine SQLite trigger ile injected failure verildiğinde event
  de rollback olur; restart sonrası iki projection da boştur.

Odak test: `tests/test_futures_dca_journal_schema.py` — `10/10 PASS`.  
Tam proje kontrolü `tools/run_checks.py` — `543/543 PASS` (çalışan runtime’a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu coordinator yeni bounded journal şemasını doğrular; mevcut ayrı
`FuturesDcaEventStore` ve `ReservationLedger` verisini otomatik taşımaz. Eksik
profile, contract-size/multiplier, fee/slippage/rounding, release identity veya
posting alanları varsayımla doldurulmaz. Release transition,
partial/cancel/late/UNKNOWN ekonomik otoritesi, funding, position/core binding
ve canlı venue authority açılmadı.

## Sonraki tek iş

Mevcut split Futures DCA store’larının satırlarını read-only envanterleyip,
eksik ekonomik alanlar için güvenli migration kapsamını belirlemek; kanıt
yeterli değilse migration’ı `NO-GO` olarak bırakmaktır.
