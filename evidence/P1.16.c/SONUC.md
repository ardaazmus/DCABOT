# P1.16.c — Feature/label horizon overlap ve purge kararı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/horizon_overlap.py`
- Test: `tests/test_horizon_overlap.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.d` multiple-testing trial registry karar kapısı

P1.16 araştırmasındaki feature/label horizon overlap kontrolünün güvenli, generic alt parçası uygulandı. Half-open integer zaman aralıkları `[start_time_us, end_time_us)` karşılaştırılıyor; sınırda birleşen aralık overlap sayılmıyor. Overlap varsa `PURGE_REQUIRED`, yoksa `NO_OVERLAP` sonucu dönüyor.

## Uygulanan sözleşme

- `TimeInterval` pozitif ve non-negative integer zamanlarla immutable’dır.
- Train-label ve test-feature aralıkları otomatik sıralanmaz; input listeleri zaman sırasını korumalıdır.
- Duplicate interval identity, geriye giden interval listesi, geçersiz/boş aralık ve yanlış tip fail-closed reddedilir.
- Overlap kimlikleri deterministic sıralı tuple olarak raporlanır.
- `PURGE_REQUIRED` yalnız bir karar/gate durumudur; kaç bar veya kaç mikro saniye purge/embargo uygulanacağını hesaplamaz.

## Bilinçli kapsam dışı

Local feature lookback, label future horizon, event settlement horizon, exact purge/embargo duration, expanding/rolling orchestration, dataset binding, OOS/trial/stress lineage, persistence, API/UI ve ekonomik sonuç bu mikro-fazda açılmadı. Exact numeric horizon local veri üretim sözleşmesi görülmeden seçilmeyecek.

## Kontroller

- Önce test RED: yeni `horizon_overlap` modülü eksik olduğu için `308` testte beklenen import error verdi.
- İlk GREEN denemesinde pozitif çoklu-overlap fixture’ının input sırası sözleşmeye aykırı olduğu görüldü; fixture düzeltildi, otomatik sıralama eklenmedi.
- Düzeltme sonrası `uv run --frozen python tools/run_checks.py`: `311/311 PASS`.
- Bağımsız horizon oracle: adjacent sınır, gerçek overlap ve deterministic ID listesi: `INDEPENDENT_HORIZON_ORACLE_PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `132` aktif Python dosyası.
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` purge/embargo gereğinin feature/label yapısına bağlı olduğunu ve sabit horizon uydurulmaması gerektiğini belirtir. Bu teslim yalnız overlap’i görünür kılan generic kontrolü kapatır; purge/embargo uygulamasının tamamlandığını iddia etmez.
