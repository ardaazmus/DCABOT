# P1.12.g.b — Futures DCA max-DCA/stop/EXHAUSTED contract

## Kapsam

Bu mikro-faz, Futures DCA lifecycle’ının stop boundary’sini yalnız offline ve
salt-okunur değerlendirme olarak açar:

- tüketilmemiş ladder varken `CONTINUE`;
- ladder seviyeleri kalırken max-DCA sınırında `STOP`;
- dış stop nedenlerini (`STOP_LOSS`, `TIMEOUT`, `MARKET_CLOSE`, `BOT_STOP`,
  `USER_STOP`) ayrı `STOP` sonucu olarak koruma;
- tüm ladder tüketildiğinde `EXHAUSTED` terminal sonucu.

`EXHAUSTED` dış stop nedeni değildir ve yeni order/recovery talebi üretmez.
Max-DCA, ladder’ın tamamı tüketilmeden de averaging’i durdurabilir. Bu
değerlendirme lifecycle state’i değiştirmez; order/fill/reserve/persistence
yazmaz ve venue/Binance mutation yapmaz. `P1.12.g.a` start gate’i veya
mevcut genel lifecycle state machine’i değiştirilmedi.

## Kanıt

- Odak: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_stop_contract tests.test_futures_dca_start_gate tests.test_deal_lifecycle tests.test_lifecycle_event_contract` — `19/19 PASS`.
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `640` test; `638 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `order_authority=NONE`; stop contract içinde persistence, SQLite/HTTP transport, order attempt, fill veya reserve çağrısı bulunmuyor. AST/write-surface testi PASS.
- Bağımsız doğrudan contract oracle’ı `CONTINUE`, max-DCA `STOP`, full-ladder `EXHAUSTED` ve explicit `TIMEOUT` stop reason önceliklerini PASS doğruladı.
- Compile ve workspace kontrolleri ayrıca çalıştırıldı; `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt yalnız max-DCA, explicit stop reason ve full-ladder `EXHAUSTED`
boundary’sini kapatır. Average-entry TP, split TP, trailing, breakeven,
stop-loss fiyat tetikleme hesabı, terminal persistence ve durable recovery
sonraki mikro-fazlardır.

## Sonraki tek mikro-faz

`P1.12.g.c`: average-entry TP için fill sonrası salt-okunur hedef projection
ve split-TP miktar conservation contract’ı.
