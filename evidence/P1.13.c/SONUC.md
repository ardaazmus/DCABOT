# P1.13.c — Spot grid fee ve cycle/equity karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; bu mikro-fazda production kodu değişmedi.

## İddia kontrolü

Araştırma, accepted grid sell’in sahip olunan base kapasitesini tüketmesini, accepted buy’ın inventory artırmasını ve matched grid profit’in total equity ile aynı sayı olmadığını belirtiyor. Aynı araştırma fee asset/unit etiketini, fee rounding owner’ını ve per-fill rounding politikasını zorunlu tutuyor; rounding owner yoksa fail-closed kararı veriyor.

Local core kontrolünde `FILL` event’i `fee_asset == config.quote_asset` şartı taşıyor ve `State.fees` tek bir scalar quote gideri olarak tutuluyor. Bu, spot fee’nin base asset olarak envanterden düşülmesini veya üçüncü bir fee asset’inin zamanlı kurla değerlenmesini temsil etmiyor. `State.equity` de tek bir position mark’ına bağlı CORE01 hesabıdır; grid’in açık base inventory mark-to-market değeri, matched cycle realized profit’i ve toplam equity köprüsü değildir.

## Uygulama kararı

Fee asset/rounding/posting ve cycle-profit/equity projection eklenmedi. Mevcut generic fee toplamını grid fee authority olarak yeniden kullanmak güvenli değildir. Geometric precision/quantization, accepted FILL’in core Store’a bağlanması, replacement, reserve, multi-asset valuation, API/UI ve public grid sonucu da açılmadı.

## Kanıt

- Local inspection: `src/dcabot/domain/engine.py` içinde strict `FILL` fee asset kontrolü, scalar `fees` ve CORE01 single-position equity formülü doğrulandı.
- Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`; fee/rounding owner ve grid profit/equity ayrımı için kanıt mevcut, local implementation claim’i yok.
- Önceki doğrulanmış kod baseline: `259/259 PASS`.
- Compile ve workspace baseline: `PASS`; `110` aktif Python dosyası.
- Karar: fee varlığı/yuvarlama sahibi ve çok varlıklı equity valuation contract’ı seçilmeden numeric grid net sonucu güvenli değildir.

## Yeniden açma koşulları

Seçilen spot model için fee asset (quote/base/third), fee sign, per-fill rounding quantum/mode, fee’nin inventory/cashflow etkisi, accepted fill ve persistence identity, mark authority ve bağımsız Decimal oracle dondurulmalıdır. Matched cycle realized profit ile open inventory mark-to-market total equity ayrı alanlar olarak modellenmeli; duplicate/replay ve partial-fill property testleri geçmelidir.

## Sonraki tek iş

`P1.13.d` — geometric seviye precision/quantization veya mevcut kanıt yetersizse güvenli karar kapısı. Reverse/infinity/trailing/leveraged grid hâlâ ayrı profile ve bağımlılık kapılarıdır.
