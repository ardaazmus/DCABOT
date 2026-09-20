# Aktif iş — P1 kapandı, Faz 3'e geçiş Arda'nın onayını bekliyor

P1 kapanış ölçütünün üç şartı da tamamlandı: temiz klonda 9 adımlık akış, bağımsız review (`APPROVED_WITH_FINDINGS`, Codex/muse), `git tag p1-demo-complete` atıldı. Ayrıntı: STATE.md, docs/KARARLAR.md, `evidence/P1_CLOSURE_INDEPENDENT_REVIEW_2026_09_20/SONUC.md`. Şu anda Claude'un elinde açık, kritik/matematik nitelikli bir görev yok.

## Açık karar (Arda'ya — gerçek ürün-kapsamı/zamanlama kararı)
Sıradaki faz **Faz 3 — P2: gerçek Binance testnet** (reconnect worker, REST catch-up, salt-okunur hesap ekranı, mutation gate kararı, tek testnet emri, restart recovery, uçtan uca testnet DCA). Bu, projenin ilk kez yerel/offline sınırın dışına çıkıp gerçek bir dış servise (testnet de olsa) bağlanacağı faz — AGENTS.md'nin "credential, gerçek emir, mainnet" çizgisine en yakın nokta. Roadmap sırası zaten belli (docs/YOL_HARITASI.md), ama BAŞLAMA zamanlaması ve "testnet'e bağlanmaya hazırız" onayı Arda'nın kararı.

## Değişmez sınırlar
- Credential, secret, signed request, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- Faz 3.1-3.3 (reconnect/REST catch-up/salt-okunur hesap) dahi olsa, gerçek testnet credential'ı gerektiren herhangi bir adımdan önce Arda'ya açıkça bildirilir.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda Faz 3'e başlamayı onayladığında, Claude 3.1 (reconnect worker) için kendi TASK.md brief'ini yazıp devam eder.
