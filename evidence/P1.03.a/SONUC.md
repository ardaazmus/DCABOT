# P1.03.a — Public kaynak sözleşmesi ve indirme doğrulama hazırlığı

Durum: IMPLEMENTED / LOCAL_PASS  
Bağımsız inceleme: NOT_RUN  
Kapsam: ağ çağrısı yapmayan, açık allowlist ve checksum/byte metadata sözleşmesi.

## Teslim

- `src/dcabot/data_adapters/public_sources.py`: immutable `PublicSourceSpec`, `PublicDownloadPlan` ve doğrulanmış artifact metadata modelleri.
- Yalnız registry’ye açıkça eklenmiş source ID’ler plan oluşturabilir.
- URL için HTTPS, allowlisted host/path, filename uyumu, query/fragment, kullanıcı adı/şifre ve traversal kontrolleri.
- Beklenen SHA-256 ve byte sayısı plan metadata’sında tutulur; üst indirme sınırı 256 MiB’dir.
- Payload doğrulaması tip, boyut ve SHA-256 uyuşmazlığında reddeder; ağ açmaz ve diske yazmaz.
- Gerçek Binance URL/checksum manifesti bu fazda sabitlenmedi; güncel dış araştırma olmadan kaynak uydurulmadı.

## Kanıt

- `uv run --frozen python tools/run_checks.py`: **53 test PASS**.
- `uv run --frozen python tools/check_workspace.py`: **PASS**; yedek alanı taranmadı/çalıştırılmadı.
- Odak testleri: allowlist dışı source, HTTP/query URL, metadata ve payload checksum/byte kontrolleri **PASS**.
- Ağ çağrısı, credential, private endpoint, public downloader ve testnet çalıştırılmadı.

## Sınır ve sonraki faz

Bu faz yalnız sözleşme ve doğrulama hazırlığıdır; indirme/cache, ilerleme/iptal/retry ve yerel katalog henüz yoktur. Gerçek kaynak kaydı için güncel resmi URL/checksum araştırması gerekir. Sıradaki tek görev `P1.03.b` bu araştırma sonucu doğrulanmış bir kaynakla indirme/cache’in en küçük dikey dilimini eklemektir.
