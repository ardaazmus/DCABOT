# Aktif iş — Faz 2.1: demo akışı denetimi

Hedef: Local demo akışını girişten kayıtlı sonuca kadar gözlemlemek; canlı borsa, credential ve mutation açmamak.
Süre kutusu: 1 oturum. Bu alt sistemde ardışık dilim: 0/3.

## Adımlar
1. AGENTS.md, STATE.md ve TASK.md'yi oku; temiz çalışma ağacını ve aktif dalı doğrula.
2. Local API ve frontend'i güvenli demo modunda başlat; health/capabilities ve ilk ekran sözleşmesini kontrol et.
3. Dataset kataloğu, VERIFIED seçim, preflight ve historical profile eşleşmesini denetle.
4. Yalnız bounded offline simulation akışını çalıştır; INDETERMINATE veya COMPLETED sonuçlarını yanlış biçimde canlı sonuç gibi sunmadığını kontrol et.
5. Explicit save ile SQLite kayıt, liste ve detail akışını denetle; duplicate/idempotency ve corrupt/missing state sınırlarını doğrula.
6. Arayüz akışındaki bulguları mevcut kaynak/testlerle eşleştir; gerekirse tek küçük dikey dilim seç. Yeni belge/evidence klasörü açma.
7. Değişen alanın testlerini, tam checker'ı ve frontend tsc/vitest'i çalıştır; STATE.md'yi yalnız güncel gerçekle üzerine yaz.

## Değişmez sınırlar
- Credential, secret, signed request, emir, mutation ve mainnet yok.
- Gerçek ekonomik sonuç veya testnet mutation için açık karar/gate gerekir.
- Manual işlem kaydı, eski source DB/export veya migration girdisi istenmez.
- UNKNOWN, INDETERMINATE, eksik veri ve gap başarı kanıtı sayılmaz.
- Faz başına tek evidence/Sonuc dosyası kuralı korunur; yeni klasör ancak AGENTS/TASK kapsamındaki faz kabulüyle açılabilir.

## Kabul
- Demo akışı yalnız güvenli local/offline veya read-only public sınırda kalır.
- UI, API ve persistence sözleşmeleri birbirine bağlı kanıtla raporlanır.
- Test sonucu açıkça PASS/FAIL ve kapsamıyla STATE.md'ye yazılır.
- Bağımsız inceleme yapılmadıysa review=NOT_RUN olarak kalır.