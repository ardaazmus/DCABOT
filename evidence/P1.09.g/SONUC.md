# P1.09.g — Sizing pre-acceptance gate sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09.a–f’deki saf sözleşmeler tek bir ekonomik olmayan pre-acceptance gate’te birleştirildi. Gate’in geçmesi order kabulü veya reserve oluşturma yetkisi vermez.

## Uygulanan sınır

`evaluate_sizing_pre_acceptance` şu koşulları birlikte doğrular:

- sizing candidate ve ladder aynı `QUOTE_NOTIONAL` birimindedir;
- eligible balance budget asset’i explicit `quote_asset` ile aynıdır;
- candidate quantity/price/notional kendi içinde exact tutarlıdır ve instrument profile filters’tan geçer;
- ladder seviyelerinin allocation toplamı conservation kaydıyla aynıdır;
- candidate notional + ladder notional toplamı eligible budget’ı aşmaz.

BASE candidate veya farklı asset/unit bağlamı sessiz conversion yapılmadan fail-closed reddedilir. Geçen sonuçta `order_authority=NONE` korunur.

## Kanıt zinciri

### RED

Yeni `tests/test_sizing_pre_acceptance.py`, henüz mevcut olmayan `dcabot.application.sizing_pre_acceptance` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/sizing_pre_acceptance.py` eklendikten sonra proje kontrolü:

```text
Ran 194 tests ... OK
```

Odak testleri quote candidate + ladder + profile + eligible budget birleşimini, toplam commitment budget aşımını ve cross-unit/cross-asset reddini doğrular.

### Farklı kontrol

Pre-acceptance suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Gate yalnız ortak quote unit’i destekler; BASE↔QUOTE conversion ve multi-asset budget yoktur.
- Passing sonuç order authority, risk acceptance, reserve veya economic posting değildir.
- Metamorphic/property oracle, API/UI, persistence, multi-deal ledger, venue/live/testnet ve indikatör koşulları yoktur.
- P1.09.h bağımsız exact/metamorphic oracle kontrolleri tamamlanmadan public sizing akışı açılmayacaktır.
