# P1.13.g.a — Futures Grid dynamic order placement boundary

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_order_placement.py`
- Odak test: `tests/test_futures_grid_order_placement.py` — `4/4 PASS`
- P1.13.a–d, f.a–f.d ve g.a ilişkili grid kümesi: `49/49 PASS`
- Tam suite: `743` testte `741 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.g.b` trailing/expansion/reversal/range revision ve replacement karar kapısı

## Açılan güvenli sınır

Statik `FIXED` placement, daha önce exact üretilmiş Futures Grid seviyelerini
yalnız inert candidate listesi olarak döndürüyor. `DYNAMIC` placement ile
`RANGE_REVISION` ayrı sözleşmeler olarak sınıflandırılıyor ve exact current-price
selection, range transition, reserve, cancel/replace identity ve replay
kanıtlanana kadar `BLOCKED_CONTRACT_REQUIRED` dönüyor. Sonuçta
`order_authority=NONE`; order ID, request veya mutation üretilmiyor.

## Bilinçli kapsam dışı

Dynamic order selection, current-price/working-type authority, pending order
ve reserve lifecycle, replacement identity, trailing/expansion/reversal,
range revision, persistence/replay, API/UI, Binance/Testnet mutation ve canlı
emir açılmadı. Static candidate listesi kabul edilmiş fill veya order değildir;
ekonomik state’i değiştirmez.

## Kontroller

- Tam regresyon: `743` test, `741 PASS`, faz dışı Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence eklenmedi.
