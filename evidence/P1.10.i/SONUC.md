# P1.10.i — Trailing trigger–exit boundary

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`bind_trailing_exit_candidate` adapter’ı long/short fixed-distance ve long/short percentage olmak üzere dört trailing state türünü kabul edecek şekilde genişletildi.

- Yalnız `TRIGGERED` ve geçerli `stop_price` ile exit adayı üretilebilir.
- Aday, `validate_exit_capacity` üzerinden accepted fill + mevcut commitment + yeni miktar sınırına bağlanır.
- Adayın `trigger_price`, requested quantity ve remaining capacity alanları exact sözleşmede döner.
- `order_authority="NONE"` korunur.
- Adapter accepted economic fill, `ORDER_FINAL`, reserve, position veya PnL mutasyonu yapmaz.
- Untriggered state `TRAILING_EXIT_NOT_TRIGGERED`, bilinmeyen state `TRAILING_EXIT_STATE_INVALID`, kapasite aşımı ise `EXIT_CAPACITY_EXCEEDED` olarak fail-closed davranır.

## Test-first ve bağımsız kanıt

1. RED: Mevcut adapter yalnız `TrailingLongState` kabul ettiği için short/percentage varyantları kontrollü olarak başarısız oldu.
2. GREEN: `tests.test_trailing_exit_binding` `5/5 PASS`.
3. Farklı kontrol: dört triggered variant bağımsız çağrıyla aynı kapasite sonucunu verdi; state snapshot’ları binding öncesi/sonrası değişmedi (`PASS`).
4. Tam regresyon: `228/228 PASS`.
5. Workspace/compile: `PASS`; 96 aktif Python dosyası; backup layout test discovery dışında.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` içindeki `Trigger != execution`, `ExecutionCandidate -> Accepted Exit FILL` ve quantity conservation sınırları uygulandı. Bu adapter yerel candidate sınırıdır; venue-specific order acknowledgement, cancel-replace, late fill ve gerçek execution kanıtı değildir.

## Kapsam dışı

Stop-market/stop-limit execution, gap/slippage, OCO/cancel-replace, late fill, reserve lifecycle, economic posting, API/UI, persistence, futures/cross/hedge ve breakeven bu mikro faza alınmadı.

## Sonraki tek iş

`P1.10.j` — OCO/cancel-replace ve late-fill kapasite karar kapısı.
