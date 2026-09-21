# Faz 14 kanıt — SONUC.md (ileri backtest + sinyal kalite, 2026-09-21)

## 14.1 istatistik kararı (KAPALI)
float64 izole `analytics/` (stdlib-only, numpy/scipy yok); AST sınır testi:
ledger katmanları analytics import edemez (2 köprü modülü allowlist'li).

## 14.2 embargo
`embargo_after` (test sonu → +µs, çağrıcı seçer) + `drop_embargoed`
(half-open çakışan train düşer, dokunan korunur). Purge kararı reuse.

## 14.3 CPCV
N grup + C(N,k) kombinasyon + purge (etiket↔test-özellik) + embargo +
phi path rekonstrüksiyonu (her path tüm grupları 1 kez kapsar) + path Sharpe.

## 14.4 PBO/DSR
PBO/CSCV (registry salt-okunur, yalnız SUCCEEDED; el-hesaplı 0.0/1.0
vakaları) + DSR skorlayıcı. TrialRecord'a opsiyonel `parameter_hash`.

## 14.5 sweep orkestratörü
Reducer aynen korunur; max_workers=1 sıralı, >1 ProcessPool + worker-init
bar-cache (tek yazma). Paralel==sıralı kanıtlandı (Windows spawn OK).

## 14.6 sampler
Sampler yalnız önerir, registry kaydeder. Random (seed'li) + Grid
yerleşik; Optuna ask-tell adaptörü opsiyonel import (yoksa açık hata).

- Tam checker 1414/1414 PASS (F14 payı +68, 1 skip=optuna-yok yolu).
- `python tools/phase_gate.py F14` → GATE PASS.
