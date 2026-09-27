# BÜYÜK FAZ F kanıt — Regime Detection + Correlation-Aware Risk

## Kapsam (FAZ16 harita §8.6, 2/2 dilim kapalı)
- F.1 (Claude + muse teyit): `regime_detection.py` — ADX/+DI/−DI
  exact Fraction (Wilder recursive + `bounded()`); BBW
  `analytics/regime_scores.py`'de izole (tek köprü allowlist'te);
  5 durum, squeeze-önce, TREND yalnız ADX+DI-ayrımı; confidence
  deterministik Fraction. Öneri-only, tüketici yok.
- F.2 (Claude + muse teyit): `correlation_risk.py` — karar
  integer-only (çapraz-çarpım, bölme bile yok); log-return;
  çok-pencere + taban (en muhafazakâr); PSD sanity; fail-closed
  DENY (HISTORY/PRECISION/BREACH); `account_reservation`'a
  yalnızca yeni-deal ön-kapısı (`project_reservation` değişmedi).

## Doğrulama (2026-09-22)
- F testleri: 45/45 (14+9+8+14); `test_analytics_boundary` PASS.
- `uv run --frozen python tools/run_checks.py` → **1681/1681 PASS**
  (skip=1).
- `npx tsc -b` temiz; `npx vitest run` → **324/324** (frontend
  değişmedi); `npm run build` temiz.
- M/F/B çelişki kontrolü (muse): ADX exact ✓, BBW izole ✓,
  squeeze-önce ✓, DI-ayrımı ✓, confidence deterministik ✓,
  integer-karar ✓, PSD ✓, fail-closed DENY/ALLOW ✓, otomatik
  geçiş yok ✓ (üretim çağıranı yok), geriye dönük SO/TP yok ✓.
- Float sızıntı incelemesi (muse): boundary allowlist'te yalnız 2
  yeni köprü; `application/` karar dosyalarında float/`**0.5`/
  sqrt yok (grep: docstring + köprü-dönüşümleri hariç temiz);
  `analytics/` dışa yalnız skor verir, ledger'a yazmaz.

## Bilinçli kapsam-dışı (gelecek iş)
- ADX eşik kalibrasyonu (20/25 kanıtlanmamış konvansiyon).
- Backtest-doğrulama altyapısı (walk-forward/PBO, ayrı onay).
- Rejim/korelasyon UI bağlama (ayrı dilim).

## Kapanış
- Claude bağımsız teyit etti (1681/1681 + tsc + sqrt-grep +
  allowlist + SONUC incelemesi).
- **BÜYÜK FAZ F Arda onayıyla KAPANDI (2026-09-22, ek not yok).**
