# P1.13.e — Grid trailing-up/down ve reverse/infinity karar kapısı

## Sonuç

- Durum: `DEFERRED / NO-GO / LOCAL_PASS`
- Kod değişikliği: yok
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.f` Futures Grid v1 için ayrı profile ve exact projection karar kapısı

Bu mikro-fazda spot-grid trailing-up/down davranışı ile reverse/infinity grid ailelerinin üretim ekonomik davranışı açılmadı. Araştırma, bu ailelerin aynı spot-grid seviye üreticisine veya mevcut exit-trailing ratchet’ına isim değiştirerek bağlanmasına izin vermiyor.

## Kanıt ve çapraz kontrol

1. `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md` içindeki `CLM-113-04` reverse/infinity exact semantics iddiasını `NOT_VERIFIED / DEFER` olarak işaretliyor. Aynı belge, trailing-up için yalnızca gözlenen ürün davranışını kabul ediyor; tam ekonomik state-machine’in yerel olarak geçerli olduğunu iddia etmiyor.
2. `docs/P1_KRITIK_ARASTIRMA_FINAL/sources/SOURCE_CARDS.md` içindeki `S29`, trailing-up davranışını destekliyor; ancak tüm grid ailelerini tanımlamadığını açıkça belirtiyor. Bu nedenle reverse/infinity için numeric sözleşme türetilmedi.
3. Yerel `src/dcabot/application/trailing_ratchet.py` yalnızca long/short exit-trigger ratchet projection’ıdır. Grid range kaydırma, seviye iptali/yeniden yerleştirme, pending order identity, reserve transferi, accepted fill veya replacement sonucu taşımaz. Bu modül grid trailing authority olarak yeniden kullanılmadı.
4. Yerel `src/dcabot/application/spot_grid_levels.py` yalnız exact aritmetik seviyeleri üretir ve unrepresentable step’i sessiz yuvarlamadan reddeder. Range kayması ve yeni grid version sözleşmesi yoktur.

## Güvenli karar

Trailing-up/down için aşağıdaki sınırlar dondurulmadan uygulama yapılmadı:

- tetikleme gözlemi ile ekonomik kabul arasındaki ayrım,
- yeni range’in ve level/index semantiğinin exact tanımı,
- eski grid version, pending emir ve reserve yaşam döngüsü,
- cancel/replace identity, duplicate/conflict ve late fill davranışı,
- partial fill, aynı-bar yarış ve persistence/replay atomicity,
- tick/quantity/notional/fee precision ve rounding sahibi,
- yeni seviyelerin envanter veya kâr sonucu üretmediğinin kanıtı.

Reverse/infinity için boundary, inventory conservation, replacement ve kapanış/EOF semantiği doğrulanmadığından özellik numeric olarak modellenmedi. Leveraged grid ayrıca P1.12 futures margin/profile ve P1.11 shared-account bağlarına bağımlı olduğundan bu mikro-faza alınmadı.

## Kontroller

- İlk odak test denemesi import yolu ayarlanmadığı için `ModuleNotFoundError` verdi; bu bir ürün davranışı sonucu değildir.
- Son doğrulanmış checkout baseline'ında kanonik `tools/run_checks.py` sonucu:
  `712` test, `710 PASS`, Windows Credential Manager `Windows error 1312`
  nedeniyle `2` environment error. Bu iki hata faz dışı credential provider
  ortamına aittir; grid kararını etkilemez.
- `tools/check_workspace.py`: `PASS`; backup discovery kapsam dışı.
- `python -m compileall -q src` ve `git diff --check`: `PASS`.
- Bu mikro-fazda production grid code, API, UI, order/reserve veya persistence
  değişikliği yapılmadı.

## Açma koşulları

Bu karar yalnızca seçilmiş ve sürümlenmiş bir profile şu alanları açıkça tanımladığında yeniden açılabilir: trailing-up/down tetik ve range transition tablosu; reverse/infinity’in ayrı level/inventory/replacement sözleşmesi; exact precision/rounding; event identity ve replay; reserve/order ownership; bağımsız oracle; positive/negative/duplicate/late-fill testleri. Bu kanıtlar gelmeden numeric sonuç veya “tam grid desteği” iddiası yapılmaz.
