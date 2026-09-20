# Durum — 2026-09-20

Aktif faz: **Faz 3 (P2 gerçek Binance testnet) başladı — 3.1 kod tamam, offline doğrulandı; REAL_TESTNET kanıtı Arda'yı bekliyor.** P1 (Faz 2) `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan (offline): tam checker 886/886 PASS (0 skip); frontend tsc -b temiz, vitest 23/23 PASS.
Eksenler: implementation=IN_PROGRESS(3.1) · verification=PASS(offline) · evidence_scope=LOCAL_INTEGRATION (REAL_TESTNET henüz yok) · review=NOT_RUN(3.1) · deployment=NOT_DEPLOYED

## Faz 3.1 — Reconnect worker (bu oturum, Claude yaptı, delege edilmedi)
- **Ne yapıldı:** `src/dcabot/application/user_stream_reconnect_worker.py` — mevcut `BinanceTestnetUserDataStream` (kasıtlı reconnect'siz, tek bağlantı) ile mevcut `ReconciliationCoordinator`'ı (offline connection/event state machine) sınırlı, deterministic backoff (varsayılan 1/2/4/8/16 sn, en fazla 5 deneme) ile birbirine bağlıyor. Hem `connect()` hem `recv()` hatası aynı `_register_failure` yoluna giriyor — bir socket bağlanıp sonra her `recv()`'de düşerse backoff'suz sıkı döngüye girmez (kendi ilk taslağımda bu riski fark edip düzelttim).
- **Kapsam netleştirmesi (bkz. docs/KARARLAR.md):** SYNCED'e ulaşmak `ReconciliationCoordinator`'ın kendi kuralı gereği bir authoritative REST snapshot gerektiriyor (3.2, henüz yok). 3.1'in kanıtladığı gerçek yay: `CONNECTED_READ_ONLY → (düş) → STALE → (backoff+reconnect) → RECONCILIATION_REQUIRED → (gerçek gap varsa) → GAP` — roadmap'in kısa tanımıyla ("bağlan, düş, yeniden bağlan; gap tespiti") birebir.
- **Test:** `tests/test_user_stream_reconnect_worker.py`, 6 test — happy path (connect+event→`CONNECTED_READ_ONLY`), disconnect+başarılı reconnect (→`RECONCILIATION_REQUIRED`), reconnect sonrası gerçek out-of-order event ile gap tespiti (→`GAP`), bounded retry tükenmesi (fail-closed, `ReconnectWorkerError`), constructor doğrulaması. Sahte websocket (`FakeSocket`) ve sahte credential (dummy HMAC, gerçek değil) ile tamamen offline.
- **Canlı çalıştırma aracı (Claude hiç çalıştırmadı, çalıştıramaz):** `tools/run_user_stream_reconnect_worker.py <credential_id>` — gerçek ağ + Arda'nın Windows Credential Manager'da sakladığı testnet credential'ını kullanır. Import/syntax kontrolü yapıldı (`main` fonksiyonu doğru yükleniyor), ama gerçek testnet'e hiç bağlanılmadı — bu adım Arda'nın yerel makinesinde olmalı.

## REAL_TESTNET kanıtı için Arda'nın yapması gerekenler (bkz. TASK.md)
1. Testnet API anahtarı üret (testnet.binance.vision), sonra yerelde kaydet: `uv run --frozen python tools/configure_testnet_credential.py <credential_id>` (repoya girmez, Windows Credential Manager'da kalır).
2. Çalıştır: `$env:PYTHONPATH='src'; uv run --frozen python tools/run_user_stream_reconnect_worker.py <credential_id>`.
3. Birkaç saniye bekle (ilk `CONNECTED` satırını gör), sonra ağı kapat/aç (Wi-Fi'yi kapat-aç veya kabloyu çek-tak).
4. Terminaldeki transition log'unu izle: `DISCONNECTED` → `RECONNECTING` (backoff saniyesiyle) → `RECONNECTED` bekleniyor. Gerçek bir `GAP` yalnız o sırada gerçekten bir event kaçırılırsa görülür — garanti değil, testnet'in o an event üretip üretmediğine bağlı.
5. Ctrl+C ile durdur, log'u (yalnız redakte edilmiş state/kind satırları, credential/secret yok) Claude'a yapıştır — Claude bunu inceleyip STATE.md'yi `evidence_scope=REAL_TESTNET` olarak günceller.

## Faz 2 (P1) özeti — kapandı, `p1-demo-complete` etiketli (ayrıntı git geçmişinde)
Sıralı deal, ekonomik metrikler, reproduce+compare, etkileşimli marker, dar kapsamlı stress-slippage profili, temiz klon + bağımsız review (Codex/muse, `APPROVED_WITH_FINDINGS`) + tag.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): P1'in tam demo akışı (bkz. git geçmişi).
- CLI tools/bot.py: demo, init/replay/status/audit, preview. Yeni: tools/run_user_stream_reconnect_worker.py (Arda'nın yerelde çalıştıracağı).
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet: public/account/user-stream adaptörleri (mevcut) + yeni reconnect worker (bu oturum, offline doğrulandı, canlı doğrulanmadı).

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. REST catch-up (3.2) henüz yok — SYNCED'e ulaşılamıyor.
- Reconnect worker gerçek testnet'e karşı hiç çalıştırılmadı; yalnız offline/sahte-socket testleriyle doğrulandı.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok. Tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (bkz. `docs/KARARLAR.md`)
P1 kapanış ölçütü tamamlandı ve etiketlendi; Faz 3.1 kapsamı SYNCED'i 3.2'ye bırakacak şekilde netleştirildi (mevcut coordinator/adapter kodunu değiştirmeden).

## Sıradaki adım
Arda'nın `tools/run_user_stream_reconnect_worker.py`'yi yerelde testnet credential'ıyla çalıştırıp ağı kesip/açarak REAL_TESTNET kanıtı üretmesi bekleniyor. Kanıt geldiğinde Claude STATE.md'yi günceller ve **3.2 (REST catch-up)**'a geçer — bu da Claude-owned, kritik/persistence bir dilim olacak.
