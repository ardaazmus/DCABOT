# P1.08.i — Pause altında order policy sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Bu mikro dilim yalnız PAUSED lifecycle altında pending order ve yeni intent için ekonomik olmayan policy kararını tanımlar. Dış araştırmadaki üç aday policy açık isimlerle tutuldu:

- `KEEP_OPEN`: mevcut pending order’a cancellation request uygulanmaz;
- `CANCEL_REQUESTED`: yalnız cancellation request’in gönderilmek istendiğini bildirir;
- `BLOCKED`: pending order tarafında otomatik işlem yapılmaz.

Her üç policy’de de yeni economic intent `BLOCKED` durumundadır. Böylece PAUSED sırf sinyal geldi diye yeni order üretmez.

## Uygulanan sınır

`evaluate_paused_orders` saf bir karar üretir; order state’i, reserve’i, position’ı, ledger’ı veya persistence’ı mutasyona uğratmaz. `CANCEL_REQUESTED` sonucu `REQUESTED_NOT_CONFIRMED` olarak ayrıştırılır; bu sonuç cancellation’ın gerçekleştiğini, fill geldiğini veya reserve’in serbest kaldığını iddia etmez. Gerçek cancellation/late-fill reconciliation gelecekte ayrı order adapter ve execution identity kapısında ele alınacaktır.

Bilinmeyen policy `PAUSE_ORDER_POLICY_INVALID` ile fail-closed reddedilir. API/UI ve mevcut core ekonomik reducer bu mikro faza bağlanmadı.

## Kanıt zinciri

### RED

Yeni `tests/test_pause_order_policy.py`, henüz mevcut olmayan `dcabot.application.pause_order_policy` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/pause_order_policy.py` eklendikten sonra proje kontrolü:

```text
Ran 173 tests ... OK
```

Testler üç explicit policy’nin tam karar nesnesini, tüm policy’lerde yeni intent blokajını, cancellation request’in gerçekleşmiş cancellation/fill olarak yorumlanmamasını ve bilinmeyen policy reddini doğrular.

### Farklı kontrol

Odak policy suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak ayrıca geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- `KEEP_OPEN`, `CANCEL_REQUESTED` veya `BLOCKED` henüz runtime order state’e uygulanmıyor.
- Pause event’ine policy alanı eklenmedi; persistent lifecycle schema/API değişmedi.
- Cancellation confirmation, late fill, reserve release, partial fill ve venue state machine kapsam dışıdır.
- Shared account/isolation ve toplu bot işlemleri sonraki P1 kapsamındadır.
