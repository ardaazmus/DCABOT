# P1.12.f.h.at — Read-only CORE01 replay projection oracle

## Sonuç

Durum: IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY

Restart oracle, durable journal’daki accepted event, economic posting, release
transition ve replay receipt satırlarını read-only loader’larla doğruluyor.
Aynı girişlerle pure CORE01 replay decision/projection yeniden hesaplanıyor;
durable receipt fingerprint ve scope bu kararın ürettiği receipt ile eşleşirse
READY dönüyor. Receipt eksikse veya CORE01 admission stale ise fail-closed
BLOCKED dönüyor. Oracle hiçbir state, journal, receipt veya venue kaydı
yazmıyor.

Bu kanıt, CORE01 projection’ın restart sonrası aynı immutable girdilerden tekrar
üretilebildiğini gösterir; henüz CORE01 state’in durable owner’ı veya canlı
Binance ekonomik authority’si değildir.

## Kanıt

- Odak: 12/12 PASS
- İlişkili Futures DCA kümesi: 52/52 PASS
- Tam proje: 608/608 PASS
- Compile/workspace: PASS
- Aktif Python dosyası: 238
- git diff --check: mevcut LF/CRLF dönüşüm uyarıları dışında hata yok

Odak komutu:

    $env:PYTHONPATH="$PWD\src"
    uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_core_replay_oracle tests.test_futures_dca_core_replay_atomic tests.test_futures_dca_core_replay_store

İlişkili küme ve tam suite tools/run_checks.py ile çalıştırıldı; tam suite
yükseltilmiş yetkiyle Windows Credential Manager sınırını aşarak doğrulandı.

## Sonraki tek mikro-faz

P1.12.f.h.au: read-only oracle’ın durable reservation/posting/release
projection checksum ve duplicate/conflict sınırlarını genişletmek. Bu kapıda
CORE01 Store mutation, venue mutation ve canlı Binance emri açılmayacak.
