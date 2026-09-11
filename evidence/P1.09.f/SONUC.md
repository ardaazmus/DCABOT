# P1.09.f — Realized-profit eligible reinvestment sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

P1.09 araştırmasındaki yeniden yatırım sınırı, yalnız `realized_profit_eligible` havuzundan ve açık asset etiketinden bütçe üretilecek şekilde saf application projection olarak uygulandı.

## Uygulanan davranış

`build_reinvestment_budget`:

- asset kodunu explicit ve büyük harfli ister;
- `realized_profit_eligible` pool değerini exact decimal string olarak parse eder;
- negatif pool’u reddeder;
- reinvestment percent’i `0..1` aralığında kabul eder;
- `budget = realized_profit_eligible * percent` hesabını exact yapar;
- pool türünü sabit `REALIZED_PROFIT_ELIGIBLE` metadata’sıyla döndürür.

Zero pool veya zero percent numeric olmayan gizli bir değer üretmez; exact `0` budget verir. Fonksiyon unrealized PnL, fee/funding veya account balance keşfetmez ve ledger/reserve/order üzerinde yan etki oluşturmaz.

## Kanıt zinciri

### RED

Yeni `tests/test_reinvestment_budget.py`, henüz mevcut olmayan `dcabot.application.reinvestment_budget` modülünü import ettiği için test discovery aşamasında `ModuleNotFoundError` verdi.

### GREEN

`src/dcabot/application/reinvestment_budget.py` eklendikten sonra proje kontrolü:

```text
Ran 191 tests ... OK
```

Odak testleri `100 * 0.5 = 50` exact projection’ını, zero sınırını ve negative pool/wrong asset reddini doğrular.

### Farklı kontrol

Reinvestment suite’i doğru `src` import yolu ile bağımsız unittest hedefi olarak `3/3 PASS` geçti. `compileall` ve `tools/check_workspace.py` de PASS verdi.

## Açık sınırlar

- Projection yalnız caller-supplied realized eligible pool’ü kabul eder; pool’ü üreten ledger authority’si yoktur.
- Unrealized PnL’nin reject edilmesi bu API’nin alan tasarımıyla korunur; mevcut ekonomik reducer’a bağlanmadı.
- Fee/funding allocation, reserve, multi-deal cashflow, risk, API/UI, persistence ve economic posting yoktur.
- P1.09.g pre-acceptance gate tamamlanmadan bu projection public sizing/order yoluna bağlanmayacaktır.
