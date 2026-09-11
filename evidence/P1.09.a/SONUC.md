# P1.09.a — Exact BASE/QUOTE sizing candidate sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09 araştırmasındaki exact sizing claim’i, mevcut domain’in string → exact `Fraction` sınırıyla uyumlu en küçük application contract olarak uygulandı. `BASE_QTY` ve `QUOTE_NOTIONAL` aynı scalar alanmış gibi ele alınmadı.

## Uygulanan davranış

`build_sizing_candidate`:

- yalnız explicit `BASE_QTY` veya `QUOTE_NOTIONAL` kabul eder;
- amount ve reference price’ı plain positive decimal string olarak parse eder;
- BASE girdisinde amount’ı aday BASE quantity kabul eder;
- QUOTE girdisinde `candidate_quantity = quote_notional / reference_price` hesaplar;
- `candidate_notional = candidate_quantity * reference_price` değerini exact üretir;
- sonuçları frontend/display hesabı olmadan exact decimal string olarak döndürür;
- quantity/tick rounding, instrument filter, balance lookup, risk acceptance veya economic posting yapmaz.

`BALANCE_PERCENT`, `BASE`/`QUOTE` belirsiz modları ve malformed/zero girdiler fail-closed reddedilir. Exact decimal dışına taşan aday da kabul edilmez.

## Kanıt zinciri

### RED

Yeni `tests/test_sizing_units.py`, henüz mevcut olmayan `dcabot.application.sizing_units` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/sizing_units.py` eklendikten sonra proje kontrolü:

```text
Ran 176 tests ... OK
```

Odak testleri BASE ve QUOTE eşdeğerliğini, mixed-unit/unsupported mode reddini ve invalid amount/price reddini doğrular.

### Farklı kontrol

Sizing suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Bu yalnız pre-quantization candidate contract’ıdır; accepted order intent değildir.
- Venue quantity-step/tick/min-notional metadata owner’ı ve rounding mode henüz profile-bound değildir.
- Balance-percent, custom ladder toplamı, exposure/risk kapısı, reinvestment, API/UI, persistence ve live/testnet venue yoktur.
- P1.09.b exact ladder allocation/conservation contract’ı tamamlanmadan bu candidate public run yoluna bağlanmayacaktır.
