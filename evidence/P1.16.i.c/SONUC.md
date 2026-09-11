# P1.16.i.c — Deterministic scenario/result identity audit

## Karar

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Ekonomik scenario identity durumu: `DEFERRED / NO-GO`
- Kod değişikliği: yok
- Sonraki tek iş: `P1.16.i.d` persistence/replay/recovery karar kapısı
- Production readiness: `NO`

Bu alt faz mevcut metadata identity’sinin deterministik ve base/stress ayrımını koruduğunu doğruladı. Ancak ekonomik scenario sonucu henüz bulunmadığı için rapordaki geniş `dataset/config/model/kernel/seed/scenario` kimliği production economic result identity olarak uygulanmadı.

## Yerel authority karşılaştırması

| Kimlik | Mevcut kapsam | Kanıtlanan sınırlama |
|---|---|---|
| `HistoricalRunExecutionIdentity` | canonical input hash, artifact hash, config hash, model/profile sürümleri, kernel version, instrument risk snapshot, seed policy | `SEED_POLICY=NOT_APPLICABLE`; stochastic seed ve economic scenario id yok |
| Historical result capture | result JSON/hash, execution identity JSON/hash, canonical input/config ve bounded snapshot | Ekonomik stress sonucu değil; mevcut base historical capture |
| `StressLineage` | `base_result_id`, `stress_profile_id`, `stress_profile_hash`, türetilmiş `stress_result_id`, sabit `STRESS` etiketi | Scenario branch, bar/order kapsamı ve seed bileşeni yok; metadata identity’sidir |
| `EvaluationRunBinding` | run/result/input/config hash, study/trial/OOS ve optional stress profile/result bağları | Stress economics veya scenario event identity üretmez |
| Canonical serialization | recursive sorted-key JSON, ASCII, compact separators, `allow_nan=False`, float rejection | Tam RFC 8785/JCS uyumluluğu iddia edilmedi; Decimal/number string policy ayrı bir karardır |

## Bağımsız kontrol

Production identity fonksiyonu çağrılmadan mevcut `StressLineage` formülü yeniden hesaplandı:

```text
canonical = stress-lineage-v1|result-base-1|ohlc-worst-1|cccc...(64 hex)
expected = stress-v1:a6cfd2b477dec40af9687964d5e5797ac01261ed22d700a4d50a235877617a2d
changed_profile_identity_differs = True
dataset_config_model_kernel_seed_scenario_in_current_identity = False
```

Odak test: `9/9 PASS` (`test_stress_lineage`, `test_evaluation_run_binding`). Tam regresyon baz çizgisi: `325/325 PASS`.

Kontrol sonucu:

- Aynı base result + aynı profile id/hash aynı stress identity’yi üretir.
- Profile id/hash değişince stress identity değişir.
- Stress identity base result identity’sini kullanamaz.
- `EvaluationRunBinding` stress lineage’ı mevcut capture sonucu ile eşleşmezse reddeder.
- Mevcut identity’de `scenario_id` ve stochastic `seed` alanı yoktur; raporun T-12 çelişkisi bu nedenle çözülmüş sayılmaz.

## Raporla doğrulanan ve ayrılan noktalar

1. Raporun “base result stress sonucu üzerine yazmamalı” kararı mevcut separate stress lineage ile uyumludur.
2. Raporun T-12 kuralı çelişkilidir: seed hash’e dahil edilecek denirken deterministic modelde seed’in `null` ve hash dışında olması gerektiği de yazılmıştır. Bu iki davranış aynı contract olarak uygulanamaz.
3. RFC 8785 kaynaklı canonical JSON yaklaşımı property sorting ve I-JSON/ECMAScript serialization bağlamındadır; yüksek hassasiyetli finansal değerleri string olarak taşıma kararı yine uygulama contract’ıdır. Mevcut `canonical_json` bu nedenle doğrudan JCS olarak etiketlenmemiştir.
4. `kernel_hash` byte/source hash’inin seçimi raporda açık bırakılmıştır. Mevcut project `kernel_version` kullanır; source byte hash’e sessiz geçiş yapılmadı.

## Uygulama kararı

| Davranış | Karar |
|---|---|
| Mevcut stress lineage determinism’i | `ACCEPT` — olduğu gibi korunur |
| Base/stress identity ayrımı | `ACCEPT` — P1.16.e/h sınırı korunur |
| Scenario branch identity | `DEFERRED` — economic branch authority yok |
| Seed/RNG | `DEFERRED` — stochastic model yok; mevcut `NOT_APPLICABLE` korunur |
| Tam JCS migration | `DEFERRED` — mevcut canonical contract ve testleri değiştirecek ayrı karar gerekir |
| Dataset/config/model/kernel/stress identity genişletmesi | `DEFERRED` — i.b economic contract ve i.d persistence ile birlikte ele alınmalı |
| Overwrite/dedup/conflict | Mevcut stress/base sınırları korunur; yeni economic result yazımı yok |

## Kapanış kontrolleri

- Odak identity/binding testleri: `9/9 PASS`.
- Önceki tam regresyon baz çizgisi: `325/325 PASS`.
- Workspace: `PASS`; `138` aktif Python dosyası.
- Kod değişikliği: yok; kanıt yalnız mevcut davranış ve bağımsız kontrol üzerine kuruldu.
- Production readiness: `NO`.

## Sonraki geçiş

`P1.16.i.c` tamamlandı-with-limitation. Mevcut metadata identity güvenli biçimde korunuyor; ekonomik scenario identity, seed ve branch sonucu hâlâ uygulanabilir contract değildir. Sıradaki tek iş `P1.16.i.d` içinde mevcut Store/historical run persistence sınırlarını stress event, branch isolation, atomic commit, replay ve recovery iddialarıyla denetlemektir. Economic runner veya public API/UI açılmayacaktır.
