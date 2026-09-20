# Aktif iş — Faz 3.5 kapandı; sıradaki adım Faz 3.6 kapsam araştırması

Faz 3.5 (tek testnet emri) `evidence_scope=REAL_TESTNET` ile kapandı. Bkz. STATE.md, docs/KARARLAR.md. Şu anda Claude'un elinde açık kod görevi yok.

## Sıradaki: Faz 3.6 — Dolum + restart kurtarma (KAPSAM ARAŞTIRMASI, kod yazmadan önce)
Hedef (docs/YOL_HARITASI.md): süreç ortada öldürülür, yeniden başlayınca tek ekonomik kayıt (duplicate yok, kayıp yok).

## İlk adımlar
1. `ReconciliationCoordinator.startup`/`startup_with_durable_recovery` ve `AttemptStore.recover_after_restart` zaten var — bunların mevcut restart-kurtarma kapsamını (Faz 3.2'de kullanıldı) 3.6'nın istediği "dolum sırasında öldürme" senaryosuna ne kadar karşıladığını netleştir.
2. Testnet'te gerçek bir "process ortada öldürülürken bir emrin SENDING/ACKNOWLEDGED durumda kalması" senaryosunu nasıl güvenle simüle edeceğini (Arda'nın yerelde Ctrl+C ile mi keseceği, yoksa ayrı bir kill sinyali mi) belirle.
3. Dar kapsamı Arda'ya sun, onaysız kod yazma.

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- Claude gerçek testnet'e karşı hiçbir mutation çalıştırmaz.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Kod yazılmadan önce dar kapsam Arda'ya sunulur ve onaylanır.
