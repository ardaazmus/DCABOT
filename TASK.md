# Aktif iş — Faz 3.6 kapandı; sıradaki adım Faz 3.7 kapsam araştırması

Faz 3.6 (dolum + restart kurtarma) `evidence_scope=REAL_TESTNET` ile kapandı. Bkz. STATE.md, docs/KARARLAR.md. Şu anda Claude'un elinde açık kod görevi yok.

## Sıradaki: Faz 3.7 — DCA botu testnet'te uçtan uca (KAPSAM ARAŞTIRMASI, kod yazmadan önce)
Hedef (docs/YOL_HARITASI.md): base + 1-2 safety + TP — testnet'te gerçek, tam bir DCA döngüsü. Bu Faz 3'ün SON dilimi; tamamlanınca kapanış ölçütü (bağımsız review + `git tag p2-testnet-complete`).

## İlk adımlar
1. Mevcut `testnet_order_execution.py`/`binance_testnet_order_execution.py` yalnız tek bir LIMIT emri destekliyor — DCA için birden fazla emri (base + safety'ler + TP) sıralı/duruma bağlı yönetmek gerekiyor. Mevcut çekirdek `engine.py`'nin (`State`/`apply`/`decision`) DCA mantığını zaten offline/simülasyonda yönettiğini hatırla — 3.7'nin işi bu mantığı gerçek testnet mutation'larına bağlamak, yeniden icat etmek değil.
2. Kapsamı büyük olasılıkla küçük tutmak gerekecek: tam bir "canlı bot döngüsü" (sürekli çalışan worker + reconnect + fill event'leri dinleme) yerine, önce elle tetiklenen adımlarla (CLI, Faz 3.5'teki gibi) bir DCA deal'inin tamamını (base gönder → safety tetiklenirse gönder → TP gönder) kanıtlamak daha güvenli olabilir.
3. Dar kapsamı Arda'ya sun, onaysız kod yazma.

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- Faz 3.4'ün 7 kuralı (kill-switch, tutar tavanı, onay, idempotency, tek-eşzamanlı-mutation, cancel disiplini, testnet hard-code) her yeni mutation'da aynen uygulanır.
- Claude gerçek testnet'e karşı hiçbir mutation çalıştırmaz.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Kod yazılmadan önce dar kapsam Arda'ya sunulur ve onaylanır.
