# P1.09.e — Exact ladder generation binding sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Mevcut domain `build_plan` üretimi, P1.09.a sizing candidate ve P1.09.b allocation conservation contract’larına bağlandı. Bu bir order acceptance veya public run implementation’ı değildir.

## Uygulanan davranış

`build_ladder_binding`:

- explicit positive decimal string ladder parametrelerini parse eder;
- mevcut domain `build_plan` ile exact price/quantity seviyelerini üretir;
- `BASE_QTY` seçilirse allocation’ı level quantity olarak alır;
- `QUOTE_NOTIONAL` seçilirse allocation’ı `level quantity * level price` olarak exact hesaplar;
- level’ları canonical decimal string olarak döndürür;
- allocation tuple’ını conservation contract’ına verir;
- budget aşımını veya geçersiz/collapsed ladder üretimini fail-closed reddeder.

## Kanıt zinciri

### RED

Yeni `tests/test_ladder_binding.py`, henüz mevcut olmayan `dcabot.application.ladder_binding` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/ladder_binding.py` eklendikten sonra proje kontrolü:

```text
Ran 188 tests ... OK
```

Odak testleri exact BASE allocation, exact QUOTE level notional, budget overrun ve invalid/collapsed generation sınırlarını doğrular.

### Farklı kontrol

Ladder binding suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Ladder binding pre-quantization seviyedir; venue rounding/filter bu akışa bağlanmadı.
- Balance-percent projection henüz ladder’a bağlanmadı; gerçek eligible balance authority’si yoktur.
- Risk/exposure, reserve, economic intent/fill, API/UI, persistence, live/testnet venue yoktur.
- P1.09.f realized-profit eligible pool ve reinvestment contract’ı tamamlanmadan yeniden yatırım yapılmayacaktır.
