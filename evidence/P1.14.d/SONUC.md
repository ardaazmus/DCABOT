# P1.14.d — Rebalancing threshold/time trigger projection

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/rebalance_triggers.py`
- Test: `tests/test_rebalance_triggers.py`
- Bağımsız review: `PASS` (Mendel salt-okunur Codex incelemesi)
- Production readiness: `NO`
- Sonraki tek iş: `P1.14.e` template integrity ve non-authority karar kapısı

Bu mikro-fazda rebalancing için iki ayrı salt-okunur tetik projection’ı eklendi. Threshold ve time-interval politikaları birbirine karıştırılmadı; sonuçlar ekonomik emir veya fill değildir.

## Uygulanan sözleşme

- Threshold: `abs(current_weight - target_weight) >= threshold`; sınır eşitliği `TRIGGERED` kabul edilir.
- Time interval: `observation_time_us - last_rebalance_time_us >= interval_us`; sınır eşitliği `TRIGGERED` kabul edilir.
- Weight ve threshold exact plain decimal string olarak, 0–1 aralığında doğrulanır.
- Zamanlar non-negative integer microseconds olmalıdır; geriye giden observation zamanı reddedilir.
- Sonuçlarda deviation veya elapsed süre açıkça taşınır; gizli wall-clock/processing-time kullanılmaz.

## Bilinçli kapsam dışı

Target allocation projection ile trigger’ın birleştirilmesi, asset price conversion, fee/rounding, available balance, instrument filters, order sizing, order/reserve/fill, persistence/replay, signal binding, template, API ve UI eklenmedi. `TRIGGERED` yalnızca aday üretimine izin veren bir gözlem kapısıdır.

## Kontroller

- Önce test RED: yeni test dosyası eksik `rebalance_triggers` modülü nedeniyle import error verdi.
- Güncel odak `python -m unittest tests.test_rebalance_triggers`: `8/8 PASS`.
- İlgili projection kümesi `python -m unittest tests.test_rebalance_triggers tests.test_rebalance_projection`: `14/14 PASS`.
- Bağımsız Decimal/time oracle: threshold deviation, inclusive boundary, threshold zero/signed zero,
  elapsed interval, same timestamp, malformed numeric values ve bool zaman girdileri `PASS`.
- Mendel salt-okunur Codex review: `PASS`; threshold/time formülleri, input sınırları,
  immutable kararlar ve order/candidate/fill authority yokluğu uygun bulundu.
- `python -m compileall -q src`: `PASS`; `git diff --check`: `PASS`.
- `tools/run_checks.py` güncel tam-suite için `FAIL`: proje `Python 3.13` isterken
  kullanılabilir bundled runtime `3.12.14`; bu nedenle güncel tam-suite sonucu iddia edilmiyor.
- Önceki tarihsel tam-suite sonucu (`281/281`) bu oturumun doğrulaması olarak kullanılmadı.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` threshold ve time trigger ailelerini davranış/model kanıtı olarak destekliyor; yerel implementation’ın geçtiğini iddia etmiyor. Bu teslim yalnız trigger projection kabulüdür; rebalancing işleminin gerçekleştiği iddia edilmez.
