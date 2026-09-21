# Faz 10 kanıt — SONUC.md (F20 + 9 yeni aile dilimi, 2026-09-21)

## F20 şablon (önceki kapı, özet)
Onaylı profile binding + materialization/import-export/diff + 6
endpoint + TemplatePanel. `phase_gate.py F20` GATE PASS (kanıt korunur).

## F16 recurring projection
`POST /api/recurring/schedule` saf projeksiyon + RecurringPanel. 3/3
API + 2/2 panel testi. Zamanlanmış yürütme yok (PLAN).

## F22 run export
`GET /api/historical-runs/{run_id}/export` CSV/JSON + SavedRunsPanel
bağlantısı. 3/3 API testi. CANLI: export roundtrip kanıtlı.

## F28 dashboard
`GET /api/dashboard` paper+bot aggregation (read-only) +
DashboardPanel. 2/2 API + 2/2 panel testi. Venue account PLAN.

## F29 chart üstünde taslak
`POST /api/datasets/{id}/draft-level` sha-bound ACCEPTED/REJECTED +
sürükleme/klavye/metin UI. 4/4 API + 17/17 chart testi (4 yeni).
CANLI: ACCEPTED (94401.14) + REJECTED (1.5) + sha-mismatch 422.

## F33 olay merkezi
`GET /api/events` yerel liste + EventPanel. 2/2 API + 2/2 panel
testi. Dış kanallar DEFERRED.

## F35 settlement
USDT-only `GET /api/settlement` + settlement_profile gate. 4/4
test. Çoklu settlement DEFERRED (kur/envanter yok).

## F36 backup
`POST /api/admin/backup` + verify + liste + BackupPanel. 5/5 API +
2/2 panel testi (traversal-safe). Restore otomasyonu PLAN.

## F39 risk açıklaması
`POST /api/risk/explain` read-only + RiskPanel. 5/5 API + 2/2 panel
testi. Değişiklik-etkisi simülasyonu PLAN.

## F40 timeline replay
`GET /api/deals/{id}/timeline` step/seek + TimelinePanel oynatma/hız.
5/5 API + 2/2 panel testi. Salt okunur, yeni dal yok.

- Tam checker 1245/1245 PASS; tsc temiz; vitest 102/102 PASS.
- `python tools/phase_gate.py F10` → GATE PASS.
