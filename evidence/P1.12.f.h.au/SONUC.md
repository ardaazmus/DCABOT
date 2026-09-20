# P1.12.f.h.au — durable replay integrity oracle

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`

Read-only CORE01 replay restart oracle genişletildi. Oracle artık durable
event, economic posting, release history ve reservation son projection
yükleyicilerinin checksum/consistency kontrollerini kullanır; bozuk durable
veri exception olarak dışarı taşınmadan `BLOCKED` ve
`FUTURES_DCA_CORE_REPLAY_ORACLE_DURABLE_CORRUPT` ile fail-closed kalır.

Pure replay sınırları da restart değerlendirmesine bağlandı:

- aynı reservation projection ile ikinci uygulama `DUPLICATE` olmalıdır;
- aynı receipt girdilerinin retry değerlendirmesi `DUPLICATE` olmalıdır;
- aynı scope içinde değişmiş posting/fingerprint retry’si `BLOCKED` conflict
  olmalıdır;
- durable receipt aynı scope ile farklı fingerprint taşıyorsa
  `FUTURES_DCA_CORE_REPLAY_ORACLE_RECEIPT_CONFLICT` döner.

Receipt eksikliği, reservation eksikliği ve stale CORE admission önceki
fail-closed davranışını korur. Oracle hiçbir durable satıra yazmaz; Binance,
venue mutation, CORE01 durable ownership, gerçek emir, mainnet, secret,
migration veya publish açılmadı.

## Kanıt

- Odak test: `15/15 PASS`
- İlişkili küme: `55/55 PASS`
- Tam proje suite: `611/611 PASS`
- Compile: `PASS`
- Workspace kontrolü: `PASS`
- Aktif Python dosyası: `238`
- Workspace backup layout: `EMPTY_OR_NOT_PLACED`

Çalıştırılan kapsam:

- `tests.test_futures_dca_core_replay_oracle`
- `tests.test_futures_dca_core_replay_atomic`
- `tests.test_futures_dca_core_replay_store`
- ilgili mapping, journal schema, release transition/store, atomic binding ve
  CORE binding testleri
- `tools/run_checks.py`
- `python -m compileall -q src tools tests`
- `tools/check_workspace.py`

Yeni testler posting checksum bozulmasını, reservation projection bozulmasını
ve receipt fingerprint conflict’ini doğrudan SQLite fixture üzerinde doğrular;
test fixture bağlantıları explicit close/commit ile Windows cleanup kilidini
korumalı biçimde kapatır.

## Sıradaki tek mikro-faz

`P1.12.f.h.av` — read-only replay integrity oracle için bağımsız inceleme ve
kritik gate değerlendirmesi. Bu fazda yeni ekonomik davranış veya venue
mutasyonu açılmayacaktır.
