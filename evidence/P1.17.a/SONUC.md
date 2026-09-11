# P1.17.a — Public read-only data authority inventory

## Karar

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Tarihsel public dataset/cache yolu: `ACCEPT / scope-limited`
- Public canlı fiyat adapter’ı: `NOT_PRESENT`
- Stale/reconnect canlı veri davranışı: `NOT_PROVEN`
- Live paper-trading ekonomik yolu: `DEFERRED / NO-GO`
- Kod değişikliği: yok
- Sonraki tek iş: `P1.17.b` public read-only feed contract research gate
- Production readiness: `NO`

Bu mikro faz yalnız mevcut yerel public veri authority’sini denetledi. Projede doğrulanmış bir historical public artifact indirme ve offline parse/cache zinciri vardır; fakat public canlı fiyat akışı, canlı bağlantı yaşam döngüsü veya canlı veriyi simulated emir akışına bağlayan adapter yoktur. Bu nedenle canlı davranış varsayımla eklenmedi.

## Yerel authority envanteri

| Katman | Mevcut gerçek | Karar |
|---|---|---|
| Public source registry | `PublicSourceSpec` host/path allowlist’i; mevcut kayıt Binance Spot günlük `BTCUSDT/1h` tarihsel ZIP planıdır | `PASS / historical-only` |
| Download plan | HTTPS, host/path, filename, SHA-256, byte ve ZIP iç dosya sınırları | `PASS` |
| Network download | `urllib` tabanlı bounded GET; redirect reddi, status/header/encoding kontrolü ve timeout var | `PASS / download-only` |
| Cache publication | Staging `.part`, fsync, doğrulama ve `os.replace`; doğrulanmamış ZIP yayınlanmıyor | `PASS / iki metadata dosyasının ortak transaction’ı değil` |
| Cache inspection | Network kullanmadan ZIP + metadata + hash + boyut + içerik bütünlüğü yeniden kontrol ediliyor | `PASS` |
| Dataset catalog | Yalnız explicit tanımlar listeleniyor; yalnız doğrulanmış local cache seçiliyor; URL/path response’a taşınmıyor | `PASS` |
| Historical parser | 12 alanlı kline şeması, exact decimal-string boundary, OHLC, closed bar, zaman sırası/çakışma ve bounded bar sayısı doğrulanıyor | `PASS` |
| Historical simulation input | 1h için contiguous open-time grid ve bar validity yeniden kontrol ediliyor; gap fail-closed | `PASS / historical-only` |
| Download job | In-memory queued/running/retrying/succeeded/failed/cancelled state, bounded retry ve cancel | `PASS / process restart recovery yok` |
| Live feed | REST polling, WebSocket, subscription, heartbeat, sequence/reconnect veya stale-price state bulunmadı | `RED / NOT_PRESENT` |
| Live simulated execution | API capability `offline`, `HISTORY_LOCAL`, `SIMULATED`, `trading_enabled=false`; live route yok | `PASS / live paper trading yok` |

## Claim → kontrol → sonuç

### C-17A-01 — Public historical download güvenli ve bounded mı?

**İddia:** Public historical artifact yalnız allowlist ve doğrulama sınırları geçildikten sonra cache’e alınmalıdır.

**Yerel kontrol:** `public_sources.py` HTTPS/host/path/filename/hash/byte planını doğrular. `public_download.py` redirect’i reddeder, response sınırlarını kontrol eder, bounded stream ile SHA-256 hesaplar, ZIP iç yol/symlink/CRC/tek CSV sınırlarını kontrol eder.

**Bağımsız kontrol:** Fake opener/response kullanan testlerde doğrulanmış ZIP cache’e alınmış, hash mismatch durumunda final ZIP/metadata/part dosyası bırakılmamış ve Content-Length üst sınırı body okunmadan reddedilmiştir.

**Sonuç:** `PASS`; bu yalnız historical download/cache contract’ıdır, canlı feed contract’ı değildir.

### C-17A-02 — Cache seçimi gerçekten offline ve doğrulanmış mı?

**İddia:** Simülasyon yalnız verified local artifact üzerinden başlamalıdır.

**Yerel kontrol:** Catalog `list_entries()` network kullanmadan cache’i inceler; `select()` yalnız checksum/ZIP bütünlüğü doğrulanan artifact’ı döndürür. Historical parser `quality_status=VERIFIED` ve güvenli path/file şartlarını tekrar kontrol eder.

**Bağımsız kontrol:** Catalog testlerinde missing/corrupt cache seçimi reddediliyor; verified cache seçimi exact metadata/path ile parse ediliyor. API dataset/preflight testleri missing/corrupt durumları açık problem detail olarak döndürüyor.

