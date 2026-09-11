# P1.10.g — Short sabit-mesafeli trailing ratchet

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/trailing_ratchet.py` içine short için trigger-only projection eklendi:

- `INACTIVE → ACTIVE → TRIGGERED`.
- Aktivasyon, gözlenen fiyat `activation_price` değerine eşit veya düşük olduğunda gerçekleşir.
- Exact short stop: `stop_price = low_water + distance`.
- Favorable hareket yalnız düşük yeni `low_water` değeriyle ratchet eder; stop fiyatı yukarı taşınmaz.
- Geri çekilme `observed >= stop_price` olduğunda `TRIGGERED` üretir.
- Trigger state execution, accepted fill, order, position veya PnL mutasyonu yapmaz.
- Geçersiz decimal, geçersiz state, activation’dan büyük/eşit distance ve trigger sonrası yeniden gözlem fail-closed reddedilir.

## Test-first kanıtı

1. RED: Short API/state mevcut olmadığı için yeni test import aşamasında kontrollü olarak başarısız oldu (`TrailingShortState` bulunamadı).
2. GREEN: `tests.test_trailing_ratchet` long + short suite `10/10 PASS`.
3. Farklı kontrol: bağımsız Python 3.13 `Decimal` oracle ile aktivasyon, `low_water + distance`, monoton ratchet ve trigger sınırı `PASS`.
4. Tam regresyon: `221/221 PASS`.

## Kapsam dışı

Percentage trailing, stop-market/stop-limit execution, gap/slippage, OCO/cancel-replace, late fill, reserve, economic posting, API/UI, persistence, futures/cross/hedge ve breakeven bu mikro faza alınmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` içindeki F18 short formülü ve trigger/execution ayrımı kullanıldı. Bu genel short trailing contract kanıtıdır; venue-specific execution davranışı iddia edilmez.

## Sonraki tek iş

`P1.10.h` — yüzde-mesafeli trailing ratchet için karar/uygulama kapısı.
