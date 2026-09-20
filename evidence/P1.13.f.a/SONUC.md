# P1.13.f.a — Futures Grid v1 profile-bound exact level projection

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.f IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_levels.py`
- Odak test: `tests/test_futures_grid_levels.py` — `7/7 PASS`
- P1.13.a–d ve f.a ilişkili grid kümesi: `25/25 PASS`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.f.b` position/initial-position ve accepted-fill state
  karar kapısı

## Açılan güvenli sınır

Seçilen offline Futures Grid v1 profile ayrı typed record olarak tanımlandı:
`BINANCE`, `USD_M`, `USDT` settlement/margin, `PERPETUAL`, `ONE_WAY`,
`ISOLATED`; leverage yalnız explicit profile alanıdır ve bu dilimde ekonomik
etki üretmez. `LONG`, `SHORT` ve `NEUTRAL` strategy direction değerleri
explicit taşınır. Initial-position policy yalnız `FLAT` kabul edilir; mevcut
position açılışı veya devri varsayılmaz.

Arithmetic ve geometric level setleri exact decimal/rational kök ve explicit
`price_tick`/`tick_origin` ile projekte edilir. Off-grid, non-perfect root,
geçersiz direction/mode/profile veya desteklenmeyen initial-position değeri
fail-closed reddedilir; sessiz rounding yapılmaz. Futures sonucu Spot Grid
state/ledger/position kaydı değildir.

## Bilinçli kapsam dışı

Bu dilim position/fill/inventory, margin reserve/adjustment, leverage etkisi,
funding, mark-price P&L, liquidation estimate, grid-profit/total-equity,
order/replacement, persistence/replay, API/UI, Binance/Testnet mutation ve
canlı emir authority’si açmaz. Bunlar sonraki ayrı profile ve oracle kapılarıdır.

## Kontroller

- Tam regresyon: `719` test, `717 PASS`, Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error. Hatalar faz dışı
  credential provider ortamına aittir; Futures Grid testleri geçmiştir.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`; backup discovery kapsam dışı.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence
  eklenmedi.
