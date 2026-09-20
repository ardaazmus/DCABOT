# P1.12.f.h.o — Minimum reservation projection kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; release/atomic binding `NO-GO`

## Kanıt

V1 Futures DCA journal şemasındaki `reservations` sahibi artık minimum exact
projection olarak yazılıp replay ediliyor. Projection şu alanları koruyor:

- reservation identity, owner scope ve asset;
- exact `reserved_amount`, `consumed_amount` ve `releasable_amount`;
- optional release identity ve opaque terminal state;
- monotonic kararını henüz vermeyen version alanı;
- optional, mevcut immutable journal event’ine source reference.

Kurallar:

- exact duplicate `DUPLICATE`, farklı payload `CONFLICT`;
- negatif veya bozuk ekonomik alanlar fail-closed;
- source event verilmişse mevcut event olmadan reservation yazılmaz;
- restart sonrası reservation projection aynı exact değerlerle replay edilir.

Odak test: `tests/test_futures_dca_journal_schema.py` — `8/8 PASS`.  
Tam proje kontrolü `tools/run_checks.py` — `541/541 PASS` (çalışan runtime’a
dokunmadan izole, kilitli bağımlılık ortamında).

## Sınır

Bu faz event ve reservation’ı aynı transaction’da bağlamaz; release transition,
partial/cancel/late/UNKNOWN ekonomik otoritesi, fee/slippage/funding posting,
position/core binding, venue authority ve migration yapmaz. `consumed_amount`
ile `releasable_amount` için ekonomik toplam kuralı da varsayılmadı.

## Sonraki tek iş

Event + reservation atomic coordinator için failure-injection sınırı gerçek
Futures DCA kaynaklarına bağlanmalı; release ve posting ancak immutable ekonomik
kurallar ile bağımsız doğrulama kapısından sonra açılmalıdır.
