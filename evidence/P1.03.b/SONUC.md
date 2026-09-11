# P1.03.b — doğrulanmış public indirme ve cache sonucu

## Kapsam

Bu küçük dikey dilim, araştırma yanıtında doğrulanmış tek resmi public artifact ile sınırlıdır:

- Source: `binance_spot_klines_v1`
- Ürün: Binance Spot klines, `BTCUSDT`, `1h`, günlük arşiv
- Dönem: `2025-01-01`
- ZIP: `BTCUSDT-1h-2025-01-01.zip`
- Sabit beklenen boyut: `1591` byte
- Sabit beklenen SHA-256: `8077644eb5088200969b135d7046ba777281be303fa32aceff28fe3baeaa5873`
- Beklenen iç CSV: `BTCUSDT-1h-2025-01-01.csv`

Kaynak URL ve `.CHECKSUM` doğrulaması kullanıcı tarafından sağlanan 2026-09-07 tarihli araştırma yanıtında VERIFIED olarak raporlanmıştır. Bu faz yeni credential, özel endpoint veya testnet kullanmaz.

## Uygulama

- `public_sources.py`: Binance kaynağı ve immutable örnek planı; strict checksum parser; plan başına byte, iç ZIP, üye ve açılım sınırları.
- `public_download.py`: yalnız HTTPS request, redirect reddi, `Accept-Encoding: identity`, bounded streaming, Content-Length/Encoding kontrolü, SHA-256 ve ZIP CRC/path/symlink doğrulaması.
- Başarısız checksum, aşım veya bozuk ZIP staging dosyasını final cache’e yayınlamaz.
- Başarılı dosya `<sha256>.zip`, metadata ise `<sha256>.json` olarak aynı cache klasöründe atomik `os.replace` ile yayınlanır. Doğrulanmış cache tekrarında ağ çağrısı yapılmaz.

## Kanıt

- `tools/run_checks.py`: PASS, 58 test.
- `tools/check_workspace.py`: PASS; yedek alanı taranmadı/çalıştırılmadı.
- Yeni odak testleri: gerçek payload ile başarılı cache + cache hit, checksum mismatch’te final dosya yok, Content-Length aşımında body okunmuyor, checksum formatı ve sabit Binance planı.
- `compileall`: PASS.
- Canlı smoke: resmi Binance ZIP geçici klasöre indirildi; `1591` byte ve sabit SHA-256 eşleşti; ikinci çağrı `cache_hit=True` döndü; geçici klasör komut sonunda kalıcılaştırılmadı.

## Açık sınırlar

Bu fazda checksum URL’sini dinamik çözümleyen retry/cancellation orkestrasyonu, süreçler arası cache lock, DNS/private-IP pinleme, stale fallback, katalog/API/UI ve raw Binance başlıksız CSV’nin canonical bar normalizasyonu uygulanmadı. Bunlar planın sonraki küçük fazlarına aittir. Canlı smoke yalnız araştırmada sabitlenen tek ZIP ile sınırlıdır; daha geniş tarih/kapsam ve checksum çözümleme kanıtı yoktur.

Durum: `COMPLETE / LOCAL_PASS`; bağımsız inceleme: `NOT_RUN`.
