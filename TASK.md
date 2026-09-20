# Aktif iş — Faz 2.1: demo akışı denetimi

Hedef: Local demo akışını girişten kayıtlı sonuca kadar denetlemek; canlı borsa, credential ve mutation açmamak.
Süre kutusu: 1 oturum. Bu alt sistemde ardışık dilim: 0/3.

## Denetim tablosu — ölçülen dilim

| Kontrol | Sonuç | Ölçüm / sınır |
|---|---|---|
| Deal bittikten sonra bot yeniden başlıyor mu? | HAYIR | VERIFIED BTCUSDT 1h fixture: 24 bar, 1 başlatılan BASE deal, 0 tamamlanan; `OPEN_AT_END`, yalnız `BASE` aksiyonu. `State.orders` temizlenmediği için kapanış sonrası restart yolu yok. |

## Adımlar

1. AGENTS.md, STATE.md ve TASK.md'yi oku; temiz çalışma ağacını ve aktif dalı doğrula.
2. Local API ve frontend'i güvenli demo modunda başlat; health/capabilities ve ilk ekran sözleşmesini kontrol et.
3. Dataset kataloğu, VERIFIED seçim, preflight ve historical profile eşleşmesini denetle.
4. Yalnız bounded offline simulation akışını çalıştır; INDETERMINATE veya COMPLETED sonuçlarını canlı sonuç gibi sunmadığını kontrol et.
5. Explicit save ile SQLite kayıt, liste ve detail akışını denetle; duplicate/idempotency ve corrupt/missing state sınırlarını doğrula.
6. Arayüz akışındaki bulguları mevcut kaynak/testlerle eşleştir; gerekirse tek küçük dikey dilim seç. Yeni belge/evidence klasörü açma.
7. Değişen alanın testlerini, tam checker'ı ve frontend tsc/vitest'i çalıştır; STATE.md'yi yalnız güncel gerçekle üzerine yaz.

## Tasarım özeti — Faz 2.1b Sıralı deal (uygulama yok)
- Katman: Deterministik döngü `historical_simulation` orkestrasyonunda; `service`/API çağırır ve aggregate sonucu kaydeder.
- Her tamamlanan deal sonrası yeni `State` açılır; çekirdekteki tek-deal ve “One base order per deal” değişmezleri korunur.
- `deal_id = execution_id:deal:<sequence>`; sıra 1’den artar ve aynı execution içinde tekrarlanmaz.
- Dedup/idempotency anahtarı `(execution_id, deal_id, event_sequence)`; run kaydı için mevcut `source_execution_id` korunur.
- Persistence tek immutable run aggregate’i ve sıralı deal özetlerini saklar; yeni deal realized PnL/equity devrini exact değerlerle alır.
- Oracle: elle hesaplanmış iki deal’lik bar dizisi; iki kimlik, iki kapanış, devreden realized PnL/equity ve tekil posting doğrulanır.
- Bu yalnız tasarımdır; `engine.py`, çekirdek State ve canlı/testnet yürütme değiştirilmedi.

## Değişmez sınırlar

- Credential, secret, signed request, emir, mutation ve mainnet yok.
- Gerçek ekonomik sonuç veya testnet mutation için açık karar/gate gerekir.
- Manual işlem kaydı, eski source DB/export veya migration girdisi istenmez.
- UNKNOWN, INDETERMINATE, eksik veri ve gap başarı kanıtı sayılmaz.
- Faz başına tek evidence/Sonuc dosyası kuralı korunur; yeni klasör açılmaz.

## Kabul

- Demo akışı yalnız güvenli local/offline veya read-only public sınırda kalır.
- UI, API ve persistence sözleşmeleri birbirine bağlı kanıtla raporlanır.
- Test sonucu açıkça PASS/FAIL ve kapsamıyla STATE.md'ye yazılır.
- Bağımsız inceleme yapılmadıysa `review=NOT_RUN` olarak kalır.
