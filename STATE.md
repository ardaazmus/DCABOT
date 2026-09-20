# Durum — 2026-09-21

Aktif faz: **Faz 3.1 (reconnect worker) tamamen kapandı — `evidence_scope=REAL_TESTNET`.** P1 (Faz 2) `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 888/888 PASS (0 skip); frontend tsc -b temiz, vitest 23/23 PASS; gerçek testnet'e karşı canlı çalıştırıldı (aşağıda).
Eksenler: implementation=DONE(3.1) · verification=PASS · evidence_scope=REAL_TESTNET(3.1) · review=NOT_RUN(3.1) · deployment=NOT_DEPLOYED

## Faz 3.1 — Reconnect worker: REAL_TESTNET kanıtı alındı (bu oturum)
- **Kod:** `src/dcabot/application/user_stream_reconnect_worker.py` (önceki turda yazıldı), `tools/run_user_stream_reconnect_worker.py` (canlı çalıştırma aracı, Claude hiç çalıştırmadı — Arda çalıştırdı).
- **Arda'nın yerelde çalıştırdığı canlı test:** Testnet credential kaydedildi (`tools/configure_testnet_credential.py`; ilk denemede API key yanlış kopyalanmıştı — venue `Illegal characters... apiKey` diye redde reddetti, teşhis için secret'a hiç dokunmayan geçici bir script yazıldı, sorun bulundu ve düzeltildi). Worker gerçek testnet'e bağlandı, ağ birden çok kez kesilip açıldı.
- **Gerçek bug bulundu ve düzeltildi:** İlk canlı çalıştırmada program çöktü — `websockets.exceptions.ConnectionClosedError` (Exception alt sınıfı, OSError DEĞİL) `recv_execution_report`/`recv_order_list_event`'in except bloğunca yakalanmıyordu. Offline sahte-socket testleri bunu yapısal olarak kaçırıyordu (yalnız OSError fırlatıyorlardı). Fix: `connect()`'in zaten sahip olduğu `except Exception` catch-all deseni her iki `recv_*` metoduna da eklendi; 2 yeni test gerçek `ConnectionClosedError` sınıfıyla kanıtlıyor (bkz. docs/KARARLAR.md).
- **İkinci canlı çalıştırma:** Birden fazla gerçek disconnect/reconnect döngüsü (biri `attempt=5`'e, backoff sınırına kadar gidip tam zamanında toparlandı) çökmeden atlatıldı. `CONNECTED_READ_ONLY → STALE → RECONCILIATION_REQUIRED` yayı defalarca gözlendi. Gerçek bir GAP gözlenmedi (testnet hesabında o sırada trafik yoktu) — roadmap bunu garanti etmiyordu zaten.
- **Sonuç:** Faz 3.1 kapandı. `evidence_scope=REAL_TESTNET` sağlandı.

## Faz 3.1 kapsam netleştirmesi (önceki tur, hâlâ geçerli)
SYNCED'e ulaşmak authoritative REST snapshot gerektiriyor (3.2, henüz yok). 3.1'in kanıtladığı yay roadmap'in kısa tanımıyla ("bağlan, düş, yeniden bağlan; gap tespiti") birebir — bkz. docs/KARARLAR.md.

## Faz 2 (P1) özeti — kapandı, `p1-demo-complete` etiketli (ayrıntı git geçmişinde)

## Kodda mevcut
- P2 salt-okunur Binance testnet: public/account/user-stream adaptörleri + reconnect worker (**canlı doğrulandı**, gerçek testnet'e karşı çalıştı).
- Diğerleri önceki oturumlardan değişmedi (bkz. git geçmişi).

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. REST catch-up (3.2) henüz yok — SYNCED'e ulaşılamıyor.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok. Tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (bkz. `docs/KARARLAR.md`)
P1 kapanış ölçütü tamamlandı ve etiketlendi; Faz 3.1 kapsamı netleştirildi ve REAL_TESTNET kanıtıyla kapandı (gerçek testnet'in yakaladığı bir bug — `ConnectionClosedError` — düzeltildi).

## Sıradaki adım
**Faz 3.2 — REST catch-up:** gap sonrası açık emir/işlem sorgusuyla snapshot; `ReconciliationCoordinator.apply_authoritative_snapshot`'a bağlanan authoritative REST lookup. Kritik/persistence sınırına giren bir dilim — Claude yapar, Codex'e verilmez. Henüz TASK.md brief'i yazılmadı.
