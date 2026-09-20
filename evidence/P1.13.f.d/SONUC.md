# P1.13.f.d — Futures Grid funding/mark/P&L projection

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.f IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_pnl.py`
- Odak test: `tests/test_futures_grid_pnl.py` — `5/5 PASS`
- P1.13.a–d, f.a, f.b, f.c ve f.d ilişkili grid kümesi: `45/45 PASS`
- Tam suite: `739` testte `737 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.g.a` dynamic order placement ile grid range/trailing ayrımı karar kapısı

## Açılan güvenli sınır

Kabul edilmiş Futures Grid fill’lerinden realized gross P&L, explicit
reference mark price üzerinden unrealized P&L ve caller-supplied signed funding
cashflow event’leri ayrı tutuluyor. `matched_cycle_profit`, açık inventory’yi
hariç tutan realized gross P&L + funding cashflow projection’ıdır; `total_pnl`
aynı sonuca açık inventory mark hareketini ekler. Funding rate veya mark price
venue’dan çekilmiyor; event kimliği, asset, zaman sırası ve snapshot sınırı
fail-closed doğrulanıyor.

## Bilinçli kapsam dışı

`total_equity` üretilmiyor; hesap bakiyesi, reserve mutation, maintenance
margin, liquidation, fee conversion, persistence, replay, API/UI,
Binance/Testnet mutation ve canlı emir authority’si açılmadı. Contract-size
`1` varsayılmıyor. Funding event’i signed cashflow olarak caller tarafından
sağlanıyor; funding-rate veya venue payment direction varsayılmıyor. Mark price
yerel projection girdisidir, venue mark authority değildir.

## Kontroller

- Tam regresyon: `739` test, `737 PASS`, faz dışı Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence eklenmedi.
