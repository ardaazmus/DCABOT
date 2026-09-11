# P1.06.b — Dedicated SQLite historical run store

## Kapsam

P1.06.a capture bileşenlerini mevcut CORE SQLite journal’dan ayrı, local-only ve versioned bir historical run store’a yazıp yeniden açma backend dilimi uygulandı. Bu dilimde HTTP endpoint, frontend ekranı, reproduction, compare ve delete yoktur.

## Uygulanan sözleşme

`src/dcabot/persistence/historical_runs.py`:

- Ayrı SQLite application id ve `historical-run-snapshot-v1` store metadata’sı kullanır.
- Mevcut veya backup/link edilmiş path’i benimsemez; foreign SQLite dosyası desteklenmiyor olarak reddedilir.
- Rollback journal ve `synchronous=FULL` kullanır; WAL açmaz.
- Schema v1 içinde `historical_runs` kayıtları tek `BEGIN IMMEDIATE` transaction ile immutable insert edilir.
- Server-side UUIDv4 `run_id` ve internal bounded `source_execution_id` kullanır.
- Aynı source execution retry’ı mevcut run’ı döndürür; farklı payload silent overwrite yapmadan `SOURCE_EXECUTION_CONFLICT` üretir.
- Record JSON canonical hash ile doğrulanır. Tampered/truncated kayıt detail’de fail-closed olur; listede `CORRUPT` işaretiyle diğer valid kayıtlar gösterilmeye devam eder.
- Record içindeki metadata ile SQLite liste kolonları ayrı ayrı değiştirilse bile index/snapshot uyuşmazlığı `CORRUPT` olarak işaretlenir.
- Liste varsayılan 50, hard cap 100 kayıtla `created_at DESC, run_id DESC` deterministik sıralanır.
- Record byte bütçesi 4 MiB, list limit aralığı 1..100 ile sınırlandırılır.
- Stored result içindeki P1.05 `persisted=false` semantiği korunur; storage state envelope’dan ayrıdır.

## Doğrulama

1. RED: Store modülü yokken dört yeni storage testi import hatası verdi.
2. GREEN: Uygulama sonrası save/reopen, idempotent retry/conflict, corruption isolation ve foreign DB reddi testleri geçti.
3. Windows farklı kontrolü: Foreign SQLite test bağlantısı açık bırakıldığında dosya kilidi görüldü; bağlantı explicit `close()` ile düzeltildi ve test tekrar PASS oldu.
4. Tam regresyon: `uv run --frozen python tools/run_checks.py` → `100/100 PASS`.
5. Derleme: `uv run --frozen python -m compileall -q src tests` → PASS.
6. Workspace: `uv run --frozen python tools/check_workspace.py` → PASS; backup layout `EMPTY_OR_NOT_PLACED`.

## Açık sınırlar

Store henüz API’ye bağlanmadı; uygulama yeniden açma davranışı sınıf seviyesinde doğrulandı. API response/Problem Details, localhost mutation guard, UI save/list/detail, reproduction runtime benchmark ve compare gate sonraki ayrı mikro dilimlerdir. Otomatik backup ve delete eklenmedi.

## Durum

`P1.06.b: IMPLEMENTED / LOCAL_PASS; review: NOT_RUN.` P1.06 genel fazı tamamlanmış sayılmaz.
