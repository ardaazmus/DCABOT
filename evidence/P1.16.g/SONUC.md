# P1.16.g — Local feature/label horizon ve gerçek run binding

## Karar

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod değişikliği: yapıldı; yalnız yerel, deterministik ve salt-okunur historical pipeline
- Odak red/green kontrat kontrolü: `PASS_WITH_LIMITATION`
- Ayrı bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.i` stress ekonomik modeli ve gerçek senaryo runner karar kapısı

## Uygulanan minimum dikey dilim

`src/dcabot/application/historical_features.py` içinde bounded ve fail-closed bir
feature/label pipeline eklendi. Pipeline yalnız şu açık kimlikleri kabul eder:

- `CLOSE_SMA`: kapanışların exact `Fraction` ortalaması; lookback zorunludur.
- `CLOSE_RETURN`: kapanıştan kapanışa exact getiri; lookback zorunludur.
- `FUTURE_CLOSE_RETURN`: yalnız gelecekteki kapanıştan hesaplanan label; horizon zorunludur.

Pipeline yalnız canonical closed OHLCV barlarını kabul eder; chronology, fiyat
pozitifliği, bounded bar/lookback/horizon ve exact feature/label kimlikleri
fail-closed doğrulanır. Feature değerleri float veya UI `Number` değildir; dışa
canonical ratio metniyle (`numerator/denominator`) taşınır. Bu değerler ekonomik
posting veya emir authority’sine bağlanmaz.

`src/dcabot/application/historical.py` feature binding’i run planına bağlar.
`src/dcabot/application/historical_simulation.py` binding’i reducer başlamadan
önce yeniden hesaplayıp doğrular; warmup barlarında action üretilmez ve ekonomik
runner ilk eligible bar indeksinden başlar. `historical_run_contract.py` capture
identity’sine binding checksum’ını ve bounded pipeline metadata’sını ekler.
Dataset id, artifact SHA-256, config hash, pipeline id, feature/label tanımı,
warmup, horizon, eligible aralık ve deterministic row binding birlikte korunur.

## Kanıtlanan sınırlar

- Warmup: `max(feature lookback) - 1`; ilk eligible bar bu sınırdan sonradır.
- Label: yalnız gelecekteki bar kapanışından; mevcut/geçmiş bar sızıntısı yoktur.
- Runner: binding değişirse reducer çalışmadan `HistoricalSimulationError` verir.
- Capture: binding checksum’ı run identity’ye dahil edilir; farklı pipeline/row
  binding’i aynı historical run kimliği gibi kabul edilmez.
- Limitler: en fazla `1000` bar, `500` lookback ve `500` label horizon.

Bu dilim exact numeric purge/embargo, ekonomik KPI/OOS kararları, optimizer,
stress model, persistence schema, API/UI opt-in profili veya canlı venue
davranışı seçmez. P1.16.i bu sınırları ayrı karar kapısı olarak taşır.

## Kontroller

- `tests.test_historical_features`: `4/4 PASS`
- `tests.test_evaluation_run_binding`: `6/6 PASS`
- historical API regression set: `26/26 PASS`
- `uv run --frozen --python 3.13 python -m compileall -q src tests`: `PASS`
- `uv run --frozen --python 3.13 python tools/check_workspace.py`: `PASS`
  (`288` active Python files)
- `git diff --check`: `PASS` (yalnız mevcut CRLF dönüşüm uyarıları)
- `uv run --frozen --python 3.13 python tools/run_checks.py`: `786/788 PASS`;
  kalan iki hata Windows Credential Manager ortam kapısıdır: credential write
  error `1312` ve cleanup sırasında `CREDENTIAL_NOT_FOUND`. Bunlar P1.16.g
  kaynak/feature/runner testleri değildir ve bu ortamda credential provider
  kurulumu olmadan yeniden üretildi.

## Güvenlik ve kapsam dışı

Testnet/live credential, signed request, order mutation, mainnet, public API
aktivasyonu, feature row persistence, optimizer veya ekonomik fill authority’si
açılmadı. Historical pipeline salt-okunur ve offline’dır; üretim veya trading
readiness iddiası değildir.

## Kaynak ve izlenebilirlik

- Uygulama: `src/dcabot/application/historical_features.py`
- Run planı: `src/dcabot/application/historical.py`
- Historical runner: `src/dcabot/application/historical_simulation.py`
- Capture identity: `src/dcabot/application/historical_run_contract.py`
- Odak testleri: `tests/test_historical_features.py`,
  `tests/test_evaluation_run_binding.py`
- Araştırma dayanağı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`
