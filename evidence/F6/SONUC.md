# Faz 6 SONUC — Two-leg durable journal + replay/recovery API+UI

Kutu: LCR-09 profili donduruldu (docs/KARARLAR.md). Journal yalniz gozlenen
olayi yazar; replay saf reducer'dan gecer; terminal isaretler operatorundur.

## Kapsam
- `persistence/two_leg_journal.py`: SQLite journal (start/fill/recovery/
  timeout/replay), AttemptStore deseni (app_id+schema, BEGIN IMMEDIATE,
  DUPLICATE-vs-CONFLICT).
- Projection genisletmesi: terminal+fill'siz durum kurulabilir (sozlesme
  tablosundaki LEG_A_PENDING->TIMEOUT karsiligi; BOTH+sifir-fill hâlâ ret).
- 5 endpoint: sessions, fills, recovery, timeout, replay. TwoLegPanel UI.

## Dogrulama
- `uv run --frozen python tools/run_checks.py`: 1128/1128 PASS.
- `npx tsc -b`: temiz. `npx vitest run`: 69/69 PASS (TwoLegPanel 3).
- Journal testleri: 12/12; API testleri (`tests/api/test_two_leg.py`): 8/8.
- Canli smoke (iki sunucu omru): start>fill ONE_LEG_FILLED 0.5, restart
  sonrasi replay ayni, recovery RECOVERY_REQUIRED, timeout TIMEOUT —
  F6_SMOKE_PASS.

## Sinirlar
- Same-scope HEDGE; cross-venue atomicity + economic binding PLAN.
- Order/reserve/fill posting acilmadi; recovery aksiyonu operatorundur.
- `gate F6`: PASS.
