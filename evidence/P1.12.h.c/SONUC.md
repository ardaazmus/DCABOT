# P1.12.h.c — Futures DCA durable profile recovery snapshot ve stale quarantine

## Kapsam

Bu alt faz, profile-bound recovery capability’yi deterministik ve salt-okunur
bir snapshot projection’a bağlar:

- seçilen profile ait event, posting, release ve replay receipt kimlikleri
  yeniden üretilebilir sırada projekte edilir;
- active profile revision farklıysa eski profile snapshot’ı
  `QUARANTINED` olur ve lineage dışarı verilmez;
- active profile bilinmiyorsa veya journal bozuksa `BLOCKED` kalır;
- snapshot yalnız lineage kimliklerini taşır; CORE01 state, ekonomik posting
  uygulaması, order/fill ve venue authority taşımaz;
- projection hiçbir migration, repair veya persistence yazımı yapmaz.

Canlı Binance account/order, venue mutation, mainnet, secret ve CORE01 durable
economic binding bu alt fazın kapsamı değildir.

## Kanıt

- Odak snapshot/quarantine alt kümesi: `4/4 PASS`.
- İlişkili h.a ve h.b recovery/boundary testleriyle toplam odak:
  `47/47 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `698` test;
  `696 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- `uv run --frozen python -m compileall -q src tests` PASS.
- Read-only byte-oracle; stale profile quarantine, missing receipt ve corrupt
  journal sınırları doğrulandı.
- Read-only source-surface kontrolü ve `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Profile recovery snapshot projection hazırdır; stale profile quarantine
fail-closed çalışır ve CORE01 economic admission `BLOCKED` kalır.

## Sonraki tek mikro-faz

`P1.13.c`: Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar ve salt-okunur projection kapısı.
