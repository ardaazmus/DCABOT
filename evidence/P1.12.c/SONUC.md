# P1.12.c — Linear futures fee/funding event projection

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/linear_futures_math.py` içinde persistence’sız immutable ledger-event projection eklendi:

- `TRADING_FEE` pozitif gider, `FUNDING` işaretli settlement-asset cashflow olarak ayrı tutulur.
- Her event `event_id`, `effective_time_us`, asset ve exact amount taşır.
- Event zamanı geriye gidemez; aynı kimlik ve aynı payload idempotenttir; aynı kimlik/farklı payload conflict’tir.
- Net realized projection `gross_realized - fee_expense + funding_cashflow` ile hesaplanır.
- Fee/funding state’i core spot reducer’ı, SQLite persistence’i veya UI’yı mutate etmez.

## Doğrulama zinciri

- RED: event projection sembolleri yokken yeni suite import failure.
- GREEN: tam regresyon `251/251 PASS`.
- Bağımsız kontrol: production import etmeden Decimal oracle `PASS`; gross `1500 - fee 0.5 + funding -5.25 = net 1494.25`, duplicate delta `0`.
- Workspace/compile: `uv run --frozen python tools/check_workspace.py` → `PASS`; `106` aktif Python dosyası.
- Negative kontroller: conflicting duplicate, out-of-order event ve settlement asset mismatch fail-closed reddedildi.

## Araştırma temeli

`docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md` F07/F08 ve event/replay matrisi fee ile funding’in ayrı ledger kalemleri olmasını; P1.12.a araştırması ise funding’in timestamped event olmasını destekler. Yerel core `Store` generic funding/fee posting taşısa da futures owner/profile binding’i ayrıca kanıtlanmalıdır.

## Açık sınır ve üretim kararı

Bu projection persistent değildir; event’ler process restart sonrası korunmaz ve mevcut `Store` journal’ına bağlanmaz. Funding schedule/rate dataset’i, fee tier/maker-taker ve per-fill rounding, position/account owner, cross-database atomicity, API/UI ve venue profile yoktur. Bu nedenle futures net-result production readiness `NO`; yalnız doğrulanmış saf matematik sınırı tamamdır.

## Sonraki tek iş

`P1.12.d` — timestamped fee/funding event’lerinin mevcut economic Store içinde kalıcı replay/idempotency binding karar kapısı.
