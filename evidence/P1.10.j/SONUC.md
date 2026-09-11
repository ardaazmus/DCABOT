# P1.10.j — OCO/cancel-replace ve late-fill kapasite karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; production readiness `NO`.

## Yerel kontrolde doğrulananlar

- Mevcut core reducer, final sonrasında gelen geçerli fill’i ekonomik olarak işlerken order coverage’ını `UNKNOWN` durumuna ve `LATE_FILL_AFTER_FINAL` blocker’ına taşıyor.
- Partial fill, explicit cancellation, duplicate/conflict ve pending-order risk blokajı için mevcut test kanıtı var.
- PAUSED altındaki `CANCEL_REQUESTED` yalnız cancellation request state’idir; cancellation confirmation, reserve release veya late-fill çözümü iddia etmiyor.
- Trailing exit adapter’ı yalnız aday ve kapasite projeksiyonu yapıyor; OCO üyeliği, cancel acknowledgement ve replacement order kimliği taşımıyor.

## Eksik olduğu doğrulanan sözleşme

OCO/cancel-replace için şu sahiplikler ve geçişler aynı local contract’ta yok:

1. Eski exit commitment’ının `REQUESTED → ACKNOWLEDGED/REJECTED` cancellation yaşam döngüsü.
2. Cancellation kesinleşmeden yeni exit’in eski kapasiteyi kullanmasını engelleyen invariant.
3. OCO bacakları, replacement order identity ve duplicate/conflicting callback ayrımı.
4. Late fill geldiğinde hangi order’ın ekonomik fill authority’si olduğu ve remaining capacity’nin nasıl yeniden hesaplandığı.
5. Reserve/commitment acquisition, partial reduction, release ve atomic persistence owner’ı.

Bu bilgiler olmadan yeni adapter veya numeric reserve kuralı yazmak, mevcut `UNKNOWN` fail-closed davranışını gevşetir ve plan dışı ekonomik varsayım üretir.

## Kontroller

- Late-fill, duplicate/conflict, partial/cancel ve pending-order odak suite: `27/27 PASS`.
- Tam regresyon: `228/228 PASS`.
- Workspace/compile: `PASS`; 96 aktif Python dosyası.

Kontroller mevcut güvenlik sınırının çalıştığını kanıtlar; OCO/cancel-replace’in uygulandığını kanıtlamaz. Bu nedenle RED/GREEN implementasyon döngüsü çalıştırılmadı; uygulanacak yeterli sözleşme yoktur.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` ve `docs/External_Claim_Verification/01_rapor/Ayrintili_Arastirma_Raporu.md`, cancellation confirmation olmadan capacity’nin serbest bırakılmaması ve late fill’in coverage’ı belirsizleştirmesi gerektiğini destekliyor. Dış venue örnekleri local reducer/reserve owner kanıtı sayılmadı.

## Kapsam dışı

Gerçek OCO, cancel/replace execution, order acknowledgement, venue callback, reserve ledger, API/UI, persistence migration, futures/cross/hedge ve live/testnet bağlantısı bu mikro faza alınmadı.

## Sonraki tek iş

`P1.10.k` — trailing public/API/UI readiness karar kapısı; görsel karar veya yeni UI araştırması gerektirirse otomatik olarak `DEFERRED/NO-GO` kalacak.
