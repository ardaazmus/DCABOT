# P1.12.e — Fixed-tier isolated liquidation estimate sonucu

**Tarih:** 2026-09-16
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/application/isolated_liquidation.py` yalnız one-way isolated
pozisyon için, immutable risk-tier + isolated margin + timestamped mark
snapshot girdileriyle analitik long/short liquidation kökü üretir. Çıktı
`ESTIMATE_ONLY` olarak işaretlenir.

Pozisyon/core binding, order/fill, cross/hedge, partial liquidation,
bankruptcy, ADL, canlı Binance transport ve mutation kapsam dışıdır.

## Kabul kanıtı

- `3/3` odak test PASS: long/short bağımsız kökler, authority/tier sınırları,
  exact decimal’e sığmayan kök.
- Tier dışına çıkan kök `LIQUIDATION_TIER_MISMATCH` ile reddedilir.
- Risk tier etkinliğinden eski margin snapshot reddedilir.
- Non-terminating sonuç sessiz yuvarlanmaz; `LIQUIDATION_RESULT_NOT_REPRESENTABLE`
  olarak reddedilir.
- Tam proje kontrolü `tools/run_checks.py`: `502/502 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Sınır

Bu sonuç yalnız fixed-tier matematik oracle’ıdır. Gerçek venue liquidation
parity’si, tier geçişleri, close/liquidation cost, cross account state,
partial liquidation, bankruptcy ve ADL için ayrı araştırma ve bağımsız kabul
kapısı gerekir.
