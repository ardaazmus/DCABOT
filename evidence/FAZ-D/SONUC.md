# BÜYÜK FAZ D kanıt — Anti-Liquidation Cascade (okuma + gösterim)

## Kapsam (FAZ16 harita §8.6)
- D.1 (Claude): fapi v3 position-risk/account okuyucu + fail-closed
  durum makinesi (6 durum, DELEVERAGING saklı) + ayrı rate bütçesi
  + exact hız bayrağı + capability satırı. 36 test.
- D.1-followup (Claude): `select_position_row` (exact sıfır-filtre,
  hedge-çift-bacak reddi). 6 test.
- D.2 (muse): okuma servisi (SIMULATED_ONLY/STALE-cache/typed hata)
  + `GET /api/risk/liquidation-status/{symbol}` + BotDetailView
  bölümü (8.3'ün 4 maddesi birebir). 28 test (16+5+7).
- D.3: **BLOCKED kaldı** — RG-02 koşulu (b) (WS hybrid:
  ACCOUNT_UPDATE + mark-stream) yok; roadmap kuralı gereği D.1/D.2
  yine de teslim edildi. Unblock: WS invalidation + Arda onayı.

## Doğrulama (2026-09-22)
- `uv run --frozen python tools/run_checks.py` → **1584/1584 PASS**
  (skip=1; D.1 +36, followup +6, D.2 +21).
- `npx tsc -b` temiz; `npx vitest run` → **320/320** (D.2 +7);
  `npm run build` temiz.
- Fail-closed (SIMULATED_ONLY boş + STALE/INCONSISTENT) test edildi.
- Gözlem: güncel kodda 95 route (endpoint dahil); canlı :8000
  B.3-öncesi (404 — beklenen, dokunulmadı).

## Kapıda Arda'ya bağlı işler
- Canlı `positionRisk` UI doğrulaması (futures testnet credential +
  pozisyonlu hesap gerekli — repo'da yok).
- Hız eşiği kalibrasyonu (geçici "50", BTC-ölçeği).

## Kapanış
- Claude bağımsız teyit etti (1584/1584 + tsc + 320/320 + build +
  servis/UI/D.3-gerekçe incelemesi).
- **BÜYÜK FAZ D Arda onayıyla KAPANDI (2026-09-22, ek not yok).**
