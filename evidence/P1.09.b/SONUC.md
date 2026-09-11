# P1.09.b — Exact ladder allocation/conservation sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09 araştırmasındaki ladder conservation claim’i, aynı explicit birimdeki allocation’ların exact toplanması ve configured budget’ın aşılmaması şeklinde en küçük saf contract olarak uygulandı.

## Uygulanan davranış

`validate_ladder_allocations`:

- yalnız `BASE_QTY` veya `QUOTE_NOTIONAL` allocation unit kabul eder;
- allocation’ları ve budget’ı plain positive decimal string olarak parse eder;
- allocation toplamını exact `Fraction` ile hesaplar;
- `total_allocated <= budget` invariant’ını uygular;
- exact total, budget ve remaining budget değerlerini decimal string olarak döndürür;
- budget aşımı, bilinmeyen unit ve invalid/zero allocation için fail-closed hata verir.

Bu contract pre-quantization sınırındadır. Quantity-step/tick rounding, min-notional, instrument metadata ve risk owner’ı burada varsayılmadı.

## Kanıt zinciri

### RED

Yeni `tests/test_ladder_conservation.py`, henüz mevcut olmayan `dcabot.application.ladder_conservation` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/ladder_conservation.py` eklendikten sonra proje kontrolü:

```text
Ran 179 tests ... OK
```

Odak testleri exact `.10 + .20 + .30 = .60` toplamını, kalan budget’ı, budget aşımını ve invalid unit/allocation reddini doğrular.

### Farklı kontrol

Ladder suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Bu yalnız allocation toplamı kontrolüdür; fiyat seviyeleri veya order quantity generation yapmaz.
- Venue quantity-step/tick/min-notional ve rounding mode profile-bound değildir.
- Balance-percent, reinvestment, risk/exposure, reserve, API/UI, persistence ve economic posting yoktur.
- P1.09.c profile-specific quantization/filter owner contract’ı tamamlanmadan public order/run yoluna bağlanmayacaktır.
