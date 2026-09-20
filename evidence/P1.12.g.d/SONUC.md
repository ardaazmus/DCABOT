# P1.12.g.d — Futures DCA fee-aware breakeven contract

## Kapsam

Bu mikro-faz, observed Futures DCA fill projection’ı için fee-aware breakeven
sınırının hangi açık ekonomik profile bağlı olduğunu kapatır:

- fee/funding profili olmadan yalnız gross boundary (`average_entry`) gösterilir;
- settlement asset dışındaki üçüncü fee asset’i conversion profili olmadan reddedilir;
- entry/exit fee oranları ve signed funding cashflow açık profile revision’a bağlıdır;
- explicit `PROPORTIONAL_SETTLEMENT_NOTIONAL` modelinde LONG/SHORT breakeven
  exact hesaplanır;
- hedef fiyat tick grid dışında veya exact decimal sözleşmesine sığmıyorsa
  fee-aware sonuç fail-closed kalır.

Bu faz venue commission/funding oranı keşfetmez, fee conversion yapmaz, TP/SL,
OCO, cancel-replace, reserve, persistence veya order mutation açmaz.

## Kanıt

- Odak: `uv run --frozen python -m unittest tests.test_futures_dca_breakeven_contract -v` — `9/9 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `656` test; `654 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- Bağımsız Fraction oracle LONG/SHORT fee ve signed funding formüllerini `PASS` doğruladı.
- `uv run --frozen python -m compileall -q src tests` PASS.
- AST/write-surface testi persistence/transport write çağrısı bulunmadığını doğruladı; `order_authority=NONE`.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt yalnız explicit fee-aware breakeven projection’ını kapatır. Venue’ye
özgü fee asset conversion, fee rounding, funding schedule/source, exit priority,
trailing execution, OCO/cancel-replace, durable lifecycle ve gerçek Binance
account/order akışı sonraki kapılardır.

## Sonraki tek mikro-faz

`P1.12.g.e`: TP/SL/trailing/breakeven exit priority ve aynı anda tetiklenme
karar contract’ını, gerçek execution açmadan doğrulamak.
