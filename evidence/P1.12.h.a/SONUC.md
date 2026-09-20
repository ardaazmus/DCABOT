# P1.12.h.a — Futures DCA durable recovery/replay readiness gate

## Kapsam

Bu alt faz, mevcut greenfield Futures DCA journal’ının restart sonrası güvenli
okunabilirliğini ve CORE01’e bağlanmadan önceki readiness sınırını doğrular:

- schema v4; profile revision, journal event, reservation, release transition,
  economic posting ve CORE01 replay receipt sahiplerini ayrı tutar;
- replay sequence, canonical payload/checksum ve foreign-key/link ilişkilerini
  doğrular; bozuk veya eksik projection fail-closed kalır;
- receipt preflight `query_only` ile çalışır, eksik schema/unique constraint’i
  oluşturmaz ve `BLOCKED` döndürür;
- event + release + posting + receipt atomic transaction’ı failure injection
  sonrasında kısmi state bırakmaz;
- exact duplicate `DUPLICATE`, farklı payload/scope `CONFLICT` olarak kalır;
- CORE01 economic admission mapping’i mevcut olmadığı için `BLOCKED` kalır.

Yerel durable journal kanıtı vardır; canlı Binance account/order, venue
mutation, mainnet ve CORE01 economic binding bu alt fazın kapsamı değildir.

## Kanıt

- Odak readiness alt kümesi: journal schema, release store, replay receipt,
  atomic replay, restart oracle, CORE01 binding ve event store testleri —
  `39/39 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `690` test;
  `688 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- `uv run --frozen python -m compileall -q src tests` PASS.
- Bağımsız restart oracle; missing receipt, stale admission, checksum/tamper,
  receipt conflict ve reservation corruption sınırlarını doğruladı.
- Read-only preflight source/test contract’ı local schema’yı değiştirmedi;
  CORE01 binding kararı `BLOCKED` ve `order_authority=NONE` kaldı.
- `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt durable recovery/replay readiness sınırını kapatır; CORE01 economic
admission ve profile-bound recovery capability henüz hazır değildir.

## Sonraki tek mikro-faz

`P1.12.h.b`, `P1.12.h.c` ve `P1.12.h.d` ile profile-bound recovery,
durable snapshot, immutable profile-source provenance cross-check ve
publish/migration NO-GO gate’i kapatıldı; sıradaki `P1.13.c`: Spot Grid fee
asset/rounding ve matched cycle profit-total equity ayrımının karar kapısı.
