# Aktif iş — Faz 2 kapandı, sıradaki adım Arda'nın product-scope kararını bekliyor

Faz 2 (P1 kapanışı): 2.1, 2.1b, 2.2, 2.3, 2.4, 2.5 hepsi tamam (bkz. STATE.md, docs/YOL_HARITASI.md). Şu anda Claude'un elinde açık, kritik/matematik nitelikli bir görev yok.

## Açık karar (Arda'ya, roadmap-sequencing değil, gerçek ürün-kapsamı kararı)
docs/YOL_HARITASI.md'nin Faz 2 kapanış ölçütü: "temiz klonda README komutlarıyla 9 adımlık akış hatasız çalışır → bağımsız review APPROVED → `git tag p1-demo-complete`." İki seçenek var:

1. **P1 kapanış ölçütünü şimdi çalıştır:** temiz klon + uçtan uca 9 adım doğrulama + `git tag p1-demo-complete`. Sonra Faz 3'e geç.
2. **Doğrudan Faz 3'e geç** (P2 — gerçek Binance testnet: reconnect worker, REST catch-up, salt-okunur hesap ekranı, mutation gate kararı, tek testnet emri, restart recovery, uçtan uca testnet DCA). Bu, yerel/offline sınırın dışına çıkıp gerçek bir dış servise (testnet de olsa) bağlanmak demek — AGENTS.md'nin "credential, gerçek emir, mainnet" çizgisine yaklaşan ilk faz.

Bu iki seçenek arasında Claude karar vermiyor: (1) formalite bir kapanış adımı, (2) ise projenin ilk kez gerçek bir dış sisteme (testnet Binance) bağlanacağı, risk profili değişen bir faz başlangıcı — "son ürün özellikleri" kapsamına giren bir zamanlama/kapsam kararı.

## Değişmez sınırlar (her iki seçenekte de)
- Credential, secret, signed request, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda (1) veya (2)'yi seçtiğinde, Claude o dilim için kendi TASK.md brief'ini yazıp devam eder.
