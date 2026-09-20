# P1.13.f.c — Futures Grid isolated margin/leverage and reserve projection

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.f IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_margin.py`
- Odak test: `tests/test_futures_grid_margin.py` — `6/6 PASS`
- P1.13.a–d, f.a, f.b ve f.c ilişkili grid kümesi: `40/40 PASS`
- Tam suite: `734` testte `732 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.f.d` funding/mark/liquidation ve grid profit/total-P&L karar kapısı

## Açılan güvenli sınır

P1.13.f.b ile açılmış LONG/SHORT position state üzerinden, caller tarafından
verilen exact `contract_size` ve `reference_price` ile notional ve isolated
initial-margin gereksinimi hesaplanıyor. Leverage yalnızca
`required_initial_margin = notional / leverage` projection’ında kullanılıyor;
P1.13.f.a profilindeki explicit leverage değeri sessizce varsayılanla
değiştirilmiyor. `available_margin` verilmezse kapasite `UNVERIFIED`, verilirse
yalnız yerel karşılaştırma sonucu `ELIGIBLE` veya
`INSUFFICIENT_AVAILABLE_MARGIN` olarak raporlanıyor.

## Bilinçli kapsam dışı

Contract-size, reference price veya available margin venue tarafından
doğrulanmıyor; contract-size için `1` varsayımı yapılmıyor. Bu projection
exchange balance, reserve mutation veya order authority değildir. Maintenance
margin, fee, funding, mark-price authority, liquidation, P&L, persistence,
replay, API/UI, Binance/Testnet mutation ve canlı emir açılmadı. Non-terminating
initial-margin sonucu rounding yapılmadan fail-closed reddediliyor.

## Kontroller

- Tam regresyon: `734` test, `732 PASS`, faz dışı Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence eklenmedi.
