# P1.13.f.b — Futures Grid one-way position and accepted-fill state

## Sonuç

- Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
- Ana faz: `P1.13.f IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_position.py`
- Odak test: `tests/test_futures_grid_position.py` — `9/9 PASS`
- P1.13.a–d, f.a ve f.b ilişkili grid kümesi: `34/34 PASS`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.13.f.c` isolated margin/leverage ve reserve karar kapısı

## Açılan güvenli sınır

Seçilen Futures Grid profile içinde yalnız `ONE_WAY` + `FLAT` başlangıçtan
gelen `LONG` veya `SHORT` position projection uygulanıyor. Accepted BUY/SELL
fill’leri exact quantity ve weighted average-entry ile immutable in-memory
state’e ekleniyor. Close fill mevcut position kapasitesini aşamaz; position
flip’i, flat state’te ters yönde açılış ve geriye giden effective time
fail-closed reddediliyor. Aynı `fill_id` aynı payload ile idempotent, farklı
payload ile conflict’tir.

## Bilinçli kapsam dışı

`NEUTRAL` netleme, initial non-flat position, position flip, realized/unrealized
P&L, contract-size/margin reserve, leverage effect, funding, mark-price,
liquidation, order/replacement, persistence/replay, API/UI, Binance/Testnet
mutation ve canlı emir authority’si açılmadı. Bu projection accepted fill’i
position state’e taşır; ekonomik posting veya realized P&L üretmez.

## Kontroller

- Tam regresyon: `728` test, `726 PASS`, Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error. Hatalar faz dışı
  credential provider ortamına aittir; Futures Grid odak testleri geçmiştir.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`; backup discovery kapsam dışı.
- `git diff --check`: `PASS`.
- Gerçek API key/secret, signed request, order mutation, mainnet ve persistence
  eklenmedi.
