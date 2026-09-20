# P1.15.b — Accepted two-leg fill projection

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/two_leg_fill_projection.py`
- Test: `tests/test_two_leg_fill_projection.py`
- Bağımsız review: `PASS` (Bohr salt-okunur Codex incelemesi, düzeltme sonrası)
- Production readiness: `NO`
- Sonraki tek iş: `P1.15.c` two-leg persistence/replay/recovery karar kapısı

P1.15 araştırmasındaki güvenli alt kapsamdan, aynı account/venue-profile/product/symbol kapsamındaki HEDGE LONG/SHORT iki ayağın kabul edilmiş fill projection’ı uygulandı. Projection immutable ve yalnız in-memory’dir; order, reserve, persistence veya venue authority değildir.

## Uygulanan sözleşme

- `LegFill` yalnız `A` veya `B` leg’i, explicit fill identity, integer `event_time_us`, pozitif exact decimal quantity ve `PARTIAL`/`FULL` status kabul eder.
- İlk accepted fill `A` leg’ine ait olmalıdır; iki leg aynı HEDGE side’ı taşıyamaz.
- Aynı scope dışındaki account, venue profile, product veya symbol fill’i fail-closed reddedilir.
- Leg miktarları Fraction tabanlı exact aritmetik ile canonical decimal string olarak toplanır; istenen toplam quantity bu mikro-fazda tanımlı olmadığı için conservation iddiası yapılmaz.
- `PARTIAL` veya yalnız ilk leg’in `FULL` olması ara state’i kaybetmez: `PARTIAL_HEDGE` ve `ONE_LEG_FILLED` görünür kalır; iki leg `FULL` olduğunda `BOTH_ESTABLISHED` oluşur.
- Exact duplicate aynı immutable fill payload’ında no-op’tur; aynı fill ID’nin farklı payload’ı `TWO_LEG_FILL_CONFLICT` olarak reddedilir.
- Yeni event zamanı önceki accepted fill’den geriye gidemez; tamamlanmış leg’e yeni non-duplicate fill kabul edilmez.
- Public projection kurucusu state, identity pair, fill history, aggregate quantity ve status tutarlılığını yeniden doğrular; malformed projection güvenilir ekonomik state gibi kabul edilmez.
- State/leg/status whitelist’leri exact string tipini zorunlu kılar; custom equality nesneleri allowlist’i aşamaz.

## Bilinçli kapsam dışı

Persistence/reopen/replay ledger, crash recovery, late-fill recovery policy, cross-account capacity, reduce-only, margin/collateral/liquidation, cross/isolated numeric model, venue adapter, order/reserve binding, API/UI ve ekonomik posting bu mikro-fazda açılmadı. Cross-unit conversion ve miktar hedefi/korunumu tanımlanmadığı için numeric sonuç üretilmedi.

`docs/P1_KRITIK_ARASTIRMA_FINAL/test_matrices/P1.15_TESTS.md` mevcut ancak
`SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE`; bu nedenle implementation için
tek başına kabul kanıtı sayılmadı.

## Kontroller

- Önce test RED: public projection constructor’ı tutarsız state’i ve custom equality whitelist girdisini reddetmedi; `6` odak testte `2` failure görüldü.
- Minimal uygulama sonrası odak regresyon `7/7 PASS`; hedge sözleşmesiyle ilgili küme `11/11 PASS`.
- Bağımsız accepted-fill/oracle control: `A PARTIAL → B FULL → A FULL`, exact miktar, ara state, duplicate/conflict, immutable history ve malformed constructor kontrolleri `PASS`.
- Bundled Python `3.12.14` ile `python -m compileall -q src`: `PASS`.
- `git diff --check`: `PASS`.
- `tools/run_checks.py` ve `tools/check_workspace.py`: `FAIL`, çünkü proje Python `3.13` isterken kullanılabilir bundled runtime `3.12.14`; güncel tam-suite/workspace sonucu iddia edilmiyor.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md` first-leg accepted fill’in geri alınmamasını, `ONE_LEG_FILLED`/`PARTIAL_HEDGE` ara durumlarını, iki leg’in ayrı izlenmesini ve duplicate/replay invariance gereğini destekler; persistence/recovery, cross ownership ve venue-specific risk davranışlarını sonraki karar kapılarına bırakır.
