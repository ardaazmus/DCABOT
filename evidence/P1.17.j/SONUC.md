# P1.17.j — Binance public transport activation readiness gate

Durum: `DEFERRED / NO-GO / LOCAL_PASS`  
Activation decision: `NO-GO`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.d’deki Binance Spot public venue kanıtı, P1.17.e–i ağsız local implementation sınırıyla karşılaştırıldı. Amaç canlı transport yazmak değil, canlı aktivasyonun mevcut kanıtla güvenli olup olmadığını belirlemekti.

Karar yalnız şu public/read-only profile içindir:

```text
binance-spot-public-v3
```

Bu kapı private endpoint, credential, gerçek emir, simulated economic fill, persistence implementation veya API/UI açmaz.

## 2. Claim → local kontrol → karar

### Claim A — Venue araştırması tek başına canlı aktivasyon için yeterlidir

**Kontrol sonucu:** Hayır.

P1.17.d resmi kaynak denetimi public endpoint, payload mapping, timestamp, reconnect/resubscribe ve venue sınırlarını destekliyor; ancak şu davranışları garanti etmiyor:

- WebSocket reconnect sonrası otomatik snapshot;
- REST ile tam ve kesintisiz gap repair;
- trade/aggregate ID’sinin contiguous transport sequence olması;
- uygulamaya özgü stale threshold;
- local observation persistence atomicity;
- uygulamanın reconnect worker davranışı.

Bu eksikler venue iddiası değil, uygulama aktivasyon önkoşuludur. Sonuç: `NO-GO`.

### Claim B — Yerel public observation temeli canlı transport’a hazırdır

**Kontrol sonucu:** Hayır.

Local source/import graph kontrolü şu blokajları verdi:

```text
BINANCE_TRANSPORT_ACTIVATION_GATE=NO-GO
BLOCKERS=LIVE_ENTRYPOINT_MISSING,REST_CATCHUP_UNVERIFIED,PERSISTENCE_UNIMPLEMENTED,RECONNECT_WORKER_MISSING
```

Mevcut normalizer yalnız decoded fixture kabul eder. Replay cursor caller-supplied local zaman ve kayıtlarla çalışır; canlı socket, HTTP client, reconnect worker, resubscribe orchestration veya observation persistence değildir.

### Claim C — Canlı akış açılırsa mevcut fail-closed sınır yeterlidir

**Kontrol sonucu:** Hayır; sınırın local replay’de var olması canlı transport recovery kanıtı değildir.

Canlı activation öncesinde en az şu ayrı kanıtlar gerekir:

1. bounded WSS/HTTPS transport wrapper ve host/path allowlist;
2. ping/pong, disconnect ve resubscribe state machine;
3. duplicate/conflict/out-of-order/gap quarantine ile reconnect segment kimliği;
4. REST catch-up kapsam sınırı ve catch-up mümkün değilse fail-closed durum;
5. immutable observation persistence, checksum ve crash/replay davranışı;
6. canlı observation’ın economic/candidate/order/fill yollarına kapalı kaldığını gösteren integration boundary.

Bu önkoşullar mevcut değilken canlı network kodu eklemek plan dışı ve kanıtsız capability artışı olur.

## 3. Bağımsız kontrol

Üretim karar fonksiyonunu kopyalamayan bağımsız local yapı kontrolü; import graph, live entrypoint yokluğu, replay’in WS scope sınırı ve persistence alanı yokluğunu doğruladı. Kontrol çıktısı:

```text
BINANCE_TRANSPORT_ACTIVATION_GATE=NO-GO
```

## 4. Regresyon ve güvenlik sınırı

```text
tools/run_checks.py: 355/355 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 145
```

Testlerin geçmesi yalnız mevcut ağsız sözleşmenin bozulmadığını kanıtlar; canlı Binance bağlantısı veya gerçek zamanlı catch-up kanıtı değildir.

## 5. Karar

```text
ACTIVATION_DECISION=NO-GO
IMPLEMENTATION_STATUS=DEFERRED
```

P1.17 canlı REST/WS adapter’ı, reconnect worker, catch-up, observation persistence ve simulated paper execution olarak açılmayacak. Mevcut P1.17 sonucu güvenli public observation normalization/replay temelidir; F27’nin canlı paper-trading kısmı `PLAN` olarak kalır.

Bu karar için yeni dış araştırma istemek gerekli görülmedi; mevcut resmi venue araştırmasının açıkladığı sınırlara ek olarak local önkoşulların yokluğu kararı tek başına belirliyor. Gelecekte aktivasyon tekrar açılırsa güncel venue belgeleri ve uygulama kanıtı baştan doğrulanmalıdır.

## 6. Sonraki tek iş

**P1.18.a — Offline rule-based read-only event explanation projection**

Mevcut tarihsel/public observation ve sonuç sınırlarından yalnız açıklama/projection üretilecek; parametre, emir, fill, reserve, PnL veya canlı transport authority’si eklenmeyecek. UI/API ancak mevcut sözleşme ve plan açıkça gerektirirse ayrıca ele alınacak.
