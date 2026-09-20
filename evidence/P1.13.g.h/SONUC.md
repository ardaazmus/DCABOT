# P1.13.g.h — Futures Grid offline lifecycle bağımsız oracle ve regresyon kapısı

## Sonuç

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Local event oracle: `ORACLE_PASS`
- Vendor-eşdeğer ileri lifecycle implementation: `DEFERRED / NO-GO`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Test: `tests/test_futures_grid_local_lifecycle_oracle.py` — `4/4 PASS`
- g.a–g.c, g.f–g.h ilgili güvenlik/test kümesi: `21/21 PASS`
- Production readiness: `NO`
- Bağımsız review: `NOT_RUN`

## Oracle sonucu

İnvariantlar implementasyondan ayrı literal beklenen sonuçlarla doğrulandı:

- OPEN → CANCEL_PENDING ve CANCEL_PENDING → CANCELED sıraları kabul edilir;
- CANCELED → FILL kabul edilir ve fill sonucu `FILLED` olur;
- CANCELED → REPLACEMENT_READY kabul edilir;
- OPEN → REPLACEMENT_REQUESTED quarantine edilir;
- aynı event kimliğinin farklı içeriği quarantine edilir ve geçmişe eklenmez;
- yanlış ilk sequence transition’dan önce reddedilir;
- replay sonucu status, event tuple’ı, fill kimlikleri ve outcome tuple’ı sabit
  kalır.

Bu kapı yalnız g.g’deki local in-memory reducer’ı denetler. Herhangi bir order,
replacement, reserve, economic posting, persistence veya venue authority
üretilmez. Testlerdeki `FILL_ACCEPTED` yalnız yerel gözlemdir; gerçek borsa
fill’i değildir.

## Bilinçli kapsam dışı

Bu oracle 3Commas, Pionex veya Binance’in vendor lifecycle davranışını
kanıtlamaz. Exact range revision, gerçek cancel/replacement, late-fill
ekonomik yetkisi, reserve mutation, restart persistence, signed request,
Testnet/live order ve mainnet açılmadı. P1.13.h Reverse/Infinity varyantları
ayrı karar ve kaynak kapısı olarak kalır.

## Kontroller

- Literal oracle/regresyon: `4/4 PASS`.
- İlgili g.a–g.c, g.f–g.h test kümesi: `21/21 PASS`.
- `python -m compileall -q src`: `PASS`.
- `git diff --check`: `PASS`.
- Tam canonical suite yeniden çalıştırılmadı; önceki canonical baseline
  `749` testte `747 PASS` ve 2 Windows Credential Manager `1312` environment
  error olarak korunmuştur.
- Gerçek API key/secret, signed request, order mutation, mainnet ve
  persistence eklenmedi.
