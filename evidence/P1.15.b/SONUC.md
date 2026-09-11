# P1.15.b — Accepted two-leg fill projection

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/two_leg_fill_projection.py`
- Test: `tests/test_two_leg_fill_projection.py`
- Bağımsız review: `NOT_RUN`
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

## Bilinçli kapsam dışı

Persistence/reopen/replay ledger, crash recovery, late-fill recovery policy, cross-account capacity, reduce-only, margin/collateral/liquidation, cross/isolated numeric model, venue adapter, order/reserve binding, API/UI ve ekonomik posting bu mikro-fazda açılmadı. Cross-unit conversion ve miktar hedefi/korunumu tanımlanmadığı için numeric sonuç üretilmedi.

`test_matrices/P1.15_TESTS.md` bu checkout’ta bulunmuyor; bu sınırlama kayda alındı.

## Kontroller

- Önce test RED: yeni test dosyası eksik `two_leg_fill_projection` modülü nedeniyle `295` testte beklenen import error verdi.
- Minimal uygulama sonrası `uv run --frozen python tools/run_checks.py`: `298/298 PASS`.
- Bağımsız accepted-fill control: `A PARTIAL → B FULL → A FULL`, exact miktar, ara state, duplicate no-op: `INDEPENDENT_CONTROL_PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `126` aktif Python dosyası.
- Live/testnet, credential ve gerçek emir yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md` first-leg accepted fill’in geri alınmamasını, `ONE_LEG_FILLED`/`PARTIAL_HEDGE` ara durumlarını, iki leg’in ayrı izlenmesini ve duplicate/replay invariance gereğini destekler; persistence/recovery, cross ownership ve venue-specific risk davranışlarını sonraki karar kapılarına bırakır.
