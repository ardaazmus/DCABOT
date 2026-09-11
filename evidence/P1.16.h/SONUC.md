# P1.16.h — Bounded real-run lineage binding karar kapısı

## Karar

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod değişikliği: sınırlı ve non-economic binding/persistence/API desteği uygulandı
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.i` stress ekonomik modeli ve gerçek senaryo runner karar kapısı

## Mevcut local durum

P1.06 tarihsel run capture/store zinciri kendi kapsamı içinde dataset artifact/canonical input, config hash, model/profile/version, simulator, kernel, seed policy, instrument-risk snapshot ve result identity alanlarını taşımaktadır. Save/retry sırasında source execution identity ve result/execution identity karşılaştırması yapılmakta; immutable record ve checksum korunmaktadır.

P1.16.h ile bu sınır kontrollü biçimde kapatıldı: `EvaluationRunBinding`, capture’ın mevcut run/result/input/config hash’lerini aynı canonical nesnede kayıtlı `TrialStudy`/`TrialRecord`, OOS lineage ve isteğe bağlı stress lineage ile birleştiriyor. Binding yalnız önceden kayıtlı trial kabul ediyor; stress varsa base result hash’i capture sonucu ile eşleşmek zorunda.

## Uygulanan minimum dikey dilim

- `src/dcabot/application/evaluation_run_binding.py`: mevcut capture kimliğini değiştirmeden trial/OOS/stress lineage için immutable, deterministic, secret-free binding üretir ve capture’a canonical JSON olarak ekler.
- `src/dcabot/application/historical_run_contract.py`: binding alanları capture’ın sonuna optional eklendi; binding olmadan eski P1.06 kayıtları geçerliliğini korur.
- `src/dcabot/persistence/historical_runs.py`: optional `evaluation_lineage` aynı immutable record checksum’ı içinde saklanır ve reopen sonrası doğrulanmış biçimde döner. Aynı source execution + aynı binding idempotenttir; aynı source execution + farklı binding `SOURCE_EXECUTION_CONFLICT` ile reddedilir; overwrite yoktur.
- `src/dcabot/server/api.py`: detail endpoint’i `evaluation_lineage` alanını güvenlik taramasından geçirerek salt-okunur biçimde expose eder. Liste görünümü değiştirilmedi.

Bu dilim optimizer, score/KPI, stress ekonomik sonucu, purge/embargo, feature/label pipeline veya yeni emir/fill authority eklemez.

## Açık kapsam

Bu fazın kanıtlanan kapsamı metadata lineage binding’idir. `TrialStudy`/`TrialRecord` hâlâ in-memory registry’dir; binding onu run kaydına bağlar fakat parametre snapshot’ı, score veya winner selection üretmez. Stress identity persist edilir ancak stress sonucu hesaplanmaz. Exact purge/embargo numeric policy, feature/label/warmup pipeline, economic stress runner, reproduction/compare, bağımsız review ve production readiness hâlâ açıktır.

## Kontroller

- Test-first RED: binding persistence testi, store henüz lineage’ı karşılaştırmadığı için aynı source execution’da farklı binding’i kabul etti.
- GREEN: `uv run --frozen python tools/run_checks.py` → `325/325 PASS`.
- Bağımsız canonical kontrol: üretim binding modülü import edilmeden stdlib `json` + `hashlib` ile sabit payload hash’i `bb7258345de45cffa780ed256f16f3690082feaba9040a992d85c5c3f6ebeac0` olarak doğrulandı; trial ID değişince hash değişti.
- `uv run --frozen python -m compileall -q src tests` → `PASS`.
- `uv run --frozen python tools/check_workspace.py` → `PASS`; `138` aktif Python dosyası.
- Eski binding’siz kayıt reopen davranışı mevcut testlerle korundu; yeni binding’li kayıt close/reopen sonrası aynı lineage ile doğrulandı.
- Hash’i geçerli olsa bile sözleşme dışı `secret` alanı içeren binding store tarafından `RUN_CAPTURE_INVALID` ile reddedildi.
- Live/testnet, credential, optimizer, ekonomik stress, yeni migration ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` dataset/config/model/kernel/seed identity, deterministic replay, OOS lineage ve stress’in ayrı result lineage’ını birlikte ister. Mevcut P1.06 store artık P1.16 metadata binding’ini optional ve geriye uyumlu biçimde karşılıyor; ekonomik stress/purge/embargo ve gerçek evaluation pipeline şartları bu küçük dilimin dışında tutuldu.
