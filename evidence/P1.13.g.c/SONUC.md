# P1.13.g.c — Futures Grid replacement/replay ve late-fill identity karar kapısı

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_replacement_replay_gate.py`
- Odak test: `tests/test_futures_grid_replacement_replay_gate.py` — `3/3 PASS`
- P1.13.a–d, f.a–f.d, g.a–g.c ilişkili grid kümesi: `55/55 PASS`
- Tam suite: `749` testte `747 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Ana P1.13.g’nin kalan advanced davranışları: `CONTRACT_REQUIRED`

## Açılan güvenli sınır

`RANGE_REVISION`, `CANCEL_REPLACE`, `LATE_FILL` ve `REPLAY` typed yaşam
döngüsü sınırları olarak ayrıldı. Her sınır için gerekli yüksek-seviye
sözleşme başlıkları açıkça listeleniyor: exact range transition, replacement
identity, pending/reserve lifecycle, late-fill authority ve deterministic replay
oracle. Exact kaynak ve oracle doğrulanana kadar sonuç
`BLOCKED_CONTRACT_REQUIRED` ve `order_authority=NONE`.

Gate yalnızca karar/checklist üretir. Order ID, replacement ID, candidate level,
state transition, economic posting, persistence, API/UI veya Binance/Testnet
mutation üretmez.

## Bilinçli kapsam dışı

Replacement/cancel confirmation, reserve/commitment owner, late-fill authority,
replay cursor/oracle, dynamic range transition, order placement, accepted fill,
P&L, margin, liquidation, funding, API/UI, signed request ve canlı emir açılmadı.

## Kontroller

- Tam regresyon: `749` test, `747 PASS`, faz dışı Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- Focus: `3/3 PASS`.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence eklenmedi.
