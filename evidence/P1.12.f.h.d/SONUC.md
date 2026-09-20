# P1.12.f.h.d — Futures DCA profile-revision kapsam kapısı

**Tarih:** 2026-09-17  
**Durum:** `DEFERRED / NO-GO / LOCAL_PASS`

## Bulgu

`FuturesDcaProfile` ürün ailesi, settlement/margin, position mode, margin
mode ve leverage bağlamını taşır; ancak `symbol`, `effective_time` veya
profile-revision kimliği taşımaz. Bu nedenle aynı profile farklı sembol,
venue snapshot’ı ya da zaman sürümüymüş gibi ekonomik commitment bağlamak
güvenli değildir.

## Karar

Contract semantics ancak venue + symbol + effective time + immutable profile
revision ile birlikte kabul edilebilir. Mevcut profile bu scope authority’sini
taşımadığı için DCA fill/reservation/economic posting binding açılmadı. Yeni
alanlar için kaynaklı snapshot formatı ve revision değişiminde replay policy
ayrıca tanımlanmalıdır.

## Kabul kanıtı

- Odak test: `1/1 PASS`.
- Test mevcut public profile’ın sembol/zaman/revision authority iddia
  etmediğini doğrular.
- Üretim kodu, veri, credential, canlı çağrı/emir ve dependency değişmedi.
- Tam proje kontrolü `tools/run_checks.py`: `527/527 PASS`; compile, workspace
  ve release-manifest kontrolleri PASS.

Sıradaki tek iş, bu revision scope ile fee/slippage/rounding ve
partial/cancel/late/UNKNOWN release kurallarını aynı bounded journal
transaction sözleşmesinde birleştirmektir.
