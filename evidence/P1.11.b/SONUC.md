# P1.11.b — Shared-account immutable identity contract

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/shared_account_identity.py` içine ekonomik mutation içermeyen frozen/slots identity contract’ı eklendi:

- `account_id`, `product_id`, `position_mode`, `deal_id` zorunlu explicit kimliklerdir.
- `allocation_id` doğrudan deal sahipliğinde `None`, allocation sahipliğinde explicit kimlik olabilir.
- Tüm alanlar scope-significant’tir; başka account/product/mode/deal/allocation farklı identity üretir.
- `position_mode` bu mikro fazda opaque kimliktir; spot/futures/hedge/cross semantiği eklenmedi.
- Geçersiz veya serbest biçimli kimlikler fail-closed reddedilir.
- Dataclass frozen ve hashable’dır; account balance, reservation, position, ownership veya concurrency değişmez.

## Test-first ve bağımsız kanıt

1. RED: `shared_account_identity` modülü olmadığı için test import aşamasında kontrollü başarısız oldu.
2. GREEN: `tests.test_shared_account_identity` `3/3 PASS`.
3. Farklı kontrol: bağımsız Python 3.13 frozen/hash ve mutation reddi kontrolü `PASS`.
4. Tam regresyon: `231/231 PASS`.
5. Workspace/compile: `PASS`; 98 aktif Python dosyası.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md` account/deal/position ownership ayrımını destekliyor; concurrent reservation ve replay’i local-code-required bırakıyor. Bu mikro faz yalnız kimlik sınırını uygular, account economics uygulamaz.

## Kapsam dışı

Shared account schema, reservation ledger, account capacity, balance mutation, position allocation, account version, concurrency retry, atomic persistence, replay, API/UI, futures/cross/hedge ve live/testnet bu mikro faza alınmadı.

## Sonraki tek iş

`P1.11.c` — account reservation ledger ve account-version concurrency karar kapısı.
