# P1.06.c — Explicit application/API historical run save

## Kapsam

P1.06.a canonical capture ve P1.06.b dedicated SQLite store, historical simulation sonucuna küçük bir application/API dikey dilimiyle bağlandı. Bu dilimde UI, run list/detail, reproduction, compare, delete ve backup yoktur.

## Uygulanan sözleşme

- `POST /api/historical-runs/simulate` terminal `COMPLETED` veya `INDETERMINATE` sonucunu güvenli capture olarak hazırlar.
- Capture yalnız process içindeki bounded ephemeral registry’de tutulur; registry hard cap’i 16 execution’dır.
- Simulation response’una server-side UUIDv4 biçiminde `execution_id` eklenir.
- `POST /api/historical-runs` request’i yalnız `execution_id` kabul eder; istemcinin result, config, dataset veya finansal snapshot göndermesine izin verilmez.
- Save, capture’ı dedicated `HistoricalRunStore`’a immutable olarak yazar. Yeni kayıt `201` ve `created=true` döner.
- Aynı execution tekrar kaydedilirse store idempotency ile aynı `run_id` döner; API `200` ve `created=false` döner.
- Bilinmeyen execution `404 EXECUTION_NOT_FOUND` döner ve store dosyası oluşturmadan kapanır.
- Save request native route katmanında 4 KiB ile sınırlıdır; aşım parser/validation öncesinde `413 REQUEST_TOO_LARGE` Problem Details olur.
- Stored result snapshot’taki `persisted=false` değişmez; `INDETERMINATE` status ve ambiguity bilgisi capture sözleşmesinden geçer.
- API response yalnız bounded metadata döndürür; result snapshot path/url taşımaz ve hata detayları yerel dosya yolu/stack bilgisi sızdırmaz.

## Doğrulama sırası

1. RED: Yeni API testleri, `execution_id`, save endpoint’i ve save body limit’i yokken beklenen kırılmaları üretti.
2. GREEN: API implementation sonrası save/idempotency, unknown execution ve request limit testleri geçti.
3. Farklı kontrol: Store yeniden açılarak kaydedilen snapshot’ın `persisted=false` değeri ve path/url yokluğu tekrar okuma üzerinden doğrulandı.
4. Python regresyon: `uv run --frozen python tools/run_checks.py` → `104/104 PASS`.
5. Derleme: `uv run --frozen python -m compileall -q src tests` → PASS.
6. Workspace: `uv run --frozen python tools/check_workspace.py` → PASS; `active_python_files=50`, backup layout `EMPTY_OR_NOT_PLACED`.
7. Frontend: `npm run build` (`frontend`) → TypeScript ve Vite build PASS.

## Dosyalar

- `src/dcabot/server/api.py`
- `tests/api/test_historical_simulation.py`
- `tests/api/test_request_limits.py`
- `README.md`
- `docs/VERI_VE_SIMULASYON.md`
- `docs/MIMARI.md`
- `docs/OZELLIK_MATRISI.md`

## Durum

`P1.06.c: IMPLEMENTED / LOCAL_PASS; review: NOT_RUN.` P1.06 genel fazı tamamlanmış sayılmaz. Sıradaki tek iş P1.06.d bounded list/detail API’sidir.
