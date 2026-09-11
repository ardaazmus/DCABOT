# P1.07.d.3.c — BASE-only `reserve_model=NONE` kabul testleri

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`.

Bu mikro faz, P1.07.d.3.b araştırmasının `SIMPLIFY` kararını test etti. Sayısal reserve, public API, persistence, UI, SAFETY/EXIT binding veya reducer replay-idempotency değişikliği yapılmadı.

## Uygulanan en küçük değişiklik

- Internal BASE binding sonucu artık `reserve_model=NONE` ile birlikte `reserve_amount=NOT_MODELED` ve `reserve_asset=NOT_APPLICABLE` taşır.
- Bu değerler numeric `0` değildir; reserve ledger veya monetary hesap üretmez.
- BASE-only acceptance testlerine pending BASE → SAFETY blokajı ve full quantity FILL’in final coverage olmadan anchor üretmemesi eklendi.

## RED → GREEN

1. Yeni not-modeled testinin ilk RED kontrolü beklenen `AttributeError` verdi; alanlar mevcut değildi.
2. Minimal metadata değişikliği sonrası reserve testleri GREEN oldu.
3. Pending SAFETY ve full-fill/final-coverage kabul testleri eklendi ve odak suite ile doğrulandı.

## Kanıtlanan davranışlar

- `NONE` reserve modeli numeric sıfır olarak sunulmuyor.
- Pending BASE order varken yeni SAFETY intent’i reddediliyor.
- Full quantity FILL, `ORDER_FINAL` coverage olmadan order’ı settled veya anchor-ready yapmıyor.
- Önceki d.3.a kanıtlarıyla birlikte equality/placement/ambiguity/EOF, exact leaves, BASE anchor ve pending BASE davranışları korunuyor.
- Legacy yolların davranışı tam regresyonda değişmedi.

## Doğrulama

- d.3.c / BASE binding odak suite: `9/9 PASS`
- Tam `tools/run_checks.py`: `140/140 PASS`
- `compileall src tests`: `PASS`
- `tools/check_workspace.py`: `PASS`

## Sınır

Bu testler `reserve_model=NONE` sınırının dürüst ve fail-closed olduğunu gösterir; explicit reserve ledger’ın doğru olduğunu göstermez. Saf core reducer seviyesinde `execution_id` idempotency’si ayrıca modellenmiş değildir; persistence store dedupe ve late-fill blocker testleri ayrı katmandadır. Internal probe `production_ready=false` olarak kalır.

## Sonraki tek iş

`P1.07.d.2.b — BASE-bound public limit contract readiness`: mevcut internal BASE binding’i public/API katmanına açmadan önce response authority, lifecycle status, `NONE` reserve serialization ve legacy isolation için ayrı contract gate. Explicit reserve ledger, SAFETY/EXIT, UI ve persistence bu işin kapsamı değildir.
