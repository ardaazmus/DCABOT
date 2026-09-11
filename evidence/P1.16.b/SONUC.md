# P1.16.b — OOS freeze ve evaluation lineage sınırı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/oos_lineage.py`
- Test: `tests/test_oos_lineage.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.c` feature/label horizon ve purge/embargo karar kapısı

P1.16 araştırmasındaki OOS freeze kuralının en küçük saf sınırı uygulandı. Bir evaluation lineage OOS sonucu görülmeden `OOS_UNTOUCHED` kalır; görüldüğünde `OOS_INSPECTED` olur. Bu lineage üzerinde tuning talebi, eski sonucu `TOUCHED` yapar ve `NEW_EXPERIMENT_REQUIRED` döndürür. Yeni deneyin oluşturulması, parametre çalıştırılması veya ekonomik sonuç üretimi bu mikro-fazda yapılmaz.

## Uygulanan sözleşme

- `EvaluationLineage` immutable experiment identity ve explicit OOS status taşır.
- OOS inspection idempotent’tir; `TOUCHED` lineage yeniden untouched/inspected yapılamaz.
- OOS görülmeden tuning `TUNING_ALLOWED` olarak kalır ve lineage’ı değiştirmez.
- OOS görüldükten sonra tuning `TOUCHED` + `NEW_EXPERIMENT_REQUIRED` üretir; eski OOS’un untouched gibi sunulması engellenir.
- Durum geçişi in-memory ve non-economic’tir; UI, optimizer, persistence veya run result authority değildir.

## Bilinçli kapsam dışı

Yeni experiment üretme, dataset/config/model/kernel/seed lineage binding, persisted study/trial registry, failed-run denominator, OOS KPI, expanding/rolling orchestration, purge/embargo horizon, warmup, stress result, API/UI ve ekonomik simülasyon bu mikro-fazda açılmadı. Exact purge/embargo sayısı feature lookback, label future horizon ve event settlement bilgisi görülmeden seçilmeyecek.

## Kontroller

- Önce test RED: yeni `oos_lineage` modülü eksik olduğu için `304` testte beklenen import error verdi.
- Minimal uygulama sonrası `uv run --frozen python tools/run_checks.py`: `307/307 PASS`.
- Bağımsız OOS control: untouched tuning, inspection sonrası touched/new-experiment ve touched lineage geri dönüş reddi: `INDEPENDENT_OOS_FREEZE_CONTROL_PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `130` aktif Python dosyası.
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` OOS görüldükten sonra tuning yapılırsa aynı segmentin untouched final evaluation sayılamayacağını ve yeni untouched holdout/yeni evaluation lineage gerektiğini kabul eder. Bu teslim yalnız eski lineage’ın yeniden untouched gösterilmesini önleyen saf sınırı kapatır; P1.16’nın tamamlandığını iddia etmez.
