# Aktif iş — Faz 3.4 kapandı (karar); sıradaki adım Faz 3.5 teknik tasarımı

Faz 3.4 (Mutation gate) 7 kuralla onaylandı, bkz. STATE.md/docs/KARARLAR.md. Kod yazılmadı — roadmap bunu kasıtlı "belge, kod değil" tanımlıyor.

## Sıradaki: Faz 3.5 — Tek testnet emri (KAPSAM ARAŞTIRMASI, kod yazmadan önce)
Hedef: limit emir gönder → gör → iptal et; journal kaydı. Faz 3.4'ün 7 kuralını (kill-switch, max_entry_notional, execution-anında onay, idempotent clientOrderId + durable-before-send, tek eşzamanlı mutation, cancel aynı disiplin, testnet hard-code) uygulayan dar bir implementasyon.

## İlk adımlar
1. Binance signed order-placement (`POST /api/v3/order` veya WS API `order.place`) ve cancel (`DELETE /api/v3/order`) uç noktalarının signing şeklini `signed_request.py`/`binance_testnet_account.py`/`binance_testnet_user_stream.py` ile tutarlı şekilde araştır.
2. Kill-switch (`DCABOT_TRADING_ENABLED`) ve tek-eşzamanlı-mutation kilidinin nereye (hangi katmana) konacağını netleştir.
3. UI onay ekranının (execution-anında açık onay) hangi bileşene ekleneceğini belirle.
4. Dar kapsamı Arda'ya sun, onaysız kod yazma.

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla; Faz 3.4'ün 7 kuralı hiçbiri atlanmadan uygulanacak.
- Claude gerçek testnet'e karşı hiçbir mutation çalıştırmaz — REAL_TESTNET kanıtı yine Arda'nın yerelde çalıştırmasıyla gelir.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Kod yazılmadan önce dar kapsam Arda'ya sunulur ve onaylanır (Faz 2.5/3.2/3.3 örneğindeki gibi).
