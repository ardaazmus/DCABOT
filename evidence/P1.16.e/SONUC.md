# P1.16.e — Stress lineage ve ayrı sonuç kimliği

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/stress_lineage.py`
- Test: `tests/test_stress_lineage.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.f` warmup leakage ve readiness binding karar kapısı

P1.16 araştırmasındaki stress sonucunun normal backtest sonucu gibi sunulmaması ve base result’ın üzerine yazılmaması kuralının en küçük saf sınırı uygulandı. Stress lineage; base result identity, stress profile identity ve profile hash’i birlikte taşır. Aynı girdiler deterministik ayrı bir `stress_result_id` üretir; etiket sabit olarak `STRESS` kalır.

## Uygulanan sözleşme

- `StressLineage` immutable’dır ve ekonomik sonuç, KPI, PnL veya stress hesaplamaz.
- `stress_profile_hash` yalnız 64 karakterlik lowercase hexadecimal SHA-256 kimlik olarak kabul edilir; profil içeriğinin canonical serialization’ı bu mikro-fazda tanımlanmadı.
- Stress sonucu `stress-v1:<digest>` biçiminde ayrı identity alır; base result identity’si overwrite edilemez.
- Aynı base/profile/hash girdisi aynı sonucu, farklı stress profile girdisi farklı sonucu üretir.
- Boş/geçersiz kimlikler, geçersiz profile hash’i ve base/stress identity çakışması fail-closed reddedilir.

## Bilinçli kapsam dışı

Spread, slippage, latency, volume participation, partial fill, OHLC best/worst path, missing-gap repair, seed/RNG, ekonomik stress sonucu, normal run persistence, dataset/config/model/kernel binding, API/UI ve optimizer bu mikro-fazda açılmadı. Purge/embargo sayısı local feature/label/event horizon görülmeden seçilmedi.

## Kontroller

- Önce test RED: yeni `stress_lineage` modülü eksik olduğu için beklenen import error alındı.
- Minimal uygulama sonrası `uv run --frozen python tools/run_checks.py`: `318/318 PASS`.
- Bağımsız production-importsuz kimlik kontrolü: `INDEPENDENT_STRESS_LINEAGE_CONTROL_PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `136` aktif Python dosyası.
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` stress’in normal backtest’ten ayrı lineage taşımasını ve base-run identity + stress-profile hash kullanılmasını ister. Bu teslim yalnız identity/lineage ayrımını kapatır; stress ekonomik modeli veya performans iddiası içermez.
