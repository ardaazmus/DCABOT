# Aktif iş

Hedef: DCABOT ajanının kısa, tutarlı ve güvenlik çizgilerini koruyan kanonik
başlangıç belgeleriyle doğru sıradaki ürüne ilerlemesi.

Faz/adım: Faz 0.3 — `AGENTS.md` kural reformu.

Dosyalar:

- `AGENTS.md`
- `STATE.md`
- `TASK.md`
- `WORKFLOW.md`

Kabul ölçütleri:

1. Credential, secret, imzalı hesap yanıtı, exact para hesabı, idempotency,
   UNKNOWN/gap fail-closed ve canlı emir sınırları korunur.
2. Aynı alt sistemde sonsuz mikro-regresyon zinciri yerine en fazla üç dilim,
   sonra ürün akışına veya açık karara geçiş yazılır.
3. Kanıt yetersizliği tek başına yeni varyasyon üretme gerekçesi yapılmaz;
   araştırma sonrası durma ve kullanıcı kararı açıkça tanımlanır.
4. Dosya 4 KB altında kalır ve `tools/run_checks.py` ile doğrulanır.

Bu alt sistemde ardışık dilim: `1/3`.

Faz bitince: `STATE.md` ve `TASK.md` üzerine yazılacak, release manifesti
yenilenecek, odak checker çalıştırılacak ve değişiklik snapshot dalına
pushlanacak. Arşiv dosyaları tarihçe olarak korunacak.

Güvenlik notu: Gerçek hesap, API key, CAPTCHA, testnet mutation, mainnet,
secret veya ekonomik ürün kararı gerektiren adımlar kullanıcı onayı olmadan
açılmaz.
