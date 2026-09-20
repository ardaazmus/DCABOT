# P1.12.g.a — Futures DCA start-condition gate

## Kapsam

Bu mikro-faz, Futures DCA lifecycle’ının ilk start boundary’sini yalnız offline
ve salt-okunur değerlendirme olarak açar:

- `IMMEDIATE` başlangıç koşulu;
- `CLOSED_CANDLE` source-time sınırı;
- mevcut `SignalReadiness` sonucuna bağlı `SIGNAL` başlangıcı.

`SignalReadiness` closed-bar, warmup ve staleness sahipliğini korur. Start
değerlendirmesi lifecycle oluşturmaz, order/fill üretmez, reserve/persistence
yazmaz ve venue/Binance mutation yapmaz. Calendar DCA bu sözleşmeye dahil
edilmedi; araştırma kararına uygun olarak ayrı ürün ailesi kabul edildi.

## Kanıt

- Odak: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_start_gate tests.test_signal_readiness tests.test_signal_event_contract tests.test_deal_lifecycle` — `20/20 PASS`.
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `634` test; `632 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `order_authority=NONE`; start gate içinde persistence, SQLite/HTTP transport, order attempt, fill, reserve veya lifecycle mutation bulunmuyor. AST/write-surface testi PASS.
- Compile ve workspace kontrolleri ayrıca çalıştırıldı; `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt yalnız start eligibility/blocking boundary’sini kapatır. Stop/max-DCA
ve `EXHAUSTED`, average-entry TP, split TP, trailing, breakeven, stop-loss,
terminal policy ve durable recovery bu mikro-fazda açılmadı.

## Sonraki tek mikro-faz

`P1.12.g.b`: max-DCA/stop koşulları ve `EXHAUSTED` terminal sınırının lifecycle
mutasyonu olmadan, explicit event/state contract olarak doğrulanması.
