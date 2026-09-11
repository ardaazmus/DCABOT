# P1.13.b — Spot grid accepted-fill inventory projection

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bu mikro-faz yalnız accepted spot fill sonrası exact envanter ve quote cashflow projection’ını kapsar. Production order, reserve ve venue execution authority açılmadı.

## Doğrulanan karar

Accepted BUY base envanterini artırır ve `price × base_quantity` kadar quote cashflow azaltır. Accepted SELL yalnız sahip olunan base envanteri tüketebildiğinde kabul edilir ve aynı exact notional kadar quote cashflow artırır. Aynı `fill_id` ile aynı canonical kayıt tekrarlandığında sonuç değişmez; farklı ekonomik kayıt conflict olarak reddedilir.

## Uygulanan en küçük davranış

`src/dcabot/application/spot_inventory_projection.py` immutable `SpotInventoryState` ve `SpotFill` projection’ı sağlar. Base/quote asset ayrımı açık tutulur; miktar ve cashflow external decimal string, internal hesap exact Fraction sınırındadır. Projection pending order, observation, reserve, replacement, fee, mark-to-market equity veya realized grid profit iddiası taşımaz.

Fee asset’i, fee rounding sahibi ve fee’nin base/quote envanterine etkisi araştırma/local sözleşmeyle kapanmadığı için fee hesabı özellikle eklenmedi. Replacement da yalnız accepted fill/cancel lifecycle kanıtından sonra açılacaktır.

## Kanıt

- RED: yeni test modülü import failure ile beklenen kırmızı durumu verdi.
- GREEN: odak `tests/test_spot_inventory_projection.py` `4/4 PASS`.
- Farklı kontrol: bağımsız Decimal inventory oracle `PASS`.
- Tam regresyon: `uv run --frozen python tools/run_checks.py` → `259/259 PASS`.
- Compile: `python -m compileall -q src` → `PASS`.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `110` aktif Python dosyası.

## Açık sınırlar

Bu projection grid seviyelerinin order’a çevrilmesini, reserve acquisition/release’i, fee posting’i, accepted fill’in mevcut core Store’a atomik binding’ini veya grid cycle replacement’ını kanıtlamaz. Production readiness `NO` olarak kalır.

## Sonraki tek iş

`P1.13.c` — spot grid fee asset/rounding ve matched cycle profit ile total equity ayrımının karar kapısı. Fee sözleşmesi kapanmadan ekonomik grid kârı veya public grid sonucu açılmayacaktır.
