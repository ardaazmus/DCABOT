# Aktif iş — Faz 3.3 kapandı; sıradaki adım Faz 3.4 (mutation gate kararı)

Faz 3.1-3.3 tamamlandı (bkz. STATE.md, docs/KARARLAR.md). Şu anda Claude'un elinde açık kod görevi yok.

## Sıradaki adım: Faz 3.4 — Mutation gate kararı (kod değil, karar)
docs/YOL_HARITASI.md: "hangi koşulda emir gider? Onay ekranı, tutar limiti, kill-switch, idempotent clientOrderId. Arda onaylar." Bu, AGENTS.md'nin "gerçek emir" çizgisine ilk kez yaklaşan karar — Claude tek başına karara bağlamaz.

Claude'un yapabileceği: mevcut kod tabanının (idempotency zaten `AttemptStore`/`reconcile_attempt`'te var, credential zaten Windows Credential Manager'da, reconciliation state machine zaten kurulu) neyi hazır sağladığını özetleyen bir taslak hazırlayıp Arda'ya sunmak — onay ekranı UX'i, tutar limiti değeri, kill-switch mekanizması gibi ürün kararlarını Arda verir.

## Değişmez sınırlar
- Credential, secret, signed mutating request, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda 3.4 kararını onayladığında (veya taslak istediğinde), Claude devam eder.
