# P1.04.d — Bounded tarihsel koşu doğrulaması

## Durum

- Faz: `COMPLETE / LOCAL_PASS`
- Bağımsız faz incelemesi: `NOT_RUN`
- Tarih: 2026-09-07
- Önceki araştırma girdisi: kullanıcı tarafından sağlanan anonim `deep-research-report(6).md`
- Sonraki tek faz: `P1.04.e`

## Kapsam kararı

Raporun önerdiği en küçük HTTP yüzeyi uygulandı. Bu faz yalnız mevcut salt-okunur run-plan bağlamının hâlâ güncel VERIFIED dataset artifact’ına ve aktif offline config revision’ına bağlı olduğunu doğrular. Rapor içindeki öneriler proje talimatı olarak değil, teknik araştırma girdisi olarak değerlendirildi; proje kapsamı, AGENTS/STATE/TASK ve mevcut kod sözleşmesi belirleyici kaldı.

Koşu başlatma UI’ı için görsel araştırma henüz yapılmadığından yeni başlatma butonu veya execution ekranı eklenmedi.

## Gerçekleşen davranış

- `POST /api/historical-runs/validate` yalnız `dataset_id`, `artifact_sha256`, `config_hash` ve `execution_mode="SIMULATED"` kabul eder.
- Request modeli strict’tir, bilinmeyen alanları reddeder ve SHA-256 revision alanlarını lowercase 64-hex sınırında tutar.
- Dataset yalnız explicit katalogdan resolve edilir; server güncel VERIFIED preflight/artifact kimliğini kendi okur.
- Artifact ve config revision uyuşmazlıkları güvenli `409` Problem Details ile reddedilir.
- Dataset/config sembol uyuşmazlığı, offline schema bağlamı ve server bar sınırı fail-closed korunur.
- Başarı yanıtı `READY`, `NOT_STARTED`, `read_only=true`, `offline=true` ve `SIMULATED` taşır.
- Response DTO yalnız allowlist edilmiş dataset/config özetlerini taşır; local path, URL, credential, raw config, job/run ID, seed veya ekonomik sonuç içermez.
- Endpoint run oluşturmaz, job başlatmaz, simülasyon çalıştırmaz, network kullanmaz, cache/DB/config yazmaz.
- Validation endpoint’i için 4 KiB raw body sınırı ve `Cache-Control: no-store` eklendi.

## Değişen dosyalar

- `src/dcabot/application/historical.py`
- `src/dcabot/server/api.py`
- `tests/api/test_dataset_preflight.py`
- `TASK.md`
- `STATE.md`
- `README.md`
- `docs/MIMARI.md`
- `docs/VERI_VE_SIMULASYON.md`
- `docs/OZELLIK_MATRISI.md`

## Test kanıtı

TDD akışında validation request/response ve stale revision davranışları için testler eklendi. Testler gerçek verified fixture üzerinden current artifact/config binding’ini, `NOT_STARTED` durumunu, güvenli response alanlarını, stale artifact reddini ve free-form config alanlarının reddini kontrol ediyor.

```text
& '.venv\Scripts\python.exe' tools\run_checks.py
Ran 75 tests in 0.465s
OK
```

Ek kapsam:

- `compileall -q src tools tests`: PASS
- `tools/check_workspace.py`: PASS
- Gerçek loopback HTTP smoke: `POST /api/historical-runs/validate` üzerinde 4 KiB üstü gövde `413 REQUEST_TOO_LARGE` döndürdü.
- Frontend build: bu fazda frontend değişmedi; yeni UI aksiyonu eklenmedi.
- Browser/IAB: bu fazda UI değişmedi; P1.04.c görsel kanıtı geçerli kaldı.

## Ertelenenler

- Historical simulation execution
- `run_id`, job/worker ve persistence
- Result/PnL/equity/işlem tablosu
- Client-defined date subset veya client-defined `max_bars`
- Durable idempotency
- Execution-time TOCTOU revalidation
- Koşu başlatma UI’ı; önce anonim görsel araştırma gerekli
