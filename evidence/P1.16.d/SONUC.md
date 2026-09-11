# P1.16.d — Multiple-testing trial registry sınırı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/trial_registry.py`
- Test: `tests/test_trial_registry.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.e` stress lineage ve ayrı sonuç kimliği karar kapısı

P1.16 araştırmasındaki “yalnız kazananı tutma” riskini azaltan en küçük saf registry uygulandı. Her bounded study explicit parameter-space, objective ve selection-rule kimliği taşır; `SUCCEEDED`, `FAILED` ve `INVALID` denemelerin tamamı aynı `trial_count` içine alınır.

## Uygulanan sözleşme

- `TrialStudy` immutable manifest’tir ve en fazla 1.000 trial kabul eder.
- `TrialRecord` explicit identity ve `SUCCEEDED`/`FAILED`/`INVALID` status taşır.
- Aynı trial ID ve aynı payload duplicate olarak no-op’tur; farklı status conflict olarak fail-closed reddedilir.
- Limit dolduğunda yeni deneme reddedilir; başarısız veya geçersiz deneme sessizce atılmaz.
- Registry winner seçmez, ekonomik sonuç hesaplamaz ve yalnız başarılı koşuyu export etmez.

## Bilinçli kapsam dışı

Parametre değerlerinin canonical snapshot’ı, optimizer çalıştırma, score/KPI, winner selection, persisted study/trial database, dataset/config/model/kernel/seed binding, OOS result, stress lineage, purge/embargo, API/UI ve ekonomik simülasyon bu mikro-fazda açılmadı. Bu registry local in-memory karar sınırıdır; production multiple-testing kanıtı değildir.

## Kontroller

- Önce test RED: yeni `trial_registry` modülü eksik olduğu için `312` testte beklenen import error verdi.
- Minimal uygulama sonrası `uv run --frozen python tools/run_checks.py`: `315/315 PASS`.
- Bağımsız trial control: succeeded/failed/invalid sayımı, duplicate idempotency ve bounded count: `INDEPENDENT_TRIAL_REGISTRY_CONTROL_PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `134` aktif Python dosyası.
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` her optimization study için trial count, search-space, objective, selection rule ve rejected runs görünürlüğünü; yalnız kazanan run’ın tutulmamasını ister. Bu teslim yalnız sayım ve bounded registry sınırını kapatır; optimizer veya istatistiksel performans iddiası içermez.
