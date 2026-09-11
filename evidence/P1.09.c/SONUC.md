# P1.09.c — Profile-bound instrument filter sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Araştırmadaki quantity-step, price-tick, minimum quantity ve minimum notional iddiaları, venue adına veya canlı emir yetkisine bağlanmadan explicit instrument profile contract’ı olarak uygulandı.

## Uygulanan davranış

`InstrumentFilterProfile` şu metadata’yı aynı profile bağlar:

- `profile_id`;
- quantity step;
- price tick;
- minimum quantity;
- minimum notional.

`validate_order_candidate`:

- quantity ve price’ı exact positive decimal string olarak parse eder;
- quantity’nin profile quantity-step grid’inde olduğunu doğrular;
- price’ın profile price-tick grid’inde olduğunu doğrular;
- minimum quantity ve minimum notional sınırlarını kontrol eder;
- geçen adayı exact quantity/price/notional stringleriyle döndürür.

Off-grid, invalid, minimum altı veya temsil edilemeyen adaylar fail-closed reddedilir. Rounding yönü ve otomatik quantization bu fazda seçilmedi; çünkü kaynaklar metadata sahibi olsa da genel bir rounding yönü sözleşmesi vermiyor.

## Kanıt zinciri

### RED

Yeni `tests/test_instrument_filters.py`, henüz mevcut olmayan `dcabot.application.instrument_filters` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/instrument_filters.py` eklendikten sonra proje kontrolü:

```text
Ran 182 tests ... OK
```

Odak testleri geçerli grid/minimum adayı, quantity off-grid, notional minimumu, invalid profile metadata’sını ve invalid price’ı doğrular.

### Farklı kontrol

Instrument filter suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Bu yalnız profile-bound validation’dır; otomatik rounding/quantization yapmaz.
- Profile’ın venue/version/source kimliği uygulama dışından sağlanır; canlı borsa metadata fetch’i yoktur.
- Balance-percent, eligible balance, risk/exposure, reserve, ladder integration, API/UI, persistence ve economic posting yoktur.
- P1.09.d’de eligible balance kaynağı ve budget contract’ı kapanmadan balance-percent numeric hesaplanmayacaktır.
