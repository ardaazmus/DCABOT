# P1.10.f — Breakeven fee/asset conversion karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`

Bu mikro fazda üretim kodu yazılmadı. Karar, doğrulanmamış bir breakeven formülünü sisteme sokmamak üzere kapatıldı.

## Doğrulanan kanıt

- `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` fee-aware breakeven’i ancak ücret varlığı, dönüşüm ve maliyet tahsisi profili açıkça tanımlanırsa koşullu kabul ediyor.
- Yerel `Config` yalnız `GROSS_PRICE_RETURN` ve `NET_QUOTE` hedef modlarını kabul ediyor; açık bir `BREAKEVEN` modu veya breakeven parametresi yok.
- Yerel engine’de execution fee yalnız `quote_asset` ile eşleştiğinde kabul ediliyor; farklı fee asset için dönüşüm kaynağı/oranı/zamanı yok.
- Yerel `NET_QUOTE` hesabı, position cost, toplam maliyet, realized ve beklenen çıkış ücretini kullanan genel bir net hedef hesabıdır; bu, açıkça tanımlanmış fee-aware breakeven sözleşmesinin kanıtı değildir.
- Funding state’i mevcut olsa da breakeven için hangi funding tutarının ve hangi pozisyona tahsis edileceği tanımlı değildir.

## Kontroller

`tests.test_math_core.MathTests.test_net_target_and_liquidation_roots` mevcut NET_QUOTE kök hesabını doğrular. Bu kontrol yalnız generic NET_QUOTE davranışını kanıtlar; breakeven davranışının geçtiği iddia edilmez.

Bu nedenle RED/GREEN implementasyon döngüsü çalıştırılmadı: uygulanacak güvenli bir hedef sözleşmesi yoktur ve yeni ekonomik varsayım eklemek plan dışı olur. Kod değişikliği yoktur.

## Açık önkoşullar

Breakeven yeniden açılmadan önce tek bir explicit sözleşmede şunlar tanımlanmalı ve bağımsız exact oracle ile test edilmelidir:

1. `BREAKEVEN` hedefinin kapsamı: giriş maliyeti, daha önce ödenen fee, beklenen çıkış fee’si ve funding tahsisi.
2. Fee asset farklı olduğunda conversion rate/source/time ve veri yokluğunda fail-closed durumu.
3. Economic precision, tick quantization ve rounding owner.
4. Trigger ile accepted economic fill ayrımı.
5. Partial fill, duplicate/replay ve position kapanışında invariant’lar.
