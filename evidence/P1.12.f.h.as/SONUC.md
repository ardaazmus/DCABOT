# P1.12.f.h.as — Atomic CORE01 replay receipt binding

## Sonuç

Durum: IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY

Futures DCA accepted fill event’i, release transition, economic posting ve
CORE01 replay receipt tek SQLite transaction’ında bağlandı. Dört kayıt da
birlikte ACCEPTED veya birlikte DUPLICATE olur. Receipt scope uyuşmazlığı ve
receipt insert hatası transaction’ı fail-closed rollback’a götürür; event,
release history, reservation projection ve economic posting kısmi kalmaz.
Restart sonrasında receipt bağlantıları tekrar exact olarak yüklenir.

Bu faz yalnız greenfield offline journal içindir. Binance/Testnet venue
mutation, mainnet, secret ve eski proje migration/publish açılmadı. CORE01
ekonomik authority’si için sonraki kanıt kapıları ayrıca korunur.

## Kanıt

- Odak: 25/25 PASS
- İlişkili Futures DCA kümesi: 49/49 PASS
- Tam proje: 605/605 PASS
- Compile/workspace: PASS
- Aktif Python dosyası: 236
- git diff --check: mevcut LF/CRLF dönüşüm uyarıları dışında hata yok

Odak komutu:

    $env:PYTHONPATH="$PWD\src"
    uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_core_replay_atomic tests.test_futures_dca_core_replay_store tests.test_futures_dca_release_posting_atomic tests.test_futures_dca_release_store tests.test_futures_dca_journal_schema

İlişkili küme ve tam suite tools/run_checks.py ile çalıştırıldı; tam suite
yükseltilmiş yetkiyle Windows Credential Manager sınırını aşarak doğrulandı.

## Sonraki tek mikro-faz

P1.12.f.h.at: atomik receipt binding’in CORE01 replay decision/projection
ile restart sonrası aynı ekonomik projection’ı üretip üretmediğine dair
read-only replay oracle kapısı. Yeni economic authority veya venue mutation
bu kapıda açılmayacak.
