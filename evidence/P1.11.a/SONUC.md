# P1.11.a — Ortak sanal hesap ownership/isolation karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; production readiness `NO`.

## Araştırma ve yerel bulgu

- `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md` account scope’u koşullu kabul ediyor; concurrent reservation ve replay’i `LOCAL_CODE_REQUIRED` olarak işaretliyor ve faz kararını `DEFER` veriyor.
- Yerel kodda deal lifecycle kimliği ve config-revision scope’u bulunuyor; bu, deal izolasyonunun bir parçasıdır.
- Yerel `EngineState`/`Store` shared account balance, account-level reservation ledger, pair/deal position owner veya account version conflict boundary taşımıyor.
- Mevcut writer/reserve testleri tek mevcut ekonomik store akışının sınırlarını kanıtlar; iki farklı bot/deal’in ortak sanal account kapasitesini tüketmediğini kanıtlamaz.
- F20 `available_capacity = account_capacity - Σactive_reservations` için asset/unit, rounding, reservation owner, atomic transaction ve replay identity local sözleşmede dondurulmamış.

## Karar

Yeni multi-bot/pair, account balance, reservation, ownership veya concurrency kodu yazılmadı. Account-level ekonomik mutation eklemek, mevcut tek-deal modelinin dışına çıkacağı için önce transaction/locking ve ownership sözleşmesi gerektirir.

Gerekli önkoşullar:

1. Account, deal, product/pair ve position owner kimlikleri.
2. Aynı asset/unit için reservation acquisition, reduction, release ve duplicate/replay identity.
3. Account version/serialization boundary; conflict durumunda retry veya fail-closed kararı.
4. Fill’in commitment’tan position’a tek geçişi ve UI toplamlarında double-counting yasağı.
5. Restart/reopen sonrası field-level ledger replay ve bağımsız exact oracle.

## Kontroller

- Mevcut lifecycle, engine/store, duplicate/conflict, partial/cancel, late-fill ve pending-order kontrolleri güncel suite içinde korunuyor.
- Tam regresyon: `228/228 PASS`.
- Workspace/compile: `PASS`; 96 aktif Python dosyası.

Bu kontroller mevcut tek-deal güvenlik sınırını gösterir; shared-account concurrency/ownership uygulamasının hazır olduğunu göstermez. Kod değişikliği yoktur; RED/GREEN implementasyon döngüsü çalıştırılmadı.

## Kapsam dışı

Shared account schema, account reservation ledger, multi-bot runner, pair ownership, cross-deal position allocation, concurrency retry, API/UI, persistence migration, futures/cross/hedge ve live/testnet bu mikro faza alınmadı.

## Sonraki tek iş

`P1.11.b` — shared-account immutable identity ve account/deal/position ownership contract karar kapısı.
