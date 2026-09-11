# P1.10.h — Percentage trailing ratchet

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/trailing_ratchet.py` içine long ve short için exact percentage trigger projection eklendi:

- Long: `stop_price = high_water × (1 - rate)`.
- Short: `stop_price = low_water × (1 + rate)`.
- `0 < rate < 1` zorunludur; oran ve fiyatlar strict decimal boundary’den exact `Fraction` olarak işlenir.
- Long favorable yüksek yeni high-water ile, short favorable düşük yeni low-water ile ratchet eder.
- Ters yönlü geri çekilme stop’u long’da düşürmez, short’ta yükseltmez.
- Aktivasyon öncesi gözlem tetik üretmez; stop sınırında `TRIGGERED` döner.
- Trigger state execution, accepted fill, order, position veya PnL mutasyonu yapmaz.

## Test-first ve bağımsız kanıt

1. RED: Percentage state/API mevcut olmadığı için test import aşamasında kontrollü başarısız oldu.
2. GREEN: `tests.test_trailing_ratchet` long + short fixed-distance + percentage suite `15/15 PASS`.
3. Farklı kontrol: bağımsız Python 3.13 `Decimal` oracle long/short percentage formülleri, ratchet monotonicity ve trigger sınırını doğruladı (`PASS`).
4. Tam regresyon: `226/226 PASS`.
5. Workspace/compile: `PASS`; 96 aktif Python dosyası; backup layout test discovery dışında.

## Serialization düzeltme notu

İlk GREEN denemesinde `0.1` oranının proje `exact_text` kanonunda `0.1` olarak tutulduğu doğrulandı; testteki `1/10` beklentisi davranış değiştirilmeden kanonik sözleşmeye uyarlandı.

## Kapsam dışı

Stop-market/stop-limit execution, gap/slippage, OCO/cancel-replace, late fill, reserve, economic posting, API/UI, persistence, futures/cross/hedge ve breakeven bu mikro faza alınmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` içindeki F17/F18 formülleri ve trigger/execution ayrımı kullanıldı. Bu genel trigger contract kanıtıdır; venue-specific execution davranışı iddia edilmez.

## Sonraki tek iş

`P1.10.i` — trailing trigger’ın stop/exit execution boundary’sine bağlanması için karar kapısı.
