# P1.12.f.h.m — Immutable profile revision insert/replay kapısı

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; event binding `NO-GO`

## Kanıt

Yeni v1 journal içinde yalnız immutable Futures DCA profile revision yazımı
açıldı. Revision; venue/product/symbol, settlement/margin/position mode,
effective time, explicit contract-size ve fee/slippage/rounding policy
revision kimliklerini taşır. Canonical profile hash ile doğrulanır.

- aynı revision ve aynı payload: `DUPLICATE`;
- aynı revision ve farklı payload: `FUTURES_DCA_PROFILE_CONFLICT`;
- sıfır veya geçersiz contract-size: fail-closed;
- restart replay: aynı immutable profile tuple’ını döndürür.

Odak test: `tests/test_futures_dca_journal_schema.py` — `4/4 PASS`.
Tam proje kontrolü `tools/run_checks.py` — `537/537 PASS` (yükseltilmiş yerel
Windows Credential Manager erişimiyle).

## Sınır

Bu kapı event, reservation, fill-release, economic posting, funding,
fee/slippage hesabı veya canlı venue authority açmaz. Policy revision
kimlikleri yalnız scope alanıdır; ekonomik içerikleri bu fazda varsayılmadı.

## Sonraki tek iş

Profile revision’a bağlı event envelope için immutable identity ve checksum
validator’ı eklenmeli; event kabulü reservation/posting binding’i olmadan
yalnız bounded journal sınırında kalmalıdır.
