# P1.10.k — Trailing public/API/UI readiness karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; production readiness `NO`.

## Yerel durum

- Mevcut public historical response’ları action authority, marker authority, bar/time identity ve ekonomik özet sınırlarıyla çalışıyor.
- Public response’ta trailing state, activation/rate/distance, trigger-to-candidate identity veya trailing execution lifecycle alanı yok.
- Mevcut frontend chart/marker yüzeyi yalnız mevcut historical chart/action contract’ını gösteriyor; trailing için yeni görünüm, etkileşim veya marker semantics tanımlı değil.
- `AGENTS.md` finansal UI’da yeniden hesaplamayı ve grafik koordinatlarını karar verisi olarak kullanmayı yasaklıyor.

## Karar

Trailing’i public API/UI’a açacak yeni alanlar veya UI davranışı eklenmedi. Bunun için önce şu sözleşmelerin tekil ve test edilebilir olması gerekir:

1. Trigger, execution candidate ve accepted fill authority alanlarının public isimleri ve yaşam döngüsü.
2. Long/short fixed-distance/percentage state serialization ve precision/rounding owner.
3. `INDETERMINATE`/committed-prefix durumunda trailing state ve marker görünürlüğü.
4. OCO/cancel-replace/late-fill/reserve ekseninin çözülmesi.
5. UI’da görsel/etkileşim kararları için kullanıcı onaylı dış araştırma ve 320px taşma/erişilebilirlik kabulü.

Bu önkoşullar yokken API alanı veya UI göstergesi eklemek, trigger’ı gerçekleşmiş emir gibi sunabilir. Bu nedenle karar `DEFERRED/NO-GO` olarak tutuldu.

## Kontroller

- Mevcut historical API/chart/action odak testleri ve authority sınırları korunuyor.
- Güncel tam regresyon: `228/228 PASS`.
- Workspace/compile: `PASS`; 96 aktif Python dosyası.

Bu kontroller mevcut public sözleşmenin bozulmadığını gösterir; trailing public/UI entegrasyonunun hazır olduğunu göstermez. Kod değişikliği yoktur; RED/GREEN döngüsü çalıştırılmadı.

## Kapsam dışı

Trailing API DTO’su, yeni endpoint, frontend state, görsel araştırma, tooltip/interaction, yeni marker türü, execution, OCO/cancel-replace, late fill, reserve, persistence, futures/cross/hedge ve live/testnet bu mikro faza alınmadı.

## Sonraki tek iş

`P1.11.a` — ortak sanal hesap için account/position ownership ve isolation karar kapısı.
