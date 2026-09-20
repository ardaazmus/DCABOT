# P1.12.h.b — Futures DCA profile-bound recovery capability ve CORE01 boundary

## Kapsam

Bu alt faz, mevcut durable journal içinden tek bir profile revision için
recovery capability kararı üretir. Karar yalnız salt-okunur loader ve
preflight’lerden oluşur:

- profile revision checksum ve event sequence/link replay doğrulanır;
- seçilen profile ait accepted event, economic posting, release transition ve
  CORE01 replay receipt kapsamları birebir eşleştirilir;
- eksik receipt, release veya cross-profile transition fail-closed `BLOCKED`
  kalır;
- journal bozukluğu `BLOCKED` olur, yeni migration veya repair yazılmaz;
- recovery `READY` olsa bile CORE01 admission açık değildir; mevcut intent,
  role, side ve limit authority eksikliği `BLOCKED` olarak taşınır.

Canlı Binance account/order, venue mutation, mainnet, secret ve CORE01 durable
economic binding bu alt fazın kapsamı değildir.

## Kanıt

- Odak capability ve boundary alt kümesi: `4/4 PASS`.
- İlişkili h.a replay, schema, atomicity ve CORE01 testleriyle toplam odak:
  `43/43 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `694` test;
  `692 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- `uv run --frozen python -m compileall -q src tests` PASS.
- Read-only byte-oracle, unknown profile, missing receipt, corrupt profile ve
  CORE01 admission boundary sınırlarını doğruladı.
- `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Profile-bound recovery capability hazırdır; CORE01 economic admission hâlâ
`BLOCKED` ve order authority `NONE`’dır.

## Sonraki tek mikro-faz

`P1.12.h.c` ve `P1.12.h.d` ile durable recovery snapshot, immutable
profile-source provenance cross-check ve publish/migration NO-GO gate’i
kapatıldı; sıradaki `P1.13.c`: Spot Grid fee asset/rounding ve matched cycle
profit-total equity ayrımının karar kapısı.
