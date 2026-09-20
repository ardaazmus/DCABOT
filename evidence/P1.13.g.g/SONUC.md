# P1.13.g.g — Futures Grid offline lifecycle transition simülasyonu

## Sonuç

- Alt faz durumu: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Yerel offline simulation: `CONTRACT_READY`
- Vendor-eşdeğer ileri lifecycle implementation: `DEFERRED / NO-GO`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_local_lifecycle.py`
- Odak test: `tests/test_futures_grid_local_lifecycle.py` — `5/5 PASS`
- Önceki g.a–g.c gate kümesi: `10/10 PASS`; g.f politika: `2/2 PASS`
- Production readiness: `NO`
- Bağımsız review: `NOT_RUN`

## Açılan güvenli sınır

P1.13.g.f’de ilan edilen DCABOT yerel politikası, yalnız immutable in-memory
bir transition simülasyonunda uygulandı:

- cancel request → cancel pending → cancel confirmation sırası zorunludur;
- cancel sonrası kabul edilmiş fill, yerel simülasyonda `FILLED` olarak
  cancel’e üstün gelir;
- cancel confirmation olmadan replacement isteği `QUARANTINED` olur;
- aynı fill kimliği tekrarlandığında state değişmeden `DUPLICATE` döner;
- bilinmeyen/çelişkili gözlem `QUARANTINED` olur ve sonraki gözlemler bloke
  edilir;
- aynı immutable event tuple’ı iki kez replay edildiğinde aynı state ve
  outcome tuple’ı üretilir.

Bu kod gerçek exchange event’i, order/replacement ID’si, miktar, reserve,
economic posting, persistence veya venue authority üretmez. `FILL_ACCEPTED`
yalnız local observation adıdır; kabul edilmiş gerçek borsa fill’i veya
ekonomik kayıt değildir. Herhangi bir authority alanı yoktur ve kapsam
`DCABOT_OFFLINE_SIMULATION_ONLY` olarak g.f politika kontratına bağlıdır.

## Bilinçli kapsam dışı

Exact vendor lifecycle oracle’ı bulunmadığı için bu simülasyon 3Commas,
Pionex veya Binance davranışının doğrulaması değildir. Dynamic range,
gerçek cancel/replacement request, late-fill ekonomik posting, reserve
mutation, restart persistence, signed request, Testnet/live order ve mainnet
açılmadı. Sonraki güvenli iş local event matrix için bağımsız oracle ve
conflict/replay regresyon kapısıdır.

## Kontroller

- TDD RED: yeni test, modül henüz yokken beklenen import hatası verdi.
- TDD GREEN: `5/5 PASS`.
- İlgili güvenlik kontrolleri: g.a–g.c `10/10 PASS`, g.f `2/2 PASS`.
- `python -m compileall -q src`: `PASS`.
- `git diff --check`: `PASS`.
- `tools/check_workspace.py`: bundled Python `3.12` ile çalıştırıldı; checker
  Python `3.13` istediği için `FAIL` (ortam önkoşulu, kaynak hatası değil).
- Tam `unittest discover`: bundled Python `3.12` ortamında proje bağımlılıkları
  ve `tools` yolu eksik olduğu için `664` keşfedilen testte `19` import/runtime
  environment error verdi; bu faz için geçerli tam regresyon oracle’ı değildir.
  Önceki canonical checkout baseline’ı `749` testte `747 PASS` ve 2 adet
  Windows Credential Manager `1312` environment error olarak korunmuştur.
- Gerçek API key/secret, signed request, order mutation, mainnet ve
  persistence eklenmedi.
