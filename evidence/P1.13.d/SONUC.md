# P1.13.d — Geometric grid precision ve quantization karar kapısı

## Durum

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## İddia kontrolü

Araştırmadaki geometric seviye formülü `r = (Upper / Lower)^(1/N)` ve `level_i = Lower × r^i` olarak tanımlı. Ancak bu kök alma sonucu genel olarak sonlu decimal veya exact Fraction değildir. Projenin `exact_text` sınırı yalnız exact olarak temsil edilebilen değerleri yayınlar; mevcut `align` davranışı quantize etmek yerine değerin profile tick’inde olup olmadığını doğrular.

Geometric sonucu yayınlanabilir order seviyesine dönüştürmek için hesap precision’ı, interval/order-count anlamı, endpoint koruması, instrument tick origin’i, rounding yönü ve quantization owner’ı profile kimliğine bağlanmalıdır. Bunlar seçilmeden yüksek precision bir ara Decimal’i ekonomik seviye olarak kabul etmek sessiz model değişikliği olur.

## Uygulanan en küçük davranış

`build_geometric_grid_levels` exact rational `N`-inci kökü ile geometric
oranı hesaplıyor. Oran perfect rational root değilse veya üretilen herhangi bir
seviye declared `price_tick`/`tick_origin` grid’ine tam oturmuyorsa fail-closed
reddediliyor. Otomatik rounding, yüksek hassasiyetli float/Decimal yaklaşımı
ve endpoint düzeltmesi yapılmıyor.

Accepted fill, inventory, fee, replacement, trailing/reverse/infinity/leveraged
grid ve UI bu mikro-fazın dışındadır. Sonuç immutable level projection’dır;
order authority taşımaz.

## Kanıt

- Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`; geometric formül, `N` semantiği ve rounding owner sınırı doğrulandı.
- Local math: `src/dcabot/domain/numbers.py` içinde `exact_text`, `align` ve `round_quantum` sınırları kontrol edildi.
- Local profile: `src/dcabot/application/instrument_filters.py` off-grid fiyatı reddeder; otomatik quantization yapmaz.
- P1.13.a aritmetik generator exact olmayan step’i yuvarlamadan reddetmektedir.
- Odak `tests/test_spot_grid_levels.py`: `9/9 PASS`; geometric bağımsız literal oracle, perfect-root, repeating-ratio, off-tick ve authority sınırları kapsandı.
- P1.13.a–d ilişkili Spot Grid kümesi: `18/18 PASS`.
- Compile, workspace, read-only source-surface ve `git diff --check`: `PASS`.
- Tam proje: `712` testte `710 PASS`; faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error.

## Yeniden açma koşulları

Versioned spot instrument profile içinde geometric calculation precision, `N` semantiği, endpoint/level sayısı, tick origin, rounding direction/mode ve rejected/adjusted level policy açıkça dondurulmalı; bağımsız yüksek hassasiyet oracle’ı, off-grid/edge/duplicate/replay testleri ve order acceptance boundary kanıtı eklenmelidir.

## Sonraki tek iş

`P1.13.e` — trailing-up/down ve reverse/infinity grid ailelerinin ayrı state/profile karar kapısı. Exact semantics bulunamazsa güvenli DEFER/NO-GO korunacaktır.