**Sonuç:** `PASS`, ancak `VERIFIED` burada artifact/cache bütünlüğü anlamına gelir; tek başına kapsamlı veri kalite veya canlı veri tazeliği kanıtı değildir.

### C-17A-03 — Gap/stale veri güvenli biçimde ele alınıyor mu?

**İddia:** Tarihsel simülasyon eksik veya beklenmeyen zaman grid’inde sessizce devam etmemelidir.

**Yerel kontrol:** Quality raporu gözlenen gap’i warning olarak raporlar; historical simulation 1h için ardışık `open_time_us` farkını zorunlu tutar ve `DATASET_NOT_CONTIGUOUS` ile durur. Parser ayrıca sıralama/çakışma/closed bar/limitleri kontrol eder.

**Sonuç:** Historical gap için `PASS / simulation scope`. Canlı stale veya reconnect için `NOT_PROVEN`; canlı observation sequence ve wall-clock policy mevcut değildir.

### C-17A-04 — Download retry/cancel, canlı reconnect kanıtı sayılır mı?

**İddia:** Download job retry/cancel mekanizması canlı public feed reconnect/stale davranışını karşılıyor olabilir.

**RED sonucu:** `DownloadJobManager` yalnız bounded historical file download job’larını yönetir; job state in-memory’dir. Feed sequence, heartbeat, last-observation time, reconnect backoff, duplicate/out-of-order tick ve stale publication state’i yoktur.

**Sonuç:** Download retry/cancel `PASS / kendi scope’unda`; canlı reconnect/stale authority’si değildir.

### C-17A-05 — Projede canlı public fiyat veya live paper route var mı?

**Bağımsız route/capability kontrolü:**

```text
CAPABILITIES={mode:'offline', data_mode:'HISTORY_LOCAL', execution_mode:'SIMULATED', trading_enabled:False, features:{preview:True, historical_import:False, testnet:False}}
LIVE_OR_WS_ROUTE=False
```

Mevcut API route’ları dataset catalog/download, historical preflight/chart/simulation ve preview/saved-run ile sınırlıdır; live/price/websocket route bulunmadı.

**Sonuç:** Canlı public fiyat ve live paper-trading implementation’ı `NOT_PRESENT`; yeni route veya adapter yazılmadı.

### C-17A-06 — Cache yayını tam atomik mi?

**İddia:** Başarılı doğrulama sonrası cache tek atomik işlemle kullanılabilir hale gelmelidir.

**Yerel kontrol:** ZIP staging dosyası fsync sonrası `os.replace` ile final ZIP’e taşınır; metadata ayrıca ayrı staging dosyasından `os.replace` edilir. Doğrulama başarısızsa final artifact yayınlanmaz.

**Sınır/karşı örnek:** ZIP replace ile metadata replace arasında process ölümü veya metadata yazma hatası için ortak directory transaction/recovery marker yoktur. Böyle bir durumda mevcut inspection metadata yoksa cache’i verified saymaz; ancak iki dosyalı yayının tek commit olduğu iddia edilemez.

**Sonuç:** “Doğrulanmamış payload yayınlanmaz” `PASS`; “ZIP + metadata tek transaction’da atomik yayınlanır” `NOT_PROVEN`. Bu fazda cache schema değişmedi.

## Güvenle korunabilecek mevcut davranışlar

- Public historical download yalnız explicit allowlist ve sabit plan üzerinden yürür.
- Cache’e girmeden önce boyut, SHA-256, ZIP yapısı, CSV üyeliği ve güvenli yol sınırları kontrol edilir.
- Historical parser ve simulation exact string/Fraction sınırlarını, kapalı barı ve gap politikasını korur.
- API capability offline/simulated/trading-disabled durumunu açıkça yayımlar.
- Private credential, gerçek emir ve testnet yolu açılmamıştır.

## Açık kapılar ve sonraki araştırma

Canlı public feed için güncel resmi sözleşme araştırması gerekir: seçilecek public endpoint/transport, rate limit ve bağlantı yaşam döngüsü, event/receive/processing time ayrımı, stale eşiği, sequence/out-of-order/duplicate, reconnect/backoff, gap ve offline fallback, simulated adapter sınırı ve güvenli error contract. Bu araştırma P1.17.b’ye ayrıldı; P1.17.a kapsamında dış canlı entegrasyon veya kod uygulanmadı.

## Kapanış kontrolleri

- Kanonik regresyon: `uv run --frozen python tools/run_checks.py` → `325/325 PASS`.
- Public source/download/catalog/historical API testleri: kanonik regresyonda `PASS`.
- Bağımsız capability/route kontrolü: `LIVE_OR_WS_ROUTE=False`.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `138` aktif Python dosyası.
- Kod/schema/API/UI değişikliği: yok.
- Production readiness: `NO`.
