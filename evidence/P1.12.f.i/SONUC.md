# P1.12.f.i — Pionex DIY per-safety-order deviation/allocation profile

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`

Greenfield Futures DCA custom ladder profile projection’ı eklendi. Her safety
order için:

- anchor’a göre açıkça **cumulative deviation** taşınır;
- seviye index’i 1’den başlayarak kesintisiz ilerler;
- LONG seviyeleri pozitif ve aşağı, SHORT seviyeleri yukarı yönlü strict
  ilerler;
- fiyatlar exact tick hizasına alınır;
- allocation unit tek ve açık olarak `BASE_QTY` veya `QUOTE_NOTIONAL` olur;
- tüm per-level allocation’lar ortak explicit budget’a exact olarak toplanır.

Mevcut multiplier ladder yeniden yazılmadı; custom ladder ayrı bir projection
olarak çalışır. `SHARE` semantiği ürün kaynağında ekonomik anlamı ve bütçe
otoritesi kesinleşmeden varsayılmadı. Quantity-step, venue minimum/notional
filter, accepted order candidate, persistence ve canlı venue mutation bu
mikro-faza alınmadı.

## Kanıt

- Odak custom ladder: `5/5 PASS`
- İlgili DCA/sizing/ladder kümesi: `43/43 PASS`
- Tam proje suite: `616/616 PASS`
- Compile: `PASS`
- Workspace kontrolü: `PASS`
- Aktif Python dosyası: `239`
- Workspace backup layout: `EMPTY_OR_NOT_PLACED`
- Bağımsız Decimal oracle: custom LONG fiyatları ve exact allocation
  conservation kontrolü `PASS`
- `git diff --check`: hata yok; yalnız mevcut LF/CRLF dönüşüm uyarıları

Odak testleri `tests/test_futures_dca_custom_ladder.py` içinde bağımsız
Decimal formülü, SHORT quote allocation, index/deviation monotonicity,
budget overflow, unsupported `SHARE` ve empty ladder sınırlarını doğrular.

## Sıradaki tek mikro-faz

`P1.12.f.i.a` — custom ladder allocation’ını quantity-step ve quote/base
candidate sözleşmesine bağlamak. Bu adımda instrument metadata, quantization
ve min-notional fail-closed ele alınacak; canlı emir veya mutation açılmayacak.
