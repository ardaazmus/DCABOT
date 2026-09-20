# P1.12.f.h.aj — Immutable Futures DCA → CORE01 mapping contract

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- Futures DCA accepted event ve economic posting’i, açık bir CORE01 mapping
  candidate sözleşmesiyle eşleştiren saf doğrulayıcı eklendi.
- Mapping; `profile_revision_id`, `core_order_id`, `core_order_intent_id`,
  `role`, `side` ve exact `limit_price` alanlarını zorunlu taşıyor.
- Posting source/commitment/fee ve event/profile identity eşleşmeden candidate
  üretilmiyor; BUY/SELL limit kuralı ve CORE01 destekli role kümesi
  (`BASE`, `SAFETY:n`, `EXIT`, `STOP`) doğrulanıyor.
- Candidate yalnız immutable, non-economic bir sözleşmedir. CORE01 `State`,
  `Store`, order intent veya posting mutation’ı yapmaz; venue order’ından
  side/role/intent varsaymaz.

## Kanıt

- Mapping contract odak testleri: `5/5 PASS`.
- Hedefli Futures DCA release/posting/binding kümesi: `28/28 PASS`.
- Tam proje: `tools/run_checks.py` — `583/583 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- Canlı Binance emri, mutation, mainnet, secret, CORE01 Store yazımı veya
  cross-database atomicity çalıştırılmadı.

## Sıradaki tek iş

`P1.12.f.h.ak` — immutable mapping candidate’ı mevcut CORE01 state ile
mutasyonsuz scope/order eşleşmesi üzerinden kabul etmeye hazırlayan offline
admission oracle’ı.
