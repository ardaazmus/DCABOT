# P1.13.a — Spot grid aritmetik seviye üretimi

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bu mikro-faz yalnız aritmetik spot-grid seviye üretimini kapsar. Production order authority, inventory veya ekonomik posting açılmadı.

## Doğrulanan karar

Araştırmadaki `ArithmeticGridStep = (Upper - Lower) / N` ve `N + 1` seviye sözleşmesi exact Fraction/decimal sınırında uygulandı. Alt ve üst fiyat pozitif olmalı, üst sınır alt sınırdan büyük olmalı ve `interval_count` 1–1000 aralığında tam sayı olmalıdır. Exact decimal sözleşmesine sığmayan seviye sessizce yuvarlanmak yerine fail-closed reddedilir.

## Uygulanan en küçük davranış

`src/dcabot/application/spot_grid_levels.py` içindeki `build_arithmetic_grid_levels` yalnız immutable seviye kümesi ve exact step üretir. Sonuçta alt/üst fiyat, interval count, step ve seviyeler string olarak taşınır. Fonksiyon order, fill, reserve, inventory, fee, realized grid profit, equity, replacement veya venue quantization üretmez.

Geometric seviye üretimi, kök alma sonrası decimal precision/quantization sahibi açıkça seçilmediği için bu mikro-faza alınmadı. Trailing, reverse, infinity ve leveraged grid ayrıca bekletiliyor; leveraged grid P1.12/P1.11 bağımlılıklarını bypass etmiyor.

## Kanıt

- RED: yeni test modülü import failure ile beklenen kırmızı durumu verdi.
- GREEN: odak `tests/test_spot_grid_levels.py` `4/4 PASS`.
- Farklı kontrol: bağımsız `Decimal` oracle, `1000..2000 / 10` için `PASS`.
- Tam regresyon: `uv run --frozen python tools/run_checks.py` → `255/255 PASS`.
- Compile: `python -m compileall -q src` → `PASS`.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `108` aktif Python dosyası.

## Açık sınırlar

Bu sonuç grid seviyelerinin doğru üretildiğini kanıtlar; seviyelerin order’a dönüşmesini, pending reserve’i, accepted FILL’i, envanter tüketimini, fee allocation’ını veya grid profit/equity ayrımını kanıtlamaz. Production readiness `NO` olarak kalır.

## Sonraki tek iş

`P1.13.b` — spot grid inventory/fee ve accepted-fill sonrası cycle/replacement karar kapısı. Replacement yalnız accepted fill/cancel lifecycle kapsamı kanıtlandıktan sonra açılacaktır.
