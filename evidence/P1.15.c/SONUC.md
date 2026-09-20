# P1.15.c — Two-leg persistence/replay/recovery karar kapısı

## Karar

- Durum: `DEFERRED / NO-GO / LOCAL_PASS`
- Kod değişikliği: yok
- Bağımsız review: `PASS` (Beauvoir salt-okunur Codex incelemesi)
- Production readiness: `NO`
- Sonraki güvenli tek iş: `P1.16.a` chronological split ve leakage-free evaluation sınırı

Bu turda persistence/replay/recovery üretim kodu yazılmadı. Araştırma sözleşmesi ve mevcut iki store’un gerçek şeması, P1.15.b’deki in-memory `TwoLegFillProjection`’ı güvenli biçimde kalıcı ekonomik kayda bağlamak için gerekli kimlik, zaman, model lineage, recovery ve tek transaction sahipliğini birlikte sağlamıyor.

## Kanıtlanan mevcut durum

- `src/dcabot/persistence/lifecycle_store.py` gerçek restart/replay ve duplicate/conflict koruması taşıyor; ancak metadata kapsamı açıkça `NON_ECONOMIC_LIFECYCLE_ONLY`. Şeması yalnız lifecycle event/config revision alanlarını içeriyor; hedge leg, side, quantity, `event_time_us`, effective/persistence time veya economic payload alanları yok.
- `src/dcabot/persistence/store.py` generic economic `FILL`/posting journal’ıdır; `execution_id` dedup ve payload hash taşır. P1.15 two-leg identity, leg bazlı quantity/status, position mode/side, effective event time ve recovery state için versioned contract taşımaz.
- P1.15.b projection immutable in-memory’dür; canonical serialize/hash, export/import, persistent append ve replay adapter’ı yoktur.
- Araştırma belgesi persistence için event identity + economic payload + ordering/effective time + model/config/dataset/kernel/schema/canonicalization version’larını ve deterministic replay’i; recovery için local code/selected profile kanıtını ister. `docs/P1_KRITIK_ARASTIRMA_FINAL/test_matrices/P1.15_TESTS.md` mevcut, fakat `SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE` durumundadır.
- Lifecycle store ile economic Store’u sonradan bağlayan bir adapter tek transaction atomicity’sini kanıtlamaz; iki ayrı kaynağı “persist edildi” saymak güvenli değildir.

## Neden kod açılmadı

Eksik sözleşme kapanmadan yeni SQLite şeması veya adapter eklemek; aynı accepted fill’in iki kez ekonomikleşmesi, bir leg’in kaydedilip diğerinin kaybolması, replay’de farklı state üretilmesi ya da recovery gerektiren olayın tamamlanmış görünmesi risklerini açık bırakır. Bu nedenle güvenli karar `DEFER/NO-GO`’dur; herhangi bir numeric recovery veya cross/liq varsayımı eklenmedi.

## Gerekli sonraki girişler

P1.15.c yeniden açılmadan önce tek bir seçilmiş persistence sahibi ve migration/version planı; canonical event schema; `event_time/effective_time/persistence_time` ayrımı; two-leg scope/leg identity; duplicate/conflict ve late-fill recovery kararları; atomic accepted-fill + projection transition sınırı; crash/reopen/replay/property test matrisi; independent field-level oracle ve gerekiyorsa selected venue/profile kanıtı tamamlanmalıdır.

## Kontroller

- Persistence sınır regresyonu: `tests.test_lifecycle_store` + `tests.test_engine_store` → `30/30 PASS`.
- Bağımsız şema kontrolü: mevcut lifecycle store metadata scope’u, `lifecycle_events` kolonları, generic economic `events` kolonları ve two-leg alanlarının yokluğu doğrulandı; `INDEPENDENT_STORAGE_SCHEMA_CONTROL_PASS`.
- Bundled Python `3.12.14` ile `python -m compileall -q src tests` → `PASS`.
- `tools/run_checks.py` ve `tools/check_workspace.py` → `FAIL`, çünkü proje Python `3.13` isterken kullanılabilir bundled runtime `3.12.14`; güncel tam-suite/workspace sonucu iddia edilmiyor.
- Hiçbir persistence migration, economic Store değişikliği, API/UI, live/testnet veya credential yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md` recovery’yi `LOCAL_CODE_REQUIRED` olarak sınıflandırır; deterministic replay, event identity, effective ordering, model lineage, field-level oracle ve duplicate/replay invariance ister. Aynı belge cross ownership, one-leg liquidation ve venue-specific risk davranışlarını da bu karar kapısının dışında bırakır.
