# P1.17.d — Venue-specific transport mapping ve reconnect/catch-up araştırma kapısı

Durum: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Girdi ve sınır

Kullanıcı tarafından teslim edilen Binance Spot public market-data raporu iddia ve araştırma girdisi olarak denetlendi; raporun içindeki kod veya kararlar otomatik talimat kabul edilmedi.

Bu kapı yalnızca `binance-spot-public-v3` profiline ilişkin public, kimlik doğrulamasız ve read-only market observation davranışını kapsar: REST/WS payload mapping’i, source event time ile local receive/processing time ayrımı, duplicate/conflict, ID sırası, gap, stale, reconnect/resubscribe ve best-effort catch-up sınırı.

Bu kapı canlı REST/WS client, network route, credential, private endpoint, gerçek/testnet emir, simulated economic fill, reserve, PnL, persistence, API veya UI açmaz.

Raporun belirttiği kaynak erişim tarihi `2025-01-15` güncel uygulama kararı için yeterli kabul edilmedi. Bu denetimde aynı resmi kaynakların güncel içerikleri `2026-09-10` tarihinde yeniden kontrol edildi. Python saat davranışı için [Python `time` belgeleri](https://docs.python.org/3/library/time.html) referans alındı.

## 2. Claim → local check → bağımsız kontrol → sonuç

### Claim A — Binance public profile seçilebilir

**Rapor iddiası:** Spot public REST ve WebSocket market-data yolları kimlik doğrulaması olmadan kullanılabilir; fiyat/miktar alanları decimal string, trade zamanları integer millisecond’tır.

**Resmi kontrol:** Güncel Binance Spot REST ve WebSocket belgeleri public market-data yollarını, trade/aggregate-trade alanlarını ve varsayılan millisecond zamanları destekliyor. WebSocket trade payload’ında `t` trade ID, `T` trade zamanı, `E` event zamanı, `p` ve `q` string alanları tanımlıdır.

Kaynaklar:

- [Binance Spot WebSocket Streams](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md)
- [Binance Spot REST API](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md)

**Yerel kontrol:** `PublicObservation` yalnız normalize edilmiş read-only observation taşır; price/quantity canonical decimal string zorunludur ve ekonomik alan yoktur.

**Sonuç:** `ACCEPT_WITH_LIMITATION`. Profile mapping yönü yeterli kanıta sahip; bu, canlı bağlantının çalıştığını kanıtlamaz.

### Claim B — WebSocket heartbeat ve limitleri

**Rapor iddiası:** Sunucu yaklaşık üç dakikada bir ping gönderir; 300 stream/connection sınırı vardır; toplam IP bağlantı limiti belirsizdir.

**Bağımsız resmi kontrol:** Güncel WebSocket belgesinde server ping aralığı 20 saniye, pong yanıt penceresi 60 saniye olarak yazılıdır. Aynı belgede 1024 stream/connection ve IP başına beş dakikalık aralıkta 300 connection attempt sınırları ayrı kurallar olarak tanımlanır. Rapor bu değerleri birbirine karıştırmıştır.

**Sonuç:** Raporun `3 dakika` ve `300 stream/connection` ifadeleri `REJECTED`. Kanonik kaynak sonucu: ping/pong `20s / 60s`; stream kapasitesi `1024 / connection`; connection attempt rate `300 / 5 min / IP`.

### Claim C — Timestamp yalnız millisecond’tır

**Rapor iddiası:** Binance zaman alanları millisecond’tır ve doğrudan microsecond’a çevrilmelidir.

**Bağımsız resmi kontrol:** Millisecond varsayılan olmaya devam eder; güncel WebSocket belgelerinde `timeUnit=MICROSECOND` seçeneği, REST belgelerinde `X-MBX-TIME-UNIT:MICROSECOND` başlığı da tanımlanmıştır.

**Sonuç:** `DEFAULT_MS_ACCEPTED`, fakat `MS_ONLY` iddiası `REJECTED_AS_INCOMPLETE`. P1.17.e’de seçilecek normalizasyon policy’si explicit olmalı; birim tahmini yapılmamalıdır.

### Claim D — `t`/`a` gerçek sequence’tir

**Rapor iddiası:** Trade ID veya aggregate trade ID monoton artar; gap `last_id + 1` ile tespit edilebilir.

**Bağımsız resmi kontrol:** Resmi payload açıklaması `t` ve `a` alanlarını trade/aggregate-trade ID olarak tanımlar; WebSocket mesaj sequence’i veya boşluksuz `+1` süreklilik garantisi vermez.

**Yerel RED kontrolü:** Mevcut generic `PublicObservation.source_sequence` alanı verilirse contiguous `+1` kontrolü yapar. Bu alana Binance `t`/`a` bağlanırsa atlanmış bir venue ID, doğrulanmamış biçimde `SEQUENCE_GAP` üretir.

**Bağımsız local control:** `source_sequence=None` ile event ID `5000` ardından `5002` kabul edildi; aynı ID’nin farklı payload hash’i `CONFLICT/FAILED` oldu; ekonomik alan üretilmedi.

**Sonuç:** Binance mapping’inde `event_id = str(t)` veya `str(a)` kabul edilebilir; `source_sequence` otomatik olarak `t/a` yapılmayacak. ID ordering/gap detection `NOT_VERIFIED / APPLICATION_POLICY` olarak kalır.

### Claim E — Reconnect otomatik snapshot/catch-up sağlar

**Rapor iddiası:** Reconnect sonrası resubscribe gerekir; REST recent-trades snapshot’ı best-effort catch-up olabilir.

**Resmi kontrol:** WebSocket belgesi bağlantı yaşam süresi, ping/pong ve subscribe protokolünü tanımlar; otomatik snapshot veya eksik WebSocket event’lerinin tam REST ile geri getirileceği garanti edilmez. REST recent trades mevcut market verisini sağlayabilir, fakat kayıp WS aralığının eksiksiz kapandığını tek başına kanıtlamaz.

**Sonuç:** Resubscribe `ACCEPT`; automatic WS snapshot `NOT_VERIFIED`; tam REST gap repair `NOT_VERIFIED`; coverage kanıtlanamazsa `GAP/RESYNC_REQUIRED` korunur. Resync tamamlanmadan `SYNCED` veya ekonomik kabul yoktur; başarılı yeni segment eski segmenti overwrite etmez.

### Claim F — `time.time_ns()` monotonic-safe’tir

**Rapor iddiası:** Yerel receive/processing zamanı için `time.time_ns() // 1000` monotonic-safe kullanılabilir.

**Kontrol:** Bu ifade doğru değildir. `time.time_ns()` duvar saatini verir; sistem saati geri alınabilir veya ayarlanabilir. Monoton geçen süre ölçümü ayrı bir monotonic clock gerektirir.

**Sonuç:** İddia `REJECTED`. Mevcut local replay sözleşmesindeki caller-supplied deterministic zaman korunur; bu fazda canlı clock helper eklenmez.

## 3. Canonical karar özeti

| Alan | Karar | Sınır |
|---|---|---|
| Venue/profile | `ACCEPT_WITH_LIMITATION` | Binance Spot public read-only; evrensel venue kararı değil |
| Primary transport | `ACCEPT_WITH_LIMITATION` | WS trade observation; client henüz yok |
| REST | `ACCEPT_WITH_LIMITATION` | allowlist/metadata ve best-effort observation; tam catch-up değil |
| Price/quantity | `ACCEPT` | venue string → exact local canonical decimal; float yok |
| Time | `ACCEPT_WITH_LIMITATION` | default ms; explicit microsecond seçeneği var; unit tahmini yok |
| `event_id` | `ACCEPT_WITH_LIMITATION` | trade `t` veya aggTrade `a`, canonical string |
| `source_sequence` | `DEFER / NOT_VERIFIED` | `t/a` sequence olarak bağlanmaz |
| Duplicate/conflict | `ACCEPT_WITH_LIMITATION` | immutable identity + payload hash; conflict fail-closed |
| Gap/out-of-order | `DEFER / APPLICATION_POLICY` | venue continuity garantisi yok; ekonomik acceptance yok |
| Ping/pong | `ACCEPT_WITH_LIMITATION` | güncel resmi 20s ping, 60s pong penceresi |
| Limits | `ACCEPT_WITH_LIMITATION` | 1024 stream/connection; 300 connection attempt/5m/IP |
| Reconnect | `ACCEPT_WITH_LIMITATION` | resubscribe gerekli; automatic snapshot garanti değil |
| Stale threshold | `DEFER` | uygulama policy’si; 30s venue kuralı değil |
| Offline fallback | `ACCEPT` | historical/replay live replacement değildir |
| Live adapter | `NO-GO / DEFERRED` | P1.17.e’de yalnız network-free parser/normalizer olabilir |

## 4. Yerel mevcut durum ve değişiklik kararı

Mevcut `src/dcabot/data_adapters/public_feed.py` generic, immutable ve salt-okunur cursor sözleşmesini taşır. `source_sequence` opsiyoneldir; bu Binance profile için `None` bırakılmalıdır. `tests/test_public_feed_contract.py` odak suite’i `11/11 PASS` oldu.

Bağımsız ağsız kontrol sonucu:

```text
BINANCE_ID_ONLY_ACCEPTS_NONCONTIGUOUS= ACCEPTED SYNCED
CONFLICT_FAIL_CLOSED= CONFLICT FAILED
NO_ECONOMIC_FIELDS= True
```

Canlı route taramasında Binance WSS/REST client veya `api/v3` canlı yolu bulunmadı; mevcut uygulama offline ve trading-disabled sınırındadır. Bu nedenle canlı transport kodu yazılmadı.

Çalıştırılan kontroller:

```text
tests.test_public_feed_contract: 11/11 PASS
tools/check_workspace.py: PASS
active_python_files: 140
```

## 5. Çıkış ve sonraki tek iş

P1.17.d araştırma kapısı, düzeltmelerle `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` olarak kapanır. Raporun seçtiği profil kullanılabilir bir araştırma yönüdür; eski heartbeat/limit/timestamp ve monotonic-clock ifadeleri kanonik karar değildir.

Sonraki tek mikro faz:

**P1.17.e — Binance public payload normalization (network-free)**

Yalnız resmi Binance trade/aggTrade fixture payload’larının ağsız parse/normalize edilmesi, trade ve aggTrade ayrımı, default-ms veya explicit-microsecond source mode’ünün fail-closed doğrulanması ve `t/a` değerlerinin sequence’e bağlanmaması ele alınabilir. WebSocket client, reconnect worker, REST catch-up, persistence, API/UI ve economic fill bu mikro fazın dışındadır.
