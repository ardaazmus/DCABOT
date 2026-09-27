# BÜYÜK FAZ C kanıt — Direction/Short-Bidirectional'ın tamamlanması

## Kapsam (FAZ16 harita §8.6, 5/5 dilim kapalı)
- C.1 (Claude): `Config.direction` (varsayılan LONG, geriye uyumlu —
  eski config/hash değişmedi); SHORT+NET_QUOTE fail-closed ret.
- C.2 (Claude): `build_plan` SHORT ladder (mevcut
  `directional_safety_price`, yeni fiyat matematiği yok).
- C.3 (Claude): `engine.py` yön-farkındalığı (side seçimi, FILL'de
  `signed_pnl`, `target()`/`decision()` yön-trig'leri) + yeni
  `is_take_profit_triggered` primitifi. LONG regresyon-sıfır.
- C.4 (muse): `data_adapters/capabilities.py` — 2 satırlı matris
  (`binance_spot/public` emirsiz, `binance_spot/testnet` LONG-only)
  + fail-closed `supports()`; tüketim yok (C.5/P4 ayrı).
- C.5 (muse): concurrency KARARI — şimdilik kapalı (C.4'te SHORT
  destekleyen venue yok; açılması P4 + koordinasyon tasarımı ister).

## Doğrulama (2026-09-22)
- Yön testleri: `test_directional_math` + `test_config_direction` +
  `test_engine_direction` + `test_adapter_capabilities` → **44/44**.
- `uv run --frozen python tools/run_checks.py` → **1521/1521 PASS**
  (skip=1; C.1-C.3'ten +22, C.4'ten +8).
- `npx tsc -b` temiz; `npx vitest run` → **313/313** (frontend
  değişmedi); `npm run build` temiz.
- Gözlem: canlı :8000 bots 200 (örnek B.3-öncesi, dokunulmadı).

## Bilinçli kapsam-dışı (gelecek iş)
- `historical_simulation.py` long-only (`_buy/_sell_reachable`).
- SHORT+NET_QUOTE ekonomik tasarımı (şu an ret).
- C.5'in açılması (marjin/vadeli venue + iki-State koordinasyonu).

## Kapanış
- Claude bağımsız teyit etti (1521/1521 + tsc + 313/313 + C.4/C.5
  incelemesi).
- **BÜYÜK FAZ C Arda onayıyla KAPANDI (2026-09-22, ek not yok).**
