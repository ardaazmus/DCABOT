# P1.13.d — Geometric grid precision ve quantization karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; bu mikro-fazda production kodu değişmedi.

## İddia kontrolü

Araştırmadaki geometric seviye formülü `r = (Upper / Lower)^(1/N)` ve `level_i = Lower × r^i` olarak tanımlı. Ancak bu kök alma sonucu genel olarak sonlu decimal veya exact Fraction değildir. Projenin `exact_text` sınırı yalnız exact olarak temsil edilebilen değerleri yayınlar; mevcut `align` davranışı quantize etmek yerine değerin profile tick’inde olup olmadığını doğrular.

Geometric sonucu yayınlanabilir order seviyesine dönüştürmek için hesap precision’ı, interval/order-count anlamı, endpoint koruması, instrument tick origin’i, rounding yönü ve quantization owner’ı profile kimliğine bağlanmalıdır. Bunlar seçilmeden yüksek precision bir ara Decimal’i ekonomik seviye olarak kabul etmek sessiz model değişikliği olur.

## Uygulama kararı

Geometric generator, otomatik rounding/quantization, order/fill, inventory, fee, replacement, trailing/reverse/infinity/leveraged grid ve UI eklenmedi. P1.13.a aritmetik generator’ı da bu sınırı korur; exact olmayan decimal sonucu fail-closed reddeder.

## Kanıt

- Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`; geometric formül kabul edilmiş olsa da precision/rounding sahibi verilmemiştir ve local implementation claim’i yoktur.
- Local math: `src/dcabot/domain/numbers.py` içinde `exact_text`, `align` ve `round_quantum` sınırları kontrol edildi.
- Local profile: `src/dcabot/application/instrument_filters.py` off-grid fiyatı reddeder; otomatik quantization yapmaz.
- P1.13.a aritmetik generator exact olmayan step’i yuvarlamadan reddetmektedir.
- Son doğrulanmış baseline: `259/259 PASS`, compile/workspace `PASS`; `110` aktif Python dosyası.

## Yeniden açma koşulları

Versioned spot instrument profile içinde geometric calculation precision, `N` semantiği, endpoint/level sayısı, tick origin, rounding direction/mode ve rejected/adjusted level policy açıkça dondurulmalı; bağımsız yüksek hassasiyet oracle’ı, off-grid/edge/duplicate/replay testleri ve order acceptance boundary kanıtı eklenmelidir.

## Sonraki tek iş

`P1.13.e` — trailing-up/down ve reverse/infinity grid ailelerinin ayrı state/profile karar kapısı. Exact semantics bulunamazsa güvenli DEFER/NO-GO korunacaktır.
