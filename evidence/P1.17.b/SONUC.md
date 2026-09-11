# P1.17.b — Public read-only feed contract araştırma kapısı

Durum: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Girdi ve kapsam

Kullanıcı tarafından teslim edilen `docs/P1_KRITIK_ARASTIRMA_FINAL/14_P1.17_SIMULATED_RUNTIME.md` araştırma çıktısı olarak değerlendirildi; içindeki metin talimat kabul edilmedi. Raporun kendisi `LOCAL_CODE_INSPECTED: NO` ve `LOCAL_TESTS_EXECUTED: 0` dediği için uygulama kararı yalnız rapora dayanmadı.

Bu alt fazın kapsamı:

- public read-only market observation sözleşmesi,
- REST/WebSocket transport ayrımı,
- source/event/receive/processing zaman ayrımı,
- duplicate, conflicting duplicate, out-of-order, sequence gap, stale ve reconnect sınırı,
- observation ile simulated economic fill arasındaki authority ayrımı.

Canlı ağ bağlantısı, credential, private account, gerçek emir, ekonomik fill, fee/spread/slippage, persistence, UI ve paper-trading endpoint’i bu fazda açılmadı.

## 2. Dış kaynak iddialarının kontrolü

Raporun S38–S40 kaynakları güncel resmi sayfalardan kontrol edildi:

| İddia | Yerel karar | Resmi kanıt | Sınır |
|---|---|---|---|
| Public market-data WebSocket kimliksiz kullanılabilir | `ACCEPT_WITH_LIMITATION` | Coinbase public market-data endpoint ve çoğu kanal için authentication gerekmediğini açıklıyor: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview | Bu, bizim adapter’ımızın çalıştığını kanıtlamaz. |
| Sequence gap/out-of-order mümkündür ve tüketici bunu ele almalıdır | `ACCEPT_WITH_LIMITATION` | Coinbase sequence değerlerinin artması gerektiğini, atlanan ve geriden gelen mesajların oluşabileceğini belirtiyor: aynı kaynak, Sequence Numbers bölümü | Feed-specific recovery algoritması hâlâ seçilmedi. |
| Source event time ile system/receive time ayrılabilir | `ACCEPT_WITH_LIMITATION` | Bybit public trade payload’ında `ts` system time, `T` trade fill time ve `seq` alanlarını ayrı veriyor: https://bybit-exchange.github.io/docs/v5/websocket/public/trade | Bu alanların bizim canonical identity’miz olduğu iddia edilmiyor. |
| Public gözlem ekonomik fill değildir | `ACCEPT_WITH_LIMITATION` | Raporun authority ayrımı ve mevcut core sahipliğiyle uyumlu; yerel implementasyon ayrıca fill/order alanı üretmiyor | Simulated adapter kararı sonraki fazdır. |

Araştırma raporu REST/WS karşılaştırması istemine rağmen teslim edilen kaynak kartları esas olarak WebSocket’i kanıtlıyor; belirli bir REST payload/schema, rate-limit ve reconnect-catch-up sözleşmesi bu faz için yeterince ayrıntılı kapatılmadı. Bu alanlar `DEFERRED / NOT_VERIFIED` olarak kaldı.

## 3. Yerel RED → GREEN kontrolü

### RED

İlk odak testinde `dcabot.data_adapters.public_feed` modülü bulunmadı:

```text
ModuleNotFoundError: No module named 'dcabot.data_adapters.public_feed'
```

Bu, araştırma metnindeki sözleşmenin yerel kodda henüz bulunmadığını kanıtladı.

### Uygulanan minimum davranış

`src/dcabot/data_adapters/public_feed.py` yalnız şu sınırı ekler:

- immutable `PublicObservation`;
- exact canonical decimal-string price/quantity;
- source/event/receive/processing time alanları;
- optional source sequence;
- `DISCONNECTED`, `SYNCED`, `STALE`, `GAP`, `RECONNECTING`, `FAILED` state’leri;
- exact duplicate → no-op;
- aynı event ID ve farklı immutable payload → `CONFLICT`/`FAILED`;
- sequence gap, missing sequence ve out-of-order → kabul edilmez;
- reconnect sonrası yalnız açık `resync=True` ile yeni segment kabulü;
- caller-provided deterministic `now_time_us` ile stale kontrolü;
- bounded accepted history (`1,024` kayıt);
- order/candidate/fill/balance/reserve/economic result alanı yoktur.

### GREEN ve farklı bağımsız kontrol

- Odak testleri: `9/9 PASS` (`tests/test_public_feed_contract.py`).
- Bağımsız fixture/oracle kontrolü: `INDEPENDENT_FEED_ORACLE=PASS`.
- Kontrol; first accept, duplicate, conflicting duplicate, sequence gap, stale boundary, out-of-order, reconnect gate ve explicit resync davranışlarını production hesaplamasını kopyalamadan beklenen state/outcome değerleriyle karşılaştırdı.

## 4. Karar

`P1.17.b` araştırma kapısı, açık sınırlamalarla kapatılabilir. Araştırma; public read-only observation sözleşmesinin ve fail-closed feed gate’inin yönünü destekliyor. Ancak bu sonuç canlı feed’in çalıştığını, belirli bir venue’nin reconnect/catch-up davranışının çözüldüğünü veya observation’ın economic execution’a güvenle dönüştürülebileceğini kanıtlamaz.

Bir sonraki tek mikro faz: `P1.17.c — Offline observation replay adapter`. Bu fazda mevcut normalize edilmiş observation’lar yalnız local replay ile cursor’a verilecek; ağ, API/UI, persistence ve ekonomik fill açılmayacaktır. Gerçek REST/WS transport seçimi ve reconnect recovery ayrı karar kapısıdır.

## 5. Açık blokajlar

- Belirli venue seçilmeden REST ve WebSocket canonical mapping tamamlanmış sayılmaz.
- Reconnect sonrası snapshot/catch-up mekanizması venue’ye özgü kanıt ister.
- Stale eşiği uygulama policy’sidir; borsa gerçeği olarak sunulamaz.
- Public observation, simulated order/fill authority’si değildir.
- Mevcut projenin canonical numeric sözleşmesi trailing zero’ları kaldırır; araştırma raporundaki `"100.00"` örneği yerel `exact_text()` ile kabul edilmedi. Fixture’lar mevcut canonical biçim olan `"100"`/`"0.1"` ile doğrulandı; numeric sözleşme değiştirilmedi.

## 6. Doğrulama komutları

```powershell
$env:PYTHONPATH = "src"
uv run --frozen python -m unittest tests.test_public_feed_contract
uv run --frozen python -c "<independent feed oracle fixture>"
uv run --frozen python tools/run_checks.py
uv run --frozen python -m compileall -q src tests
uv run --frozen python tools/check_workspace.py
```
