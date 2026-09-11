# P2.04.c — Signed Transport ve WebSocket Adapter Contract Denetimi

Tarih: 2026-09-11  
Proje: DCABOT  
Karar türü: Yerel kod ve test kanıtı

## Karar

```text
P2.04.c_AUDIT = COMPLETE_WITH_LIMITATION
LOCAL_VERIFICATION = PASS
SIGNED_REST_TRANSPORT = NOT_IMPLEMENTED
BINANCE_USER_DATA_STREAM_ADAPTER = NOT_IMPLEMENTED
REAL_SIGNED_REQUEST = NO-GO
REAL_WEBSOCKET = NO-GO
REAL_TESTNET_MUTATION = NO-GO
MAINNET = NO-GO
TRADING_ACTIVATION = NO-GO
FULL_P2.04 = IN_PROGRESS
```

Bu alt fazın amacı mevcut signed request, credential, order transport ve
reconciliation sınırlarını denetlemekti. Denetim sonucunda offline/fake
temellerin bulunduğu, fakat gerçek Binance taşıma ve User Data Stream
adaptörünün henüz bulunmadığı doğrulandı. Bu nedenle canlı signed istek,
order, secret veya mainnet yolu açılmadı.

## Yerel olarak doğrulanan bulgular

| Alan | Bulgu | Sonuç |
|---|---|---|
| Public Testnet | `binance_testnet_public.py` sabit Testnet `exchangeInfo` adresiyle kimliksiz, bounded read-only snapshot alıyor | PASS |
| Public normalizer | `binance_public.py` yalnız decoded public payload normalizasyonu yapıyor; HTTP, credential ve ekonomik state taşımıyor | PASS |
| Signed request | `signed_request.py` offline payload/signature üretimiyle sınırlı; HTTP, API-key header ve secret persistence yok | PASS |
| Credential sınırı | `credential_boundary.py` ephemeral provider ve public metadata/account capability ayrımı sağlıyor | PASS |
| Order transport | `order_sender.py` `OrderTransport` fake/gelecek adapter protokolü; gerçek Binance implementation yok | PASS / LIMITATION |
| Reconciliation | `reconciliation.py` connection state ve fake/offline coordinator içeriyor; gerçek REST/WS worker yok | PASS / LIMITATION |
| API yüzeyi | `server/api.py` health/capability/public snapshot route'ları içeriyor; signed account/order route'u yok | PASS / LIMITATION |
| Bağımlılık/arama | Gerçek `httpx`, `websockets`, `aiohttp`, `requests`, socket/TLS taşıma, `session.logon`, `userDataStream` veya signed order query implementation bulunmadı | PASS |

## Kanıtlanan güvenlik sınırı

Bu alt fazda aşağıdaki davranışlar korunmuştur:

- Public snapshot, account veya API-key trade yetkisi olarak yorumlanmıyor.
- Offline signer, gerçek gönderim kanıtı olarak kullanılmıyor.
- Fake `OrderTransport`, venue kabulü veya fill kanıtı sayılmıyor.
- Reconnect veya connection state, `SYNCED` ekonomik state yerine geçirilmiyor.
- Secret frontend, URL, log, evidence veya response içine alınmadı.
- Timeout/ambiguous sonuçlar için canlı retry yolu açılmadı.
- Mainnet hostu, gerçek Testnet mutasyonu ve gerçek emir gönderimi yok.

## Eksik gerçek adaptör kanıtı

Aşağıdaki parçalar sonraki bir implementasyon fazında ayrıca tasarlanıp
offline/fake oracle ile doğrulanmalıdır:

1. Exact Testnet host allowlist ve redirect sonrası host kontrolü.
2. Backend-only credential/key provider ve API-key header binding.
3. Signed REST account/order query transportu.
4. `timestamp`/`recvWindow` ve clock-skew policy'si.
5. Timeout sonrası `UNKNOWN` ve blind-retry yasağı.
6. Durable attempt kaydı ile send öncesi atomicity.
7. Güncel WebSocket API User Data Stream subscription modeli.
8. Reconnect, stale/gap ve REST rebuild/reconciliation worker'ı.
9. Testnet reset sonrası eski venue state quarantine davranışı.
10. Gerçek dış ağ testi; yalnız kullanıcı açıkça yetkilendirirse ve mutation
    kapsamı ayrıca onaylanırsa.

## Kalite kanıtı

Bu denetim öncesinde mevcut çalışma ağacında şu kontroller başarıyla
çalıştırıldı:

```text
tools/run_checks.py: 397/397 PASS
Python compileall: PASS
tools/check_workspace.py: PASS
frontend npm run build: PASS
```

Bu sonuçlar mevcut kodun genel/offline sağlık durumunu destekler; gerçek
Binance signed REST veya WebSocket çalışma zamanını kanıtlamaz.

## Sonraki güvenli iş

P2.04.c canlı entegrasyon açmadan tamamlandı. WIP=1 kuralına göre sıradaki
tek iş:

> P2.03 — Fake venue üzerinde Spot `LIMIT`/`MARKET` order lifecycle,
> partial fill, duplicate/out-of-order event ve cancel/fill race sözleşmesi.

P2.03, P2.02 outbox/UNKNOWN ve P2.04 reconciliation temelleri yeşil
kalırken yalnız offline/fake transport ile ilerlemelidir. Gerçek Testnet
order mutasyonu bu kanıt dosyasının kapsamı dışında ve `NO-GO` durumundadır.

## Evidence sınıfları

- `[LOCAL_EVIDENCE]` — Bu dosyada belirtilen kaynak ve test sonuçları.
- `[APPLICATION_POLICY]` — UNKNOWN, reconciliation ve secret sınırlarına
  ilişkin DCABOT fail-closed politikası.
- `[NOT_VERIFIED]` — Gerçek signed REST, User Data Stream, reconnect worker
  ve canlı Testnet mutation çalışma zamanı.

