# P1.12.h.d — Futures DCA recovery snapshot provenance ve publish/migration gate

## Kapsam

Bu alt faz, `P1.12.h.c` recovery snapshot’ını immutable profile-source
provenance target’ı ve canonical migration manifest ile salt-okunur karşılaştırır:

- recovery ve provenance journal’ındaki seçili profile revision birebir eşleşir;
- seçili profile tam bir `ACCEPTED` source snapshot bağlanmadıysa karar
  `NO_GO` olur;
- manifest hash, reopened target ve bağımsız hash/oracle sonucu birlikte
  değerlendirilir;
- stale recovery snapshot, profile mismatch, eksik/bozuk provenance veya önceki
  gate/oracle başarısızlığı fail-closed kalır;
- temiz sonuç yalnız `READY_FOR_REVIEW` üretir; `publish_action` ve
  `migration_action` her durumda `BLOCKED` kalır.

Gerçek source export, legacy migration, otomatik publish, canlı Binance,
secret, order/fill mutation ve CORE01 economic admission bu alt fazın kapsamı
değildir.

## Kanıt

- Yeni recovery-to-provenance gate odak testleri: `4/4 PASS`.
- P1.12.h.a–h.d ilişkili recovery/replay kümesi: `51/51 PASS`.
- Provenance target, manifest ve bağımsız reopen/hash oracle kümesi: `18/18
  PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `702` test;
  `700 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- `uv run --frozen python -m compileall -q src tests` PASS.
- Gate source-surface read-only kontrolü PASS; publish/migration write authority
  üretilmedi.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Recovery snapshot ile immutable provenance eşleşmesi doğrulanabilir hale geldi;
hazır sonuç yalnız insan incelemesine gider ve publish/migration `NO_GO` olarak
kapalı kalır. Mevcut projede gerçek ve eksiksiz source export bulunmadığı için
gerçek migration/publish readiness iddiası yoktur.

## Sonraki tek mikro-faz

`P1.13.c`: Spot Grid fee asset/rounding ve matched cycle profit ile total equity
ayrımının karar ve salt-okunur projection kapısı.
