# BÜYÜK FAZ B kanıt — Araştırma gerektirmeyen Faz 17 kalemleri

## Kapsam (FAZ16 harita §8.6)
- B.1 (=17.1, Claude): `volatility_adaptive_dca.py` — TR/ATR (Wilder,
  exact) + `dynamic_deviation`; `build_plan` sözleşmesi değişmedi.
- B.2 (=17.6, muse): sweep/optimize "AI Önerici" adıyla görünür +
  dürüst motor altbilgisi + rozetler; davranış değişikliği yok.
- B.3 (=17.8, muse): `canary_status.py` gerçek girdilerle karar +
  GET /api/risk/canary + POST /api/risk/kill-switch + RiskPanel bölümü.
- B.4-ui (=17.10, muse): preset galeri kartları + karşılaştırma
  dataset/config-hash güvenlikleri. **B.4-motor Claude'da OPEN.**
- B.5 (=17.11, muse + Claude doğrulama): What-If otomatik çalıştırma
  (`useWhatIfAutoRun`, 800ms debounce, plan-anahtarı başına tek atış).
- B.6 (=17.9 iskelet, muse): `data_adapters/README.md` port-desen
  sözleşmesi (3 aile/13 modül, seam'ler, yeni-venue tarifi). Kod yok.
- B.7 (=17.19 iskelet, muse): `strategies/custom/CONTRACT.md` —
  `decision(State, Config)` taslak imza + saflık kısıtları. Kod
  bağlanmadı (.py sıfır), BLOCKED kalır.

## Doğrulama (muse, 2026-09-22)
- `uv run --frozen python tools/run_checks.py` → **1486/1486 PASS**
  (skip=1).
- `npx tsc -b` temiz; `npx vitest run` → **313/313 PASS** (B.2: 4,
  B.3: 5, B.4-ui: 5, B.5: 10; +13 B.1 checker testi).
- `npm run build` temiz (dist üretildi).
- Gözlem: güncel kodda 94 route (canary/kill-switch dahil); çalışan
  :8000 örneği B.3-öncesi (bots/dashboard 200, canary 404 — beklenen);
  yeni örnek single-worker kilidiyle doğru şekilde reddedildi,
  kullanıcının sunucusuna dokunulmadı.

## Kapanış
- B.4-motor (Claude): `preset_comparison.py` — iki binding'i aynı
  datasette materialize+simulate edip yan yana sonuç; 5 yeni test.
- Checker 1491/1491 (skip=1) güncel ağaçta teyit edildi.
- **BÜYÜK FAZ B Arda onayıyla KAPANDI (2026-09-22).**
