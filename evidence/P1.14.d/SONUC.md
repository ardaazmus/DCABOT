# P1.14.d — Rebalancing threshold/time trigger projection

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/rebalance_triggers.py`
- Test: `tests/test_rebalance_triggers.py`
- Bağımsız review: `NOT_RUN`
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
- En küçük uygulama sonrası kanonik `uv run --frozen python tools/run_checks.py`: `281/281 PASS`.
- Bağımsız Decimal/time oracle: threshold deviation ve elapsed interval hesapları `PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `118` aktif Python dosyası; backup discovery kapsam dışı.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` threshold ve time trigger ailelerini davranış/model kanıtı olarak destekliyor; yerel implementation’ın geçtiğini iddia etmiyor. Bu teslim yalnız trigger projection kabulüdür; rebalancing işleminin gerçekleştiği iddia edilmez.
