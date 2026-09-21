# Aktif iş — yok (Faz 15 + 15.10 kapalı)

F15 12 dilimi (muse) + 15.10 (Claude, doğrudan düzeltme: eski paneller
"Klasik Görünüm"e taşındı, öksüz :8000/:8001 süreçleri temizlendi).
15.8/15.9 + PBO/Canary DEFERRED (gerekçeler `docs/KARARLAR.md`'de).
Sıradaki ürün adımı için `docs/YOL_HARITASI.md` "Şimdi" bölümüne bak;
Arda onayı bekleniyor.

## Durum
checker 1432/1432 · tsc temiz · vitest 234/234 · review=NOT_RUN.
Çalıştırma: `tools/run_api.py` (tek worker) + `frontend` build.

## Arda'ya açık sorular
- Faz 16 (motor esnekliği) kapsamı: risk kontrolleri, pair keşfi,
  average exactness bayrağı hangileri girsin?
- 15.8 keşif metriği: backtest-türetilmiş mi, hangi metrik?
- Canary: tutar üst sınırı, günlük kayıp, pencere, onay formatı?
- Dış LLM asistanı açılsın mı?
- NVDA/JAWS/HCM insan kapısı ne zaman?
- P4 (diğer borsalar) kapsamı ne olsun?
- Pine-parity için hangi indikatör taşınsın? (13.5 DEFERRED)
- F12–F15 bağımsız incelemesi (review=NOT_RUN) ne zaman?

## Değişmez sınırlar (sürüyor)
- Credential, secret, gerçek emir, mutation ve mainnet: açık onay olmadan asla.
