# P1.06.d — Bounded historical run list/detail read API

## Kapsam

P1.06.b dedicated immutable SQLite store ve P1.06.c save API üzerine yalnız salt-okunur list/detail/reopen API’si eklendi. UI, reproduction, compare, delete ve backup bu dilime alınmadı.

## Uygulanan sözleşme

- `GET /api/historical-runs` store mevcutsa deterministic `created_at DESC, run_id DESC` sırasını koruyan bounded liste döndürür.
- Liste `limit` query parametresini 1..100 aralığında kabul eder; default 50’dir.
- Store dosyası yoksa liste boş döner ve salt-okunur isteğin yan etkisi olarak DB oluşturulmaz.
- Liste `OK` veya `CORRUPT` record health bilgisini taşır; store’un corrupt kayıt izolasyonu API’ye yansır.
- `GET /api/historical-runs/{run_id}` canonical UUID biçimini doğrular, immutable detail’i yeniden açar ve `Cache-Control: no-store` kullanır.
- Eksik run `404 RUN_NOT_FOUND`, invalid ID `422 RUN_ID_INVALID`, bütünlük sorunu `409 RUN_CORRUPT` olarak güvenli Problem Details döndürür.
- Detail response’taki snapshot nesnelerinde path/url/secret/credential/token/password/private-key benzeri anahtarlar bulunursa `409 RUN_DETAIL_UNSAFE` ile fail-closed davranır.
- Serialized detail response 256 KiB’yi aşarsa `422 RUN_DETAIL_RESPONSE_TOO_LARGE` döner.
- Store tarafında checksum geçerli olsa bile eksik veya yanlış tipte nested record alanları exception olarak yayılmaz; listede `CORRUPT`, detail’de `RUN_CORRUPT` olur.

## Doğrulama sırası

1. RED: Yeni list/detail testleri endpoint fonksiyonları yokken `AttributeError` ile beklenen kırılmayı üretti.
2. GREEN: Liste, detail, missing-store, response-byte, forbidden-key ve invalid nested record kontrolleri geçti.
3. Farklı kontrol: Store yeniden açılarak immutable detail okundu; `persisted=false` ve path/url yokluğu korundu.
4. Python regresyon: `uv run --frozen python tools/run_checks.py` → `109/109 PASS`.
5. Derleme: `uv run --frozen python -m compileall -q src tests` → PASS.
6. Workspace: `uv run --frozen python tools/check_workspace.py` → PASS; `active_python_files=50`, backup layout `EMPTY_OR_NOT_PLACED`.
7. Önceki frontend kapısı korunarak `npm run build` (`frontend`) → TypeScript ve Vite build PASS.

## Dosyalar

- `src/dcabot/server/api.py`
- `src/dcabot/persistence/historical_runs.py`
- `tests/api/test_historical_run_reads.py`
- `tests/data/test_historical_run_store.py`
- `README.md`
- `docs/VERI_VE_SIMULASYON.md`
- `docs/MIMARI.md`
- `docs/OZELLIK_MATRISI.md`

## Durum

`P1.06.d: IMPLEMENTED / LOCAL_PASS; review: NOT_RUN.` P1.06 genel fazı tamamlanmış sayılmaz. Sıradaki tek iş P1.06.e saved-run UI araştırma kapısıdır.
