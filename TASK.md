# Aktif iş — Faz 3.2: REST catch-up (KAPSAM, Claude sahibi)

Faz 3.1 kapandı (`evidence_scope=REAL_TESTNET`, bkz. STATE.md/docs/KARARLAR.md). Sırada **3.2 — REST catch-up**: gap sonrası açık emir/işlem sorgusuyla snapshot, `ReconciliationCoordinator.apply_authoritative_snapshot`'a bağlanan authoritative REST lookup.

## Neden Claude sahibi
`application/reconciliation.py` (kritik dosya listesinde) ve signed REST çağrısı içeren bir persistence/adapter dilimi. Codex'e devredilmez.

## İlk adımlar (kod yazmadan önce netleştirilecek)
1. `application/reconciliation.py`'deki `apply_authoritative_snapshot`/`AuthoritativeReconciliationSnapshot`'ı tekrar oku — snapshot'ın hangi alanları (`event_cursor`, `observed_at_ms`) taşıması gerektiğini kesinleştir.
2. Mevcut `query_binance_testnet_order_status` (`binance_testnet_user_stream.py`) zaten tek-emir REST-benzeri sorgu yapıyor (WS API üzerinden) — REST catch-up'ın bunu mu genişleteceğini yoksa ayrı bir "açık emirler" toplu sorgusu mu gerektirdiğini araştır (Binance'in `openOrders`/`myTrades` benzeri salt-okunur uç noktaları).
3. Dar bir kapsam öner: yalnız GAP/RECONCILIATION_REQUIRED durumunda tetiklenen, salt-okunur, mevcut credential/signing altyapısını (`signed_request.py`) yeniden kullanan bir snapshot sorgusu. Yeni mutation/emir YOK.

## Değişmez sınırlar
- Credential, secret, signed mutating request, gerçek emir ve mainnet: yok.
- `engine.py` çekirdek State/apply/decision değişmez.
- STATE.md/TASK.md yalnız Claude günceller.
- Claude gerçek testnet'e karşı hiçbir şey çalıştırmaz — REAL_TESTNET kanıtı yine Arda'nın yerelde çalıştırmasıyla gelir.

## Kabul
- Kod yazılmadan önce dar kapsam Arda'ya sunulur ve onaylanır (Faz 2.5'teki gibi).
- Onaylanırsa: test-first, offline sahte-socket/sahte-REST testleri + tam checker.
- REAL_TESTNET kanıtı Arda'dan gelmeden 3.2 "tamam" sayılmaz.
