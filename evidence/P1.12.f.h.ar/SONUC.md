# P1.12.f.h.ar — Durable CORE01 replay receipt append/load

## Sonuç

Durum: IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY

Greenfield Futures DCA journal schema revision 4 içine
core_replay_receipts owner tablosu eklendi. Eski schema veya başarısız
migration runtime’a alınmadı; yeni schema yalnız yeni journal oluştururken
kullanılır. Receipt Store:

- accepted event, economic posting, release transition ve son reservation
  projection linklerini doğrular;
- aynı fingerprint ve aynı scope için DUPLICATE döndürür;
- fingerprint veya identity scope çakışmasında fail-closed CONFLICT verir;
- restart sonrasında receipt satırlarını exact dataclass olarak yükler ve
  bağlantıları tekrar doğrular;
- yalnız mevcut journal kaynaklarına append eder; venue, Binance veya canlı
  emir/mutation açmaz.

Receipt append işlemi bu fazda mevcut event/release/posting kayıtlarından
sonra ayrı transaction’dır. Receipt ile ekonomik event/release/posting’in tek
transaction’da birlikte yazılması sonraki atomik binding fazıdır ve henüz
tamamlanmış sayılmaz.

## Kanıt

- Odak: 16/16 PASS
- İlişkili Futures DCA kümesi: 46/46 PASS
- Tam proje: 602/602 PASS
- Compile/workspace: PASS
- Aktif Python dosyası: 235
- git diff --check: mevcut LF/CRLF dönüşüm uyarıları dışında hata yok

Odak komutu:

    $env:PYTHONPATH="$PWD\src"
    uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_core_replay_store tests.test_futures_dca_journal_schema

İlişkili küme ve tam suite tools/run_checks.py ile çalıştırıldı; tam suite
yükseltilmiş yetkiyle Windows Credential Manager sınırını aşarak doğrulandı.

## Sonraki tek mikro-faz

P1.12.f.h.as: receipt + event + release transition + economic posting
bağını tek transaction’da kuran atomik append/restart ve rollback kapısı.
Bu kapanmadan durable receipt Store ekonomik binding authority’si ilan
edilmeyecek.
